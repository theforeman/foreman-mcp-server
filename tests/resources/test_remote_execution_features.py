import asyncio
import json
from unittest.mock import Mock, patch

import pytest
from fastmcp import FastMCP

from foreman_mcp_server.resources.remote_execution_features import (
    _build_feature_entry,
    register_remote_execution_features,
)


class TestAllowedRemoteExecutionFeaturesResource:
    """Test the allowed remote execution features resource."""

    @pytest.fixture
    def mcp(self):
        return FastMCP(name="Test MCP Server")

    @pytest.fixture
    def mock_ctx(self):
        return Mock()

    def _get_resource_result(self, mcp, _ctx):
        """Helper to get the resource function and run it."""
        from fastmcp.server.context import Context

        all_resources = asyncio.run(mcp.local_provider._list_resources())
        resource = next(
            r
            for r in all_resources
            if str(r.uri) == "foreman://remote_execution/allowed_features"
        )

        async def _call():
            # resource.fn is wrapped by without_injected_parameters in fastmcp v3
            # which requires an active Context for DI to inject ctx.
            async with Context(fastmcp=mcp):
                return await resource.fn()

        return asyncio.run(_call())

    def test_empty_allowlist_returns_empty_features(self, mcp, mock_ctx):
        """Test that an empty allowlist returns no features."""
        register_remote_execution_features(mcp, [])

        result = json.loads(self._get_resource_result(mcp, mock_ctx))

        assert result["features"] == []
        assert result["allowed_labels"] == []

    @patch("foreman_mcp_server.resources.remote_execution_features.get_foreman_api")
    def test_happy_path_returns_features_with_template_info(
        self, mock_get_foreman_api, mcp, mock_ctx
    ):
        """Test that allowed features are returned with their template info."""
        mock_api = Mock()
        mock_api.call.side_effect = [
            # First call: remote_execution_features index
            {
                "results": [
                    {
                        "id": 1,
                        "label": "katello_errata_install",
                        "name": "Katello Errata Install",
                        "description": "Install errata via Katello",
                        "job_template_id": 42,
                    },
                    {
                        "id": 2,
                        "label": "other_feature",
                        "name": "Other Feature",
                        "description": "Some other feature",
                        "job_template_id": 99,
                    },
                ]
            },
            # Second call: job_templates index (batch)
            {
                "results": [
                    {
                        "id": 42,
                        "name": "Install Errata - Katello Script Default",
                    }
                ]
            },
        ]
        mock_get_foreman_api.return_value = mock_api

        allowed_features = ["katello_errata_install"]
        register_remote_execution_features(mcp, allowed_features)

        result = json.loads(self._get_resource_result(mcp, mock_ctx))

        assert result["allowed_labels"] == ["katello_errata_install"]
        assert len(result["features"]) == 1

        feature = result["features"][0]
        assert feature["label"] == "katello_errata_install"
        assert feature["id"] == 1
        assert feature["name"] == "Katello Errata Install"
        assert feature["job_template_id"] == 42
        assert feature["job_template_name"] == "Install Errata - Katello Script Default"
        assert feature["error"] is None

    @patch("foreman_mcp_server.resources.remote_execution_features.get_foreman_api")
    def test_nonexistent_feature_label_reports_error(
        self, mock_get_foreman_api, mcp, mock_ctx
    ):
        """Test that a feature label not found in Foreman is reported with error."""
        mock_api = Mock()
        mock_api.call.side_effect = [
            # First call: remote_execution_features index - no matching feature
            {"results": []},
            # Second call: job_templates index (empty, no IDs to fetch)
            {"results": []},
        ]
        mock_get_foreman_api.return_value = mock_api

        allowed_features = ["nonexistent_feature"]
        register_remote_execution_features(mcp, allowed_features)

        result = json.loads(self._get_resource_result(mcp, mock_ctx))

        assert len(result["features"]) == 1
        feature = result["features"][0]
        assert feature["label"] == "nonexistent_feature"
        assert feature["id"] is None
        assert feature["error"] == "Feature not found in Foreman"

    @patch("foreman_mcp_server.resources.remote_execution_features.get_foreman_api")
    def test_feature_with_inaccessible_template(
        self, mock_get_foreman_api, mcp, mock_ctx
    ):
        """Test that a feature whose template is not returned is reported with error."""
        mock_api = Mock()
        mock_api.call.side_effect = [
            # First call: remote_execution_features index
            {
                "results": [
                    {
                        "id": 1,
                        "label": "restricted_feature",
                        "name": "Restricted Feature",
                        "description": "Feature with restricted template",
                        "job_template_id": 999,
                    }
                ]
            },
            # Second call: job_templates index - template not returned (permissions)
            {"results": []},
        ]
        mock_get_foreman_api.return_value = mock_api

        allowed_features = ["restricted_feature"]
        register_remote_execution_features(mcp, allowed_features)

        result = json.loads(self._get_resource_result(mcp, mock_ctx))

        assert len(result["features"]) == 1
        feature = result["features"][0]
        assert feature["label"] == "restricted_feature"
        assert feature["id"] == 1
        assert feature["job_template_id"] == 999
        assert feature["error"] == "Job template (id=999) not accessible"

    @patch("foreman_mcp_server.resources.remote_execution_features.get_foreman_api")
    def test_feature_without_job_template(self, mock_get_foreman_api, mcp, mock_ctx):
        """Test that a feature with no associated job template is reported."""
        mock_api = Mock()
        mock_api.call.side_effect = [
            # First call: remote_execution_features index
            {
                "results": [
                    {
                        "id": 1,
                        "label": "no_template_feature",
                        "name": "No Template Feature",
                        "description": "Feature without template",
                        "job_template_id": None,
                    }
                ]
            },
            # Second call: no job templates fetched (no IDs)
            {"results": []},
        ]
        mock_get_foreman_api.return_value = mock_api

        allowed_features = ["no_template_feature"]
        register_remote_execution_features(mcp, allowed_features)

        result = json.loads(self._get_resource_result(mcp, mock_ctx))

        assert len(result["features"]) == 1
        feature = result["features"][0]
        assert feature["label"] == "no_template_feature"
        assert feature["error"] == "Feature has no associated job template"

    @patch("foreman_mcp_server.resources.remote_execution_features.get_foreman_api")
    def test_multiple_allowed_features_batch_fetches_templates(
        self, mock_get_foreman_api, mcp, mock_ctx
    ):
        """Test that multiple allowed features result in a single batch template fetch."""
        mock_api = Mock()
        mock_api.call.side_effect = [
            # First call: remote_execution_features index
            {
                "results": [
                    {
                        "id": 1,
                        "label": "feature_a",
                        "name": "Feature A",
                        "description": "First feature",
                        "job_template_id": 10,
                    },
                    {
                        "id": 2,
                        "label": "feature_b",
                        "name": "Feature B",
                        "description": "Second feature",
                        "job_template_id": 20,
                    },
                ]
            },
            # Second call: job_templates batch fetch
            {
                "results": [
                    {
                        "id": 10,
                        "name": "Template A",
                    },
                    {
                        "id": 20,
                        "name": "Template B",
                    },
                ]
            },
        ]
        mock_get_foreman_api.return_value = mock_api

        allowed_features = ["feature_a", "feature_b"]
        register_remote_execution_features(mcp, allowed_features)

        result = json.loads(self._get_resource_result(mcp, mock_ctx))

        assert len(result["features"]) == 2
        assert result["features"][0]["label"] == "feature_a"
        assert result["features"][0]["job_template_name"] == "Template A"
        assert result["features"][1]["label"] == "feature_b"
        assert result["features"][1]["job_template_name"] == "Template B"

        # Verify batch fetch - job_templates.index called with feature.label search
        calls = mock_api.call.call_args_list
        assert len(calls) == 2
        assert calls[1][0][0] == "job_templates"
        assert calls[1][0][1] == "index"
        # Search should use feature.label with IN syntax
        search_param = calls[1][0][2]["search"]
        assert search_param == "feature.label ^ (feature_a, feature_b)"

    @patch("foreman_mcp_server.resources.remote_execution_features.get_foreman_api")
    def test_api_error_returns_error_message(self, mock_get_foreman_api, mcp, mock_ctx):
        """Test that an API error returns an error message in the response."""
        mock_get_foreman_api.return_value.call.side_effect = Exception(
            "Connection refused"
        )

        allowed_features = ["some_feature"]
        register_remote_execution_features(mcp, allowed_features)

        result = json.loads(self._get_resource_result(mcp, mock_ctx))

        assert result["features"] == []
        assert result["allowed_labels"] == ["some_feature"]
        assert "Connection refused" in result["error"]

    @patch("foreman_mcp_server.resources.remote_execution_features.get_foreman_api")
    def test_mixed_found_and_not_found_features(
        self, mock_get_foreman_api, mcp, mock_ctx
    ):
        """Test a mix of existing and non-existing features."""
        mock_api = Mock()
        mock_api.call.side_effect = [
            # First call: only one feature exists
            {
                "results": [
                    {
                        "id": 1,
                        "label": "existing_feature",
                        "name": "Existing Feature",
                        "description": "This one exists",
                        "job_template_id": 50,
                    }
                ]
            },
            # Second call: template fetch
            {
                "results": [
                    {
                        "id": 50,
                        "name": "Existing Template",
                    }
                ]
            },
        ]
        mock_get_foreman_api.return_value = mock_api

        allowed_features = ["existing_feature", "missing_feature"]
        register_remote_execution_features(mcp, allowed_features)

        result = json.loads(self._get_resource_result(mcp, mock_ctx))

        assert len(result["features"]) == 2

        existing = result["features"][0]
        assert existing["label"] == "existing_feature"
        assert existing["error"] is None

        missing = result["features"][1]
        assert missing["label"] == "missing_feature"
        assert missing["error"] == "Feature not found in Foreman"


class TestHelperFunctions:
    """Test helper functions."""

    def test_build_feature_entry_with_all_data(self):
        feature = {
            "id": 1,
            "name": "Test Feature",
            "description": "A test feature",
        }
        result = _build_feature_entry(
            label="test_feature",
            feature=feature,
            template_id=42,
            template_name="Test Template",
            error=None,
        )

        assert result["label"] == "test_feature"
        assert result["id"] == 1
        assert result["name"] == "Test Feature"
        assert result["description"] == "A test feature"
        assert result["job_template_id"] == 42
        assert result["job_template_name"] == "Test Template"
        assert result["error"] is None

    def test_build_feature_entry_with_error(self):
        result = _build_feature_entry(
            label="missing_feature", error="Feature not found in Foreman"
        )

        assert result["label"] == "missing_feature"
        assert result["id"] is None
        assert result["name"] is None
        assert result["job_template_id"] is None
        assert result["error"] == "Feature not found in Foreman"
