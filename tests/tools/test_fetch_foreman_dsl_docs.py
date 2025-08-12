from unittest.mock import AsyncMock, Mock, patch

import pytest

from foreman_mcp_server.tools.fetch_foreman_dsl_docs import (
    register_fetch_foreman_dsl_docs,
)


class TestFetchForemanDslDocs:

    @pytest.mark.parametrize("anyio_backend", ["asyncio"])
    @pytest.mark.anyio
    @patch("foreman_mcp_server.tools.fetch_foreman_dsl_docs.assert_resource")
    @patch("foreman_mcp_server.tools.fetch_foreman_dsl_docs.save_dsl_docs_as_markdown")
    @patch("foreman_mcp_server.tools.fetch_foreman_dsl_docs.build_tool_result")
    @patch("foreman_mcp_server.tools.fetch_foreman_dsl_docs.mcp_info_headers")
    async def test_fetch_foreman_dsl_docs_tool_execution_success(
        self,
        mock_mcp_info_headers,
        mock_build_tool_result,
        mock_save_dsl_docs,
        mock_assert_resource,
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc_cache_dir = "/test/cache/dir"
        mock_foreman_api.http_call = Mock(return_value={"test": "response"})
        mock_get_context = Mock()
        mock_mcp = Mock()

        # Setup mocks
        mock_assert_resource.return_value = AsyncMock()
        mock_save_dsl_docs.return_value = AsyncMock()
        mock_tool_result = Mock()
        mock_build_tool_result.return_value = mock_tool_result
        mock_mcp_info_headers.return_value = {"User-Agent": "test"}

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
        register_fetch_foreman_dsl_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Execute the tool
        result = await tool_func("test_section")

        # Verify tool execution
        mock_assert_resource.assert_called_once_with(
            "test_section",
            {"name": "Section", "list_name": "sections", "type": "dsl"},
            mock_get_context,
        )
        mock_mcp_info_headers.assert_called_once_with(mock_get_context)
        mock_foreman_api.http_call.assert_called_once_with(
            "get",
            "/templates_doc/v1/test_section.en.json",
            headers={"User-Agent": "test"},
        )
        mock_save_dsl_docs.assert_called_once_with(
            "/test/cache/dir", "test_section.en.md", {"test": "response"}
        )
        mock_build_tool_result.assert_called_once_with({
            "message": "DSL documentation for section 'test_section' fetched successfully and saved to cache.",
            "file": "test_section.en.md",
            "state": "present",
        })
        assert result == mock_tool_result

    @pytest.mark.parametrize("anyio_backend", ["asyncio"])
    @pytest.mark.anyio
    @patch("foreman_mcp_server.tools.fetch_foreman_dsl_docs.assert_resource")
    @patch("foreman_mcp_server.tools.fetch_foreman_dsl_docs.build_tool_result")
    async def test_fetch_foreman_dsl_docs_tool_execution_http_error(
        self, mock_build_tool_result, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.http_call = Mock(side_effect=Exception("HTTP Error"))
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
        register_fetch_foreman_dsl_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Execute the tool
        result = await tool_func("test_section")

        # Verify error handling
        mock_build_tool_result.assert_called_once_with({
            "message": "Failed to fetch DSL documentation for section 'test_section'",
            "error": "HTTP Error",
        })
        assert result == mock_tool_result
