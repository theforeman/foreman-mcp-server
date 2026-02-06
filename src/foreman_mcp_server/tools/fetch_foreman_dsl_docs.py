from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult

from ..utils.content_utils import build_tool_result
from ..utils.dsl_docs_utils import save_dsl_docs_as_markdown
from ..utils.utils import assert_resource, get_foreman_api, mcp_info_headers


def register_fetch_foreman_dsl_docs(mcp, foreman_api):
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
    async def fetch_foreman_dsl_docs(
        section: str,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        try:
            # TODO: Fix apipie-dsl since it returns all.en.json for non-existing sections
            api = foreman_api or get_foreman_api(ctx)
            await assert_resource(
                section,
                {"name": "Section", "list_name": "sections", "type": "dsl"},
                ctx,
            )
            response = api.http_call(
                "get",
                f"/templates_doc/v1/{section}.en.json",
                headers=mcp_info_headers(ctx),
            )
            await save_dsl_docs_as_markdown(
                api.apidoc_cache_dir, f"{section}.en.md", response
            )
            message = f"DSL documentation for section '{section}' fetched successfully and saved to cache."
            return build_tool_result(
                {
                    "message": message,
                    "file": f"{section}.en.md",
                    "state": "present",
                }
            )
        except Exception as e:
            message = f"Failed to fetch DSL documentation for section '{section}'"
            return build_tool_result(
                {
                    "message": message,
                    "error": str(e),
                }
            )
