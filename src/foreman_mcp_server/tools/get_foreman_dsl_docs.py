from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult

from ..utils.content_utils import build_tool_result
from ..utils.dsl_docs_utils import read_dsl_docs_from_markdown
from ..utils.utils import assert_resource, get_foreman_api


def register_get_foreman_dsl_docs(mcp, foreman_api):
    @mcp.tool(
        description="Reads from cache and returns the documentation of available macros"
        " for template writing in Markdown format based on provided section.",
        tags=("foreman", "docs", "dsl", "markdown", "local", "file"),
        annotations={
            "title": "Get Foreman DSL Documentation",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def get_foreman_dsl_docs(
        section: str,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        try:
            api = foreman_api or get_foreman_api(ctx)
            await assert_resource(
                section,
                {"name": "Section", "list_name": "sections", "type": "dsl"},
                ctx,
            )
            docs = await read_dsl_docs_from_markdown(
                api.apidoc_cache_dir, f"{section}.en.md"
            )
            message = f"DSL documentation for section '{section}' read successfully"
            return build_tool_result(
                {
                    "message": message,
                    "section": section,
                    "documentation": docs,
                }
            )
        except FileNotFoundError:
            message = f"The cache file for section '{section}' is not found. Please fetch the DSL documentation first."
            return build_tool_result(
                {
                    "message": message,
                    "file": f"{section}.en.md",
                    "state": "absent",
                }
            )
        except Exception as e:
            message = f"Failed to read DSL documentation for section '{section}'"
            return build_tool_result(
                {
                    "message": message,
                    "error": str(e),
                }
            )
