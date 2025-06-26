from ..utils.dsl_docs_utils import save_dsl_docs_as_markdown

def register_fetch_foreman_dsl_docs(mcp, foreman_api):
  """Register the tool to fetch DSL documentation from Foreman."""

  @mcp.tool
  async def fetch_foreman_dsl_docs(section: str) -> str:
    """Fetches the DSL documentation from Foreman."""

    try:
      # TODO: Fix apipie-dsl since it returns all.en.json for non-existing sections
      response = foreman_api.http_call('get', f'/templates_doc/v1/{section}.en.json')
      await save_dsl_docs_as_markdown(foreman_api.apidoc_cache_dir, f'{section}.en.md', response)
      return f"DSL documentation for section '{section}' fetched successfully and saved to cache."
    except Exception as e:
      return f"Failed to fetch DSL documentation: {str(e)}"
