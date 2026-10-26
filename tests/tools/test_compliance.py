import asyncio
import bz2
from unittest.mock import Mock

import pytest
from fastmcp import FastMCP
from requests.exceptions import HTTPError

from foreman_mcp_server.tools.compliance import (
    MAX_COMPRESSED_REPORT_SIZE,
    ReportFilters,
    fetch_all_compliance_reports,
    filter_compliance_reports,
    format_compliance_failure,
    parse_failed_rule_details,
    register_compliance_tools,
)

ARF_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<arf:asset-report-collection
    xmlns:arf="http://scap.nist.gov/schema/asset-reporting-format/1.1"
    xmlns:xccdf="http://checklists.nist.gov/xccdf/1.2">
  <xccdf:Benchmark>
    <xccdf:Rule id="xccdf_org.example_rule_sshd" severity="high">
      <xccdf:title>Configure SSH securely</xccdf:title>
      <xccdf:description>Disable weak SSH settings.</xccdf:description>
      <xccdf:rationale>Weak settings expose the host.</xccdf:rationale>
      <xccdf:ident system="https://ncp.nist.gov/cce/index.cfm">CCE-12345-6</xccdf:ident>
      <xccdf:fix system="urn:xccdf:fix:script:sh" reboot="false">echo fixed</xccdf:fix>
    </xccdf:Rule>
    <xccdf:Rule id="xccdf_org.example_rule_passing" severity="low">
      <xccdf:title>Passing rule</xccdf:title>
      <xccdf:ident system="https://ncp.nist.gov/cce/index.cfm">CCE-99999-9</xccdf:ident>
    </xccdf:Rule>
  </xccdf:Benchmark>
  <xccdf:TestResult>
    <xccdf:rule-result idref="xccdf_org.example_rule_sshd" severity="high">
      <xccdf:result>fail</xccdf:result>
    </xccdf:rule-result>
    <xccdf:rule-result idref="xccdf_org.example_rule_passing">
      <xccdf:result>pass</xccdf:result>
    </xccdf:rule-result>
  </xccdf:TestResult>
</arf:asset-report-collection>
"""


class TestReportFiltering:
    @pytest.fixture
    def reports(self):
        return [
            {
                "id": 1,
                "host": {"id": 10, "name": "host-a.example.test"},
                "policy": {"id": 20, "name": "CIS"},
                "reported_at": "2026-09-20T10:00:00Z",
                "passed": 80,
                "failed": 3,
            },
            {
                "id": 2,
                "host": {"id": 11, "name": "host-b.example.test"},
                "policy": {"id": 21, "name": "STIG"},
                "reported_at": "2026-09-25T10:00:00+00:00",
                "passed": 90,
                "failed": 0,
            },
        ]

    def test_filters_by_ids_date_and_counts(self, reports):
        filters = ReportFilters(
            host_id=10,
            policy_id=20,
            reported_after="2026-09-19T00:00:00Z",
            reported_before="2026-09-21T00:00:00Z",
            minimum_passed=50,
            minimum_failed=1,
        )

        assert filter_compliance_reports(reports, filters) == [reports[0]]

    def test_id_filter_does_not_require_reported_at(self):
        report = {"id": 3, "host": {"id": 10}, "policy": {"id": 20}}

        assert filter_compliance_reports([report], ReportFilters(host_id=10)) == [
            report
        ]

    def test_rejects_reversed_date_range(self):
        with pytest.raises(ValueError, match="reported_after"):
            ReportFilters(
                reported_after="2026-09-21T00:00:00Z",
                reported_before="2026-09-20T00:00:00Z",
            )

    def test_fetches_all_api_pages(self):
        first_page = {
            "subtotal": 251,
            "results": [{"id": index} for index in range(250)],
        }
        second_page = {"subtotal": 251, "results": [{"id": 250}]}
        api = Mock()
        api.call.side_effect = [first_page, second_page]

        reports = fetch_all_compliance_reports(
            api, {"X-Test": "yes"}, "compliance_status=incompliant"
        )

        assert len(reports) == 251
        assert api.call.call_count == 2
        assert api.call.call_args_list[1].args[2]["page"] == 2


class TestFailedRuleParsing:
    def test_matches_xccdf_rule_id(self):
        rules = parse_failed_rule_details(
            bz2.compress(ARF_XML), ["xccdf_org.example_rule_sshd"]
        )

        assert len(rules) == 1
        assert rules[0]["title"] == "Configure SSH securely"
        assert rules[0]["severity"] == "high"
        assert rules[0]["fix_available"] is True
        assert rules[0]["fixes"][0]["text"] == "echo fixed"

    def test_matches_cce_case_insensitively(self):
        rules = parse_failed_rule_details(bz2.compress(ARF_XML), ["cce-12345-6"])

        assert len(rules) == 1
        assert rules[0]["identifiers"][0]["value"] == "CCE-12345-6"

    def test_does_not_return_passing_rules(self):
        rules = parse_failed_rule_details(bz2.compress(ARF_XML), ["CCE-99999-9"])

        assert rules == []

    def test_rejects_invalid_bzip2(self):
        with pytest.raises(OSError):
            parse_failed_rule_details(b"not bzip2", ["CCE-12345-6"])

    def test_rejects_dtd_declarations(self):
        xml = b'<!DOCTYPE foo [<!ENTITY x "unsafe">]><foo>&x;</foo>'

        with pytest.raises(ValueError, match="DTD"):
            parse_failed_rule_details(bz2.compress(xml), ["CCE-12345-6"])

    def test_rejects_oversized_compressed_report(self):
        with pytest.raises(ValueError, match="25 MiB"):
            parse_failed_rule_details(
                b"x" * (MAX_COMPRESSED_REPORT_SIZE + 1), ["CCE-12345-6"]
            )


class TestComplianceFailure:
    def test_includes_json_http_response(self):
        error = HTTPError(
            "404 Not Found", response=Mock(text='{"error": "report not found"}')
        )

        result = format_compliance_failure("get report", error)

        assert result.structured_content["response"] == {"error": "report not found"}


class TestToolRegistration:
    @pytest.fixture
    def mcp(self):
        return FastMCP(name="Test MCP Server")

    def test_registers_read_only_compliance_tools(self, mcp):
        register_compliance_tools(mcp)

        tools = asyncio.run(mcp.local_provider._list_tools())
        tools_by_name = {tool.name: tool for tool in tools}
        assert {
            "list_compliance_policies",
            "list_compliance_reports",
            "list_compliance_hosts_for_policy",
            "get_compliance_failed_rule_detail",
        } <= tools_by_name.keys()
        assert all(
            tools_by_name[name].annotations.readOnlyHint is True
            for name in (
                "list_compliance_policies",
                "list_compliance_reports",
                "list_compliance_hosts_for_policy",
                "get_compliance_failed_rule_detail",
            )
        )
