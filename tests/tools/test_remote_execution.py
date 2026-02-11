import asyncio
from unittest.mock import Mock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from requests.exceptions import HTTPError

from foreman_mcp_server.tools.remote_execution import (
    format_job_invocation_failure,
    format_job_invocation_success,
    register_remote_execution_tools,
)
from foreman_mcp_server.utils.content_utils import derive_legacy_content


class TestTriggerRemoteExecutionJob:
    def test_format_job_invocation_success(self):
        response = {
            "id": 123,
            "description": "Apply errata RHSA-2025:1234",
            "status": 0,
            "status_label": "queued",
            "task": {"id": "abc-123-def"},
            "targeting": {"search_query": "installable_errata = RHSA-2025:1234"},
            "total_hosts_count": 5,
        }

        result = format_job_invocation_success(response)

        assert result.structured_content["message"] == "Remote execution job triggered successfully."
        assert result.structured_content["job_invocation_id"] == 123
        assert result.structured_content["task_id"] == "abc-123-def"
        assert result.structured_content["description"] == "Apply errata RHSA-2025:1234"
        assert result.structured_content["targeting"]["hosts_count"] == 5

    def test_format_job_invocation_success_without_task(self):
        response = {
            "id": 123,
            "description": "Test job",
            "status": 0,
            "status_label": "queued",
            "task": None,
            "targeting": {"search_query": "name ~ test"},
            "total_hosts_count": 1,
        }

        result = format_job_invocation_success(response)

        assert result.structured_content["task_id"] is None

    def test_format_job_invocation_failure(self):
        error = Exception("Connection refused")

        result = format_job_invocation_failure(error)

        assert result.structured_content["message"] == "Failed to trigger remote execution job."
        assert result.structured_content["error"] == "Connection refused"

    def test_format_job_invocation_failure_with_http_error(self):
        error = HTTPError(
            "422 Unprocessable Entity",
            response=Mock(text='{"error": "Job template not found"}'),
        )

        result = format_job_invocation_failure(error)

        assert result.structured_content["message"] == "Failed to trigger remote execution job."
        assert "422 Unprocessable Entity" in result.structured_content["error"]
        assert result.structured_content["response"] == {"error": "Job template not found"}

    def test_format_job_invocation_failure_with_http_error_html_response(self):
        error = HTTPError(
            "500 Internal Server Error",
            response=Mock(text="<html>Internal Error</html>"),
        )

        result = format_job_invocation_failure(error)

        assert result.structured_content["response"] == "<html>Internal Error</html>"


class TestLegacyContentDerivation:
    """Test that structured content can be properly converted to legacy text format."""

    def test_job_invocation_success_legacy_content(self):
        response = {
            "id": 123,
            "task": {"id": "abc-123"},
            "targeting": {"search_query": "name ~ test"},
            "total_hosts_count": 2,
            "status": 0,
            "status_label": "queued",
            "description": "Test job",
        }

        result = format_job_invocation_success(response)
        content = derive_legacy_content(result.structured_content)

        assert "Remote execution job triggered successfully" in content
        assert "123" in content  # job_invocation_id
        assert "abc-123" in content  # task_id


class TestRexFeatureAllowlist:
    """Test remote execution feature allowlist functionality."""

    @pytest.fixture
    def mcp(self):
        return FastMCP(name="Test MCP Server")

    @pytest.fixture
    def mock_ctx(self):
        return Mock()

    @patch("foreman_mcp_server.tools.remote_execution.get_foreman_api")
    def test_allowed_feature_passes(self, mock_get_foreman_api, mcp, mock_ctx):
        """Test that an allowed feature passes validation."""
        mock_api = Mock()
        mock_api.call.return_value = {
            "id": 123,
            "description": "Test job",
            "status": 0,
            "status_label": "queued",
            "task": {"id": "task-123"},
            "targeting": {"search_query": "name ~ test"},
            "total_hosts_count": 1,
        }
        mock_get_foreman_api.return_value = mock_api

        allowed_features = ["katello_errata_install", "katello_package_install"]
        register_remote_execution_tools(mcp, allowed_features)

        # Get the registered tool function
        tool = mcp._tool_manager._tools["trigger_remote_execution_job"]

        result = asyncio.run(
            tool.fn(
                feature="katello_errata_install",
                search_query="name ~ test",
                ctx=mock_ctx,
            )
        )

        assert result.structured_content["job_invocation_id"] == 123
        mock_api.call.assert_called_once()

    def test_disallowed_feature_raises_error(self, mcp, mock_ctx):
        """Test that a disallowed feature raises ToolError."""
        allowed_features = ["katello_errata_install"]
        register_remote_execution_tools(mcp, allowed_features)

        tool = mcp._tool_manager._tools["trigger_remote_execution_job"]

        with pytest.raises(ToolError) as exc_info:
            asyncio.run(
                tool.fn(
                    feature="run_arbitrary_script",
                    search_query="name ~ test",
                    ctx=mock_ctx,
                )
            )

        assert "not allowed" in str(exc_info.value)
        assert "run_arbitrary_script" in str(exc_info.value)
        assert "katello_errata_install" in str(exc_info.value)

    def test_empty_allowlist_disables_tool(self, mcp):
        """Test that an empty allowlist registers the tool as disabled."""
        register_remote_execution_tools(mcp, [])

        tool = mcp._tool_manager._tools["trigger_remote_execution_job"]
        assert tool.enabled is False

