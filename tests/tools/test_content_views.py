from unittest.mock import Mock

import pytest
from fastmcp import FastMCP
from requests.exceptions import HTTPError

from foreman_mcp_server.tools.content_views import (
    format_content_view_failure,
    format_incremental_update_success,
    format_promote_success,
    format_publish_success,
    register_content_view_tools,
)
from foreman_mcp_server.utils.content_utils import derive_legacy_content


class TestIncrementalContentViewUpdate:
    def test_format_incremental_update_success_with_task(self):
        response = {
            "task": {"id": "task-abc-123"},
            "version": "2.1",
        }

        result = format_incremental_update_success(response)

        assert (
            result.structured_content["message"]
            == "Incremental content view update triggered successfully."
        )
        assert result.structured_content["task_id"] == "task-abc-123"
        assert result.structured_content["response"] == response

    def test_format_incremental_update_success_direct_task(self):
        response = {
            "id": "task-direct-456",
            "state": "planned",
        }

        result = format_incremental_update_success(response)

        assert result.structured_content["task_id"] == "task-direct-456"

    def test_format_incremental_update_success_no_task(self):
        response = {"results": []}

        result = format_incremental_update_success(response)

        assert result.structured_content["task_id"] is None


class TestPublishContentView:
    def test_format_publish_success(self):
        response = {
            "id": "task-pub-789",
            "state": "planned",
        }

        result = format_publish_success(response, content_view_id=42)

        assert (
            result.structured_content["message"]
            == "Content view 42 publish triggered successfully."
        )
        assert result.structured_content["task_id"] == "task-pub-789"
        assert result.structured_content["content_view_id"] == 42

    def test_format_publish_success_no_task_id(self):
        response = {"status": "ok"}

        result = format_publish_success(response, content_view_id=10)

        assert result.structured_content["task_id"] is None
        assert result.structured_content["content_view_id"] == 10


class TestPromoteContentViewVersion:
    def test_format_promote_success(self):
        response = {
            "id": "task-promo-101",
            "state": "planned",
        }

        result = format_promote_success(response, version_id=5, environment_ids=[1, 2])

        assert (
            result.structured_content["message"]
            == "Content view version 5 promotion triggered successfully."
        )
        assert result.structured_content["task_id"] == "task-promo-101"
        assert result.structured_content["content_view_version_id"] == 5
        assert result.structured_content["environment_ids"] == [1, 2]

    def test_format_promote_success_no_task_id(self):
        response = {}

        result = format_promote_success(response, version_id=3, environment_ids=[1])

        assert result.structured_content["task_id"] is None


class TestContentViewFailure:
    def test_format_failure(self):
        error = Exception("Connection refused")

        result = format_content_view_failure("incremental update", error)

        assert (
            result.structured_content["message"]
            == "Failed to incremental update content view."
        )
        assert result.structured_content["error"] == "Connection refused"

    def test_format_failure_with_http_error_json(self):
        error = HTTPError(
            "422 Unprocessable Entity",
            response=Mock(text='{"error": "Content view version not found"}'),
        )

        result = format_content_view_failure("publish", error)

        assert "Failed to publish content view" in result.structured_content["message"]
        assert result.structured_content["response"] == {
            "error": "Content view version not found"
        }

    def test_format_failure_with_http_error_html(self):
        error = HTTPError(
            "500 Internal Server Error",
            response=Mock(text="<html>Error</html>"),
        )

        result = format_content_view_failure("promote", error)

        assert result.structured_content["response"] == "<html>Error</html>"


class TestLegacyContentDerivation:
    """Test that structured content can be properly converted to legacy text format."""

    def test_incremental_update_legacy_content(self):
        response = {
            "task": {"id": "task-123"},
        }

        result = format_incremental_update_success(response)
        content = derive_legacy_content(result.structured_content)

        assert "Incremental content view update triggered successfully" in content
        assert "task-123" in content

    def test_publish_legacy_content(self):
        response = {"id": "task-pub-1"}

        result = format_publish_success(response, content_view_id=7)
        content = derive_legacy_content(result.structured_content)

        assert "Content view 7 publish triggered successfully" in content
        assert "task-pub-1" in content

    def test_promote_legacy_content(self):
        response = {"id": "task-promo-2"}

        result = format_promote_success(response, version_id=12, environment_ids=[3, 4])
        content = derive_legacy_content(result.structured_content)

        assert "Content view version 12 promotion triggered successfully" in content
        assert "task-promo-2" in content


class TestToolRegistration:
    """Test that tools are properly registered with the MCP server."""

    @pytest.fixture
    def mcp(self):
        return FastMCP(name="Test MCP Server")

    def test_tools_are_registered(self, mcp):
        """Test that all content view tools are registered."""
        register_content_view_tools(mcp, ["incremental_update", "publish", "promote"])

        tools = mcp._tool_manager._tools
        assert "incremental_content_view_update" in tools
        assert "publish_content_view" in tools
        assert "promote_content_view_version" in tools

    def test_incremental_update_tool_annotations(self, mcp):
        """Test that tool annotations are set correctly."""
        register_content_view_tools(mcp, ["incremental_update"])

        tool = mcp._tool_manager._tools["incremental_content_view_update"]
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is True

    def test_publish_tool_annotations(self, mcp):
        """Test that publish tool annotations are set correctly."""
        register_content_view_tools(mcp, ["publish"])

        tool = mcp._tool_manager._tools["publish_content_view"]
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is True

    def test_promote_tool_annotations(self, mcp):
        """Test that promote tool annotations are set correctly."""
        register_content_view_tools(mcp, ["promote"])

        tool = mcp._tool_manager._tools["promote_content_view_version"]
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is True

    def test_empty_allowlist_disables_all_tools(self, mcp):
        """Test that an empty allowlist registers all tools as disabled."""
        register_content_view_tools(mcp, [])

        tools = mcp._tool_manager._tools
        assert tools["incremental_content_view_update"].enabled is False
        assert tools["publish_content_view"].enabled is False
        assert tools["promote_content_view_version"].enabled is False

    def test_default_allowlist_disables_all_tools(self, mcp):
        """Test that the default (no allowlist) registers all tools as disabled."""
        register_content_view_tools(mcp)

        tools = mcp._tool_manager._tools
        assert tools["incremental_content_view_update"].enabled is False
        assert tools["publish_content_view"].enabled is False
        assert tools["promote_content_view_version"].enabled is False

    def test_selective_allowlist_enables_only_specified_tools(self, mcp):
        """Test that only specified actions are enabled."""
        register_content_view_tools(mcp, ["publish"])

        tools = mcp._tool_manager._tools
        assert tools["incremental_content_view_update"].enabled is False
        assert tools["publish_content_view"].enabled is True
        assert tools["promote_content_view_version"].enabled is False

    def test_all_actions_enabled(self, mcp):
        """Test that all actions can be enabled."""
        register_content_view_tools(mcp, ["incremental_update", "publish", "promote"])

        tools = mcp._tool_manager._tools
        assert tools["incremental_content_view_update"].enabled is True
        assert tools["publish_content_view"].enabled is True
        assert tools["promote_content_view_version"].enabled is True
