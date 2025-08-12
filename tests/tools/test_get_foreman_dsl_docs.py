from unittest.mock import AsyncMock, Mock, patch

import pytest

from foreman_mcp_server.tools.get_foreman_dsl_docs import register_get_foreman_dsl_docs


class TestGetForemanDslDocs:

    @pytest.mark.parametrize("anyio_backend", ["asyncio"])
    @pytest.mark.anyio
    @patch("foreman_mcp_server.tools.get_foreman_dsl_docs.assert_resource")
    @patch("foreman_mcp_server.tools.get_foreman_dsl_docs.read_dsl_docs_from_markdown")
    @patch("foreman_mcp_server.tools.get_foreman_dsl_docs.build_tool_result")
    async def test_get_foreman_dsl_docs_tool_execution_success(
        self, mock_build_tool_result, mock_read_dsl_docs, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc_cache_dir = "/test/cache/dir"
        mock_get_context = Mock()
        mock_mcp = Mock()

        # Setup mocks
        mock_assert_resource.return_value = AsyncMock()
        mock_read_dsl_docs.return_value = "Test DSL documentation content"
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
        register_get_foreman_dsl_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Execute the tool
        result = await tool_func("test_section")

        # Verify tool execution
        mock_assert_resource.assert_called_once_with(
            "test_section",
            {"name": "Section", "list_name": "sections", "type": "dsl"},
            mock_get_context,
        )
        mock_read_dsl_docs.assert_called_once_with(
            "/test/cache/dir", "test_section.en.md"
        )
        mock_build_tool_result.assert_called_once_with({
            "message": "DSL documentation for section 'test_section' read successfully",
            "section": "test_section",
            "documentation": "Test DSL documentation content",
        })
        assert result == mock_tool_result

    @pytest.mark.parametrize("anyio_backend", ["asyncio"])
    @pytest.mark.anyio
    @patch("foreman_mcp_server.tools.get_foreman_dsl_docs.assert_resource")
    @patch("foreman_mcp_server.tools.get_foreman_dsl_docs.read_dsl_docs_from_markdown")
    @patch("foreman_mcp_server.tools.get_foreman_dsl_docs.build_tool_result")
    async def test_get_foreman_dsl_docs_tool_execution_file_not_found(
        self, mock_build_tool_result, mock_read_dsl_docs, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc_cache_dir = "/test/cache/dir"
        mock_get_context = Mock()
        mock_mcp = Mock()

        # Setup mocks
        mock_assert_resource.return_value = AsyncMock()
        mock_read_dsl_docs.side_effect = FileNotFoundError()
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
        register_get_foreman_dsl_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Execute the tool
        result = await tool_func("missing_section")

        # Verify tool execution
        mock_build_tool_result.assert_called_once_with({
            "message": "The cache file for section 'missing_section' is not found. Please fetch the DSL documentation first.",
            "file": "missing_section.en.md",
            "state": "absent",
        })
        assert result == mock_tool_result
