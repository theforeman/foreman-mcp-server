from ..utils.dsl_docs_utils import read_dsl_docs_from_markdown


def register_foreman_dsl_docs(mcp, foreman_api):
    @mcp.resource(
        name="Foreman DSL Documentation",
        description="Reads from cache and returns the documentation of available macros for template writing in Markdown format based on provided section.",
        uri="foreman://documentation/dsl/{section}",
        mime_type="text/plain",
    )
    async def foreman_dsl_docs(section: str) -> str:
        try:
            docs = await read_dsl_docs_from_markdown(
                foreman_api.apidoc_cache_dir, f"{section}.en.md"
            )
            return docs
        except Exception as e:
            return f'error: Failed to read DSL documentation for section "{section}": {str(e)}'
