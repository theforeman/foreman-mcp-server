from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from foreman_mcp_server.utils.utils import get_foreman_api

from ..utils.dsl_docs_utils import read_dsl_docs_from_markdown


def register_foreman_dsl_docs(mcp, foreman_api):
    @mcp.resource(
        name="Foreman DSL Documentation",
        description="Reads from cache and returns the documentation of available macros for template writing in Markdown format based on provided section.",
        uri="foreman://documentation/dsl/{section}",
        mime_type="text/plain",
    )
    async def foreman_dsl_docs(
        section: str,
        ctx: Context = CurrentContext(),
    ) -> str:
        try:
            api = foreman_api or get_foreman_api(ctx)
            docs = await read_dsl_docs_from_markdown(
                api.apidoc_cache_dir, f"{section}.en.md"
            )
            return docs
        except Exception as e:
            return f'error: Failed to read DSL documentation for section "{section}": {str(e)}'
