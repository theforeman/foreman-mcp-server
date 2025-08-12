from unittest.mock import AsyncMock, Mock, patch

import pytest

from foreman_mcp_server.tools.get_foreman_api_resource_docs import (
    register_get_foreman_api_resource_docs,
)


class TestGetForemanApiResourceDocs:

    @pytest.mark.parametrize("anyio_backend", ["asyncio"])
    @pytest.mark.anyio
    @patch("foreman_mcp_server.tools.get_foreman_api_resource_docs.assert_resource")
    @patch("foreman_mcp_server.tools.get_foreman_api_resource_docs.build_tool_result")
    async def test_get_foreman_api_resource_docs_tool_execution_success(
        self, mock_build_tool_result, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc = {
            "docs": {
                "resources": {
                    "test_resource": {
                        "name": "test_resource",
                        "description": "Test resource documentation",
                        "methods": ["GET", "POST"],
                    }
                }
            }
        }
        mock_get_context = Mock()
        mock_mcp = Mock()

        # Setup mocks
        mock_assert_resource.return_value = AsyncMock()
        mock_tool_result = Mock()
        mock_build_tool_result.return_value = mock_tool_result

        # Capture the registered tool function
        tool_func = None
        def capture_tool_func(*args, **kwargs):
            nonlocal tool_func
            def decorator(func):
                nonlocal tool_func
                tool_func = func
                return func
            return decorator
        mock_mcp.tool = capture_tool_func

        # Register the tool
        register_get_foreman_api_resource_docs(
            mock_mcp, mock_foreman_api, mock_get_context
        )

        # Execute the tool
        result = await tool_func("test_resource")

        # Verify tool execution
        mock_assert_resource.assert_called_once_with(
            "test_resource",
            {"name": "Resource", "list_name": "resources", "type": "api"},
            mock_get_context,
        )
        mock_build_tool_result.assert_called_once_with({
            "message": "API documentation for resource 'test_resource' fetched successfully",
            "resource": "test_resource",
            "documentation": {
                "name": "test_resource",
                "description": "Test resource documentation",
                "methods": ["GET", "POST"],
            },
        })
        assert result == mock_tool_result

    @pytest.mark.parametrize("anyio_backend", ["asyncio"])
    @pytest.mark.anyio
    @patch("foreman_mcp_server.tools.get_foreman_api_resource_docs.assert_resource")
    @patch("foreman_mcp_server.tools.get_foreman_api_resource_docs.build_tool_result")
    async def test_get_foreman_api_resource_docs_tool_execution_error(
        self, mock_build_tool_result, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc = {"docs": {"resources": {}}}
        mock_get_context = Mock()
        mock_mcp = Mock()

        # Setup mocks
        mock_assert_resource.return_value = AsyncMock()
        mock_tool_result = Mock()
        mock_build_tool_result.return_value = mock_tool_result

        # Capture the registered tool function
        tool_func = None
        def capture_tool_func(*args, **kwargs):
            nonlocal tool_func
            def decorator(func):
                nonlocal tool_func
                tool_func = func
                return func
            return decorator
        mock_mcp.tool = capture_tool_func

        # Register the tool
        register_get_foreman_api_resource_docs(
            mock_mcp, mock_foreman_api, mock_get_context
        )

        # Execute the tool (will raise KeyError for missing resource)
        result = await tool_func("missing_resource")

        # Verify error handling
        mock_build_tool_result.assert_called_once()
        call_args = mock_build_tool_result.call_args[0][0]
        assert call_args["message"] == "Failed to read API documentation for resource 'missing_resource'"
        assert "error" in call_args
        assert result == mock_tool_result
