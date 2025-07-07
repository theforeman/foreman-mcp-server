from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..utils.dsl_docs_utils import save_dsl_docs_as_markdown
from ..utils.utils import check_resource


def register_fetch_foreman_dsl_docs(mcp, foreman_api, get_context):
    """Register the tool to fetch DSL documentation from Foreman."""

    @mcp.tool(
        description="Fetches the DSL documentation from Foreman for a specific section.",
        tags=("foreman", "docs", "dsl", "remote", "api"),
        annotations={
            "title": "Fetch Foreman DSL Documentation",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def fetch_foreman_dsl_docs(section: str) -> ToolResult:
        try:
            # TODO: Fix apipie-dsl since it returns all.en.json for non-existing sections
            is_not_in_list = await check_resource(
                section,
                {"name": "Section", "list_name": "sections", "type": "dsl"},
                get_context,
            )
            if is_not_in_list:
                return is_not_in_list
            response = foreman_api.http_call(
                "get", f"/templates_doc/v1/{section}.en.json"
            )
            await save_dsl_docs_as_markdown(
                foreman_api.apidoc_cache_dir, f"{section}.en.md", response
            )
            message = f"DSL documentation for section '{section}' fetched successfully and saved to cache."
            return ToolResult(
                content=[TextContent(type="text", text=message)],
                structured_content={
                    "message": message,
                    "file": f"{section}.en.md",
                    "state": "present",
                },
            )
        except Exception as e:
            message = f"Failed to fetch DSL documentation for section '{section}'"
            return ToolResult(
                content=[TextContent(type="text", text=f"{message}: {str(e)}")],
                structured_content={"message": message, "error": str(e)},
            )
