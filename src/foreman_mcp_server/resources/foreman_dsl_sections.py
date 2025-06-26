
# TODO: Change hardcoded section list
def register_foreman_dsl_sections(mcp, foreman_api):
  """Register all Foreman DSL sections with the MCP server."""

  @mcp.resource(
    name='Foreman DSL Sections',
    description='Returns all Foreman DSL sections available for template writing.',
    uri='foreman://documentation/dsl/sections',
    mime_type='text/plain'
  )
  def foreman_dsl_sections() -> str:
    sections = ('all', 'reports', 'provisioning', 'jobs', 'partition_tables', 'additional', 'basic_ruby_methods', 'webhooks')
    return ', '.join(sections)
