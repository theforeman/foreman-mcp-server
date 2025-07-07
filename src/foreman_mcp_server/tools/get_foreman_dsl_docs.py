from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..utils.dsl_docs_utils import read_dsl_docs_from_markdown
from ..utils.utils import check_resource


def register_get_foreman_dsl_docs(mcp, foreman_api, get_context):
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
    async def get_foreman_dsl_docs(section: str) -> ToolResult:
        try:
            is_not_in_list = await check_resource(
                section,
                {"name": "Section", "list_name": "sections", "type": "dsl"},
                get_context,
            )
            if is_not_in_list:
                return is_not_in_list
            docs = await read_dsl_docs_from_markdown(
                foreman_api.apidoc_cache_dir, f"{section}.en.md"
            )
            message = f"DSL documentation for section '{section}' read successfully"
            return ToolResult(
                content=[TextContent(type="text", text=f"{message}: {docs}")],
                structured_content={
                    "message": message,
                    "section": section,
                    "documentation": docs,
                },
            )
        except FileNotFoundError:
            message = f"The cache file for section '{section}' is not found. Please fetch the DSL documentation first."
            return ToolResult(
                content=[TextContent(type="text", text=message)],
                structured_content={
                    "message": message,
                    "file": f"{section}.en.md",
                    "state": "absent",
                },
            )
        except Exception as e:
            message = f"Failed to read DSL documentation for section '{section}'"
            return ToolResult(
                content=[TextContent(type="text", text=f"{message}: {str(e)}")],
                structured_content={"message": message, "error": str(e)},
            )
