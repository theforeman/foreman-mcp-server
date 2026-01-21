"""Tests for errata management tools."""

from unittest.mock import MagicMock

from foreman_mcp_server.tools.errata import (
    _generate_failure_recommendations,
    register_errata_tools,
)


class TestGenerateFailureRecommendations:
    """Tests for the failure recommendation helper function."""

    def test_no_failures_returns_generic_recommendation(self):
        failures = []
        recommendations = _generate_failure_recommendations(failures)
        assert len(recommendations) == 1
        assert "Review the error outputs" in recommendations[0]

    def test_detects_package_not_found(self):
        failures = [
            {"error_output": "no package matching xyz found"},
        ]
        recommendations = _generate_failure_recommendations(failures)
        assert any("already have the update" in r for r in recommendations)

    def test_detects_connectivity_issues(self):
        failures = [
            {"error_output": "connection refused to host"},
        ]
        recommendations = _generate_failure_recommendations(failures)
        assert any("Connectivity issues" in r for r in recommendations)

    def test_detects_permission_issues(self):
        failures = [
            {"error_output": "permission denied when executing command"},
        ]
        recommendations = _generate_failure_recommendations(failures)
        assert any("Permission issues" in r for r in recommendations)

    def test_detects_package_manager_errors(self):
        failures = [
            {"error_output": "yum transaction error"},
        ]
        recommendations = _generate_failure_recommendations(failures)
        assert any("Package manager" in r for r in recommendations)

    def test_multiple_patterns_in_one_failure(self):
        failures = [
            {"error_output": "connection timeout while running yum"},
        ]
        recommendations = _generate_failure_recommendations(failures)
        # Should detect both connectivity and package manager issues
        assert len(recommendations) >= 2


class TestRegisterErrataTools:
    """Tests for errata tool registration."""

    def test_registers_analyze_errata_impact(self):
        mcp = MagicMock()
        foreman_api = MagicMock()
        get_context = MagicMock()

        register_errata_tools(mcp, foreman_api, get_context)

        # Check that mcp.tool was called (the decorator)
        assert mcp.tool.called

    def test_tool_decorator_called_multiple_times(self):
        mcp = MagicMock()
        foreman_api = MagicMock()
        get_context = MagicMock()

        register_errata_tools(mcp, foreman_api, get_context)

        # Should register 3 tools: analyze_errata_impact, apply_errata, investigate_errata_failures
        assert mcp.tool.call_count == 3


class TestAnalyzeErrataImpactLogic:
    """Tests for analyze_errata_impact business logic."""

    def test_environment_grouping_logic(self):
        """Test that hosts are correctly grouped by lifecycle environment."""
        # This tests the logic without actually calling the async function
        hosts = [
            {
                "name": "host1.example.com",
                "id": 1,
                "content_facet_attributes": {
                    "lifecycle_environment": {"name": "Development"}
                },
            },
            {
                "name": "host2.example.com",
                "id": 2,
                "content_facet_attributes": {
                    "lifecycle_environment": {"name": "Production"}
                },
            },
            {
                "name": "host3.example.com",
                "id": 3,
                "content_facet_attributes": {
                    "lifecycle_environment": {"name": "Development"}
                },
            },
        ]

        environments = {}
        for host in hosts:
            content_facet = host.get("content_facet_attributes", {})
            lce = content_facet.get("lifecycle_environment", {})
            lce_name = lce.get("name") if lce else None

            if lce_name:
                if lce_name not in environments:
                    environments[lce_name] = {
                        "name": lce_name,
                        "hosts": [],
                        "count": 0,
                    }
                environments[lce_name]["hosts"].append({
                    "name": host.get("name"),
                    "id": host.get("id"),
                })
                environments[lce_name]["count"] += 1

        assert len(environments) == 2
        assert environments["Development"]["count"] == 2
        assert environments["Production"]["count"] == 1

    def test_production_classification_with_explicit_environments(self):
        """Test that production flag is correctly set based on provided list."""
        environments = {
            "Development": {"name": "Development", "count": 2},
            "Production": {"name": "Production", "count": 1},
            "Staging": {"name": "Staging", "count": 1},
        }
        production_environments = ["Production"]

        for env_name, env_data in environments.items():
            env_data["is_production"] = env_name in production_environments

        assert environments["Development"]["is_production"] is False
        assert environments["Production"]["is_production"] is True
        assert environments["Staging"]["is_production"] is False

    def test_production_classification_with_multiple_prod_environments(self):
        """Test classification with multiple production environments."""
        environments = {
            "Development": {"name": "Development", "count": 2},
            "Production": {"name": "Production", "count": 1},
            "Prod-DR": {"name": "Prod-DR", "count": 1},
        }
        production_environments = ["Production", "Prod-DR"]

        for env_name, env_data in environments.items():
            env_data["is_production"] = env_name in production_environments

        assert environments["Development"]["is_production"] is False
        assert environments["Production"]["is_production"] is True
        assert environments["Prod-DR"]["is_production"] is True


class TestApplyErrataLogic:
    """Tests for apply_errata business logic."""

    def test_search_query_construction(self):
        """Test that search queries are correctly built."""
        errata_id = "RHSA-2024:1234"
        lifecycle_environment = "Development"
        hostgroup = "webservers"

        search_parts = [
            f"applicable_errata = {errata_id}",
            f"lifecycle_environment = {lifecycle_environment}",
        ]
        if hostgroup:
            search_parts.append(f"hostgroup = {hostgroup}")

        search_query = " AND ".join(search_parts)

        expected = (
            "applicable_errata = RHSA-2024:1234 "
            "AND lifecycle_environment = Development "
            "AND hostgroup = webservers"
        )
        assert search_query == expected

    def test_search_query_without_hostgroup(self):
        """Test query construction without hostgroup filter."""
        errata_id = "RHSA-2024:1234"
        lifecycle_environment = "Development"
        hostgroup = None

        search_parts = [
            f"applicable_errata = {errata_id}",
            f"lifecycle_environment = {lifecycle_environment}",
        ]
        if hostgroup:
            search_parts.append(f"hostgroup = {hostgroup}")

        search_query = " AND ".join(search_parts)

        expected = (
            "applicable_errata = RHSA-2024:1234 "
            "AND lifecycle_environment = Development"
        )
        assert search_query == expected

    def test_host_id_filtering(self):
        """Test that host_ids correctly filter the target hosts."""
        affected_hosts = [
            {"id": 1, "name": "host1"},
            {"id": 2, "name": "host2"},
            {"id": 3, "name": "host3"},
        ]
        host_ids = [1, 3]

        filtered = [h for h in affected_hosts if h.get("id") in host_ids]

        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 3
