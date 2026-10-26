import bz2
import json
from datetime import UTC, datetime
from typing import Annotated, Any
from urllib.parse import urljoin
from xml.etree import ElementTree

from apypie.resource import Resource
from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import Field
from requests.exceptions import HTTPError

from ..utils.content_utils import build_tool_result
from ..utils.utils import get_foreman_api, mcp_info_headers

REPORT_BATCH_SIZE = 250
MAX_REPORTS_TO_FILTER = 10_000
MAX_COMPRESSED_REPORT_SIZE = 25 * 1024 * 1024
MAX_DECOMPRESSED_REPORT_SIZE = 100 * 1024 * 1024


def register_compliance_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        description=(
            "Lists OpenSCAP compliance policies. Supports Foreman's policy search "
            "syntax, including name, content, profile, and tailoring_file fields."
        ),
        tags=("foreman", "openscap", "compliance", "api", "get", "policy"),
        annotations={
            "title": "List Compliance Policies",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def list_compliance_policies(
        ctx: Context,
        search: Annotated[
            str | None,
            Field(description="Optional Foreman scoped-search expression."),
        ] = None,
        page: Annotated[int, Field(ge=1)] = 1,
        per_page: Annotated[int, Field(ge=1, le=1000)] = 20,
    ) -> ToolResult:
        try:
            params = _pagination_params(search, page, per_page)
            response = get_foreman_api(ctx).call(
                "policies", "index", params, mcp_info_headers(ctx)
            )
            return _format_list_success("compliance policies", response)
        except Exception as exception:
            return format_compliance_failure("list compliance policies", exception)

    @mcp.tool(
        description=(
            "Lists OpenSCAP ARF compliance reports. The optional search is sent to "
            "Foreman and supports fields such as compliance_policy, "
            "compliance_status (compliant, incompliant, inconclusive), last_for, "
            "xccdf_rule_name, and xccdf_rule_failed. ID, date, and count filters "
            "are applied to the matching API results."
        ),
        tags=("foreman", "openscap", "compliance", "api", "get", "report"),
        annotations={
            "title": "List Compliance Reports",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def list_compliance_reports(
        ctx: Context,
        search: Annotated[
            str | None,
            Field(description="Optional Foreman scoped-search expression."),
        ] = None,
        host_id: Annotated[
            int | None, Field(description="Only return reports for this host ID.")
        ] = None,
        policy_id: Annotated[
            int | None, Field(description="Only return reports for this policy ID.")
        ] = None,
        reported_after: Annotated[
            str | None,
            Field(description="ISO 8601 lower bound for reported_at, inclusive."),
        ] = None,
        reported_before: Annotated[
            str | None,
            Field(description="ISO 8601 upper bound for reported_at, inclusive."),
        ] = None,
        minimum_passed: Annotated[int | None, Field(ge=0)] = None,
        minimum_failed: Annotated[int | None, Field(ge=0)] = None,
        page: Annotated[int, Field(ge=1)] = 1,
        per_page: Annotated[int, Field(ge=1, le=1000)] = 20,
        order: Annotated[
            str | None,
            Field(
                description=(
                    "Optional Foreman ordering, for example 'compliance_failed DESC'."
                )
            ),
        ] = None,
    ) -> ToolResult:
        try:
            api = get_foreman_api(ctx)
            headers = mcp_info_headers(ctx)
            filters = ReportFilters(
                host_id=host_id,
                policy_id=policy_id,
                reported_after=reported_after,
                reported_before=reported_before,
                minimum_passed=minimum_passed,
                minimum_failed=minimum_failed,
            )

            if not filters.active:
                params = _pagination_params(search, page, per_page, order)
                response = api.call("arf_reports", "index", params, headers)
                return _format_list_success("compliance reports", response)

            reports = fetch_all_compliance_reports(api, headers, search, order)
            filtered = filter_compliance_reports(reports, filters)
            start = (page - 1) * per_page
            response = {
                "total": len(filtered),
                "subtotal": len(filtered),
                "page": page,
                "per_page": per_page,
                "results": filtered[start : start + per_page],
            }
            return _format_list_success("compliance reports", response)
        except Exception as exception:
            return format_compliance_failure("list compliance reports", exception)

    @mcp.tool(
        description=(
            "Lists Foreman hosts assigned to an OpenSCAP compliance policy. "
            "The policy filter is evaluated by Foreman's compliance_policy_id "
            "scoped search."
        ),
        tags=("foreman", "openscap", "compliance", "api", "get", "host"),
        annotations={
            "title": "List Compliance Hosts for Policy",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def list_compliance_hosts_for_policy(
        policy_id: Annotated[int, Field(ge=1)],
        ctx: Context,
        search: Annotated[
            str | None,
            Field(description="Additional Foreman host search expression."),
        ] = None,
        page: Annotated[int, Field(ge=1)] = 1,
        per_page: Annotated[int, Field(ge=1, le=1000)] = 20,
    ) -> ToolResult:
        try:
            policy_search = f"compliance_policy_id = {policy_id}"
            combined_search = (
                f"({policy_search}) and ({search})" if search else policy_search
            )
            params = _pagination_params(combined_search, page, per_page)
            response = get_foreman_api(ctx).call(
                "hosts", "index", params, mcp_info_headers(ctx)
            )
            return _format_list_success("compliance policy hosts", response)
        except Exception as exception:
            return format_compliance_failure(
                "list hosts for a compliance policy", exception
            )

    @mcp.tool(
        description=(
            "Downloads a bzipped OpenSCAP ARF report and returns details for failed "
            "rules matching the requested XCCDF rule IDs or identifiers such as "
            "CCE-27175-9. The full XML is parsed locally and is not returned."
        ),
        tags=("foreman", "openscap", "compliance", "api", "get", "xccdf"),
        annotations={
            "title": "Get Failed Compliance Rule Detail",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def get_compliance_failed_rule_detail(
        report_id: Annotated[int, Field(ge=1)],
        rule_identifiers: Annotated[
            list[str],
            Field(
                min_length=1,
                description="XCCDF rule IDs and/or identifiers such as CCE IDs.",
            ),
        ],
        ctx: Context,
    ) -> ToolResult:
        try:
            api = get_foreman_api(ctx)
            payload = download_arf_report(api, report_id, headers=mcp_info_headers(ctx))
            matches = parse_failed_rule_details(payload, rule_identifiers)
            return build_tool_result(
                {
                    "message": (
                        f"Found {len(matches)} matching failed rule(s) in "
                        f"compliance report {report_id}."
                    ),
                    "report_id": report_id,
                    "rules": matches,
                }
            )
        except Exception as exception:
            return format_compliance_failure(
                f"get failed rule detail from compliance report {report_id}",
                exception,
            )


class ReportFilters:
    def __init__(
        self,
        *,
        host_id: int | None = None,
        policy_id: int | None = None,
        reported_after: str | None = None,
        reported_before: str | None = None,
        minimum_passed: int | None = None,
        minimum_failed: int | None = None,
    ) -> None:
        self.host_id = host_id
        self.policy_id = policy_id
        self.reported_after = _parse_datetime(reported_after)
        self.reported_before = _parse_datetime(reported_before)
        self.minimum_passed = minimum_passed
        self.minimum_failed = minimum_failed

        if (
            self.reported_after is not None
            and self.reported_before is not None
            and self.reported_after > self.reported_before
        ):
            raise ValueError("reported_after must not be later than reported_before")

    @property
    def active(self) -> bool:
        return any(
            value is not None
            for value in (
                self.host_id,
                self.policy_id,
                self.reported_after,
                self.reported_before,
                self.minimum_passed,
                self.minimum_failed,
            )
        )


def _pagination_params(
    search: str | None,
    page: int,
    per_page: int,
    order: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "per_page": per_page}
    if search:
        params["search"] = search
    if order:
        params["order"] = order
    return params


def fetch_all_compliance_reports(
    api,
    headers: dict,
    search: str | None = None,
    order: str | None = None,
) -> list[dict]:
    reports: list[dict] = []
    page = 1

    while True:
        params = _pagination_params(search, page, REPORT_BATCH_SIZE, order)
        response = api.call("arf_reports", "index", params, headers)
        page_results = response.get("results", [])
        reports.extend(page_results)

        expected = response.get("subtotal", response.get("total"))
        if len(reports) > MAX_REPORTS_TO_FILTER:
            raise ValueError(
                "More than 10000 reports match the server-side search. "
                "Narrow the search before applying client-side filters."
            )
        if not page_results or (expected is not None and len(reports) >= expected):
            break
        if len(page_results) < REPORT_BATCH_SIZE:
            break
        page += 1

    return reports


def filter_compliance_reports(
    reports: list[dict], filters: ReportFilters
) -> list[dict]:
    result = []
    for report in reports:
        if (
            filters.host_id is not None
            and _related_id(report.get("host")) != filters.host_id
        ):
            continue
        if (
            filters.policy_id is not None
            and _related_id(report.get("policy")) != filters.policy_id
        ):
            continue

        if filters.reported_after is not None or filters.reported_before is not None:
            reported_at = _parse_datetime(report.get("reported_at"))
            if filters.reported_after is not None and (
                reported_at is None or reported_at < filters.reported_after
            ):
                continue
            if filters.reported_before is not None and (
                reported_at is None or reported_at > filters.reported_before
            ):
                continue
        if (
            filters.minimum_passed is not None
            and int(report.get("passed") or 0) < filters.minimum_passed
        ):
            continue
        if (
            filters.minimum_failed is not None
            and int(report.get("failed") or 0) < filters.minimum_failed
        ):
            continue
        result.append(report)
    return result


def _related_id(value: Any) -> int | None:
    if isinstance(value, dict):
        value = value.get("id")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def download_arf_report(api, report_id: int, headers: dict | None = None) -> bytes:
    params = {"id": report_id}
    action = Resource(api, "arf_reports").action("download")
    route = action.find_route(params)
    url = urljoin(f"{api.uri.rstrip('/')}/", route.path_with_params(params).lstrip("/"))
    request_headers = {"Accept": "application/octet-stream", **(headers or {})}

    with api._session.get(  # noqa: SLF001 - apypie has no binary response API
        url, headers=request_headers, stream=True
    ) as response:
        response.raise_for_status()
        chunks = []
        size = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            size += len(chunk)
            if size > MAX_COMPRESSED_REPORT_SIZE:
                raise ValueError(
                    "Compressed ARF report exceeds the 25 MiB safety limit"
                )
            chunks.append(chunk)
    return b"".join(chunks)


def parse_failed_rule_details(
    compressed_report: bytes, rule_identifiers: list[str]
) -> list[dict]:
    requested = {identifier.strip().casefold() for identifier in rule_identifiers}
    if "" in requested:
        raise ValueError("Rule identifiers must not be empty")

    definitions: dict[str, dict] = {}
    failed_results: list[dict] = []
    parser = ElementTree.XMLPullParser(events=("start", "end"))
    capture_depth = 0
    xml_scan_tail = b""

    for decompressed in _decompress_bzip2_chunks(compressed_report):
        xml_scan = (xml_scan_tail + decompressed).upper()
        if b"<!DOCTYPE" in xml_scan or b"<!ENTITY" in xml_scan:
            raise ValueError(
                "ARF reports containing DTD declarations are not supported"
            )
        xml_scan_tail = xml_scan[-16:]
        parser.feed(decompressed)
        for event, element in parser.read_events():
            name = _local_name(element.tag)
            if event == "start" and name in {"Rule", "rule-result"}:
                capture_depth += 1
                continue
            if event != "end":
                continue

            if name == "Rule":
                rule_id = element.get("id")
                if rule_id:
                    definitions[rule_id] = _parse_rule_definition(element)
                capture_depth -= 1
                element.clear()
            elif name == "rule-result":
                result = _child_text(element, "result")
                if result and result.casefold() == "fail":
                    failed_results.append(_parse_rule_result(element))
                capture_depth -= 1
                element.clear()
            elif capture_depth == 0:
                element.clear()

    parser.close()

    matches = []
    for result in failed_results:
        rule_id = result["xccdf_rule_id"]
        definition = definitions.get(rule_id, {})
        identifiers = _merge_identifiers(
            definition.get("identifiers", []), result.get("identifiers", [])
        )
        candidate_values = {rule_id.casefold()}
        candidate_values.update(
            identifier["value"].casefold() for identifier in identifiers
        )
        if requested.isdisjoint(candidate_values):
            continue

        fixes = definition.get("fixes", [])
        matches.append(
            {
                "xccdf_rule_id": rule_id,
                "result": "fail",
                "severity": result.get("severity") or definition.get("severity"),
                "title": definition.get("title"),
                "description": definition.get("description"),
                "rationale": definition.get("rationale"),
                "identifiers": identifiers,
                "fix_available": bool(fixes),
                "fixes": fixes,
            }
        )
    return matches


def _decompress_bzip2_chunks(compressed_report: bytes):
    if len(compressed_report) > MAX_COMPRESSED_REPORT_SIZE:
        raise ValueError("Compressed ARF report exceeds the 25 MiB safety limit")

    decompressor = bz2.BZ2Decompressor()
    pending = compressed_report
    total = 0
    while pending or not decompressor.needs_input:
        output = decompressor.decompress(pending, max_length=1024 * 1024)
        pending = b""
        total += len(output)
        if total > MAX_DECOMPRESSED_REPORT_SIZE:
            raise ValueError("Decompressed ARF report exceeds the 100 MiB safety limit")
        if output:
            yield output
        if decompressor.eof:
            break
    if not decompressor.eof:
        raise ValueError("Downloaded ARF report is not a complete bzip2 stream")


def _parse_rule_definition(element: ElementTree.Element) -> dict:
    return {
        "severity": element.get("severity"),
        "title": _child_text(element, "title"),
        "description": _child_text(element, "description"),
        "rationale": _child_text(element, "rationale"),
        "identifiers": _parse_identifiers(element),
        "fixes": [
            {
                "system": fix.get("system"),
                "platform": fix.get("platform"),
                "disruption": fix.get("disruption"),
                "reboot": fix.get("reboot"),
                "strategy": fix.get("strategy"),
                "text": _element_text(fix),
            }
            for fix in _direct_children(element, "fix")
        ],
    }


def _parse_rule_result(element: ElementTree.Element) -> dict:
    return {
        "xccdf_rule_id": element.get("idref", ""),
        "severity": element.get("severity"),
        "identifiers": _parse_identifiers(element),
    }


def _parse_identifiers(element: ElementTree.Element) -> list[dict]:
    return [
        {"system": identifier.get("system"), "value": _element_text(identifier)}
        for identifier in _direct_children(element, "ident")
        if _element_text(identifier)
    ]


def _merge_identifiers(*identifier_lists: list[dict]) -> list[dict]:
    merged = []
    seen = set()
    for identifiers in identifier_lists:
        for identifier in identifiers:
            key = (identifier.get("system"), identifier.get("value"))
            if key not in seen:
                seen.add(key)
                merged.append(identifier)
    return merged


def _direct_children(
    element: ElementTree.Element, name: str
) -> list[ElementTree.Element]:
    return [child for child in element if _local_name(child.tag) == name]


def _child_text(element: ElementTree.Element, name: str) -> str | None:
    children = _direct_children(element, name)
    return _element_text(children[0]) if children else None


def _element_text(element: ElementTree.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _format_list_success(subject: str, response: dict) -> ToolResult:
    count = len(response.get("results", [])) if isinstance(response, dict) else 0
    return build_tool_result(
        {
            "message": f"Found {count} {subject} on this page.",
            "response": response,
        }
    )


def format_compliance_failure(operation: str, exception: Exception) -> ToolResult:
    structured_content = {
        "message": f"Failed to {operation}.",
        "error": str(exception),
    }
    if isinstance(exception, HTTPError):
        text = getattr(exception.response, "text", None)
        if text:
            try:
                structured_content["response"] = json.loads(text)
            except json.JSONDecodeError:
                structured_content["response"] = text
    return build_tool_result(structured_content)
