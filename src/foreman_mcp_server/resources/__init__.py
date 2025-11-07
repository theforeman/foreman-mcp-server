from .foreman_api_resource_docs import register_foreman_api_resource_docs
from .foreman_api_resources import register_foreman_api_resources
from .foreman_dsl_docs import register_foreman_dsl_docs
from .foreman_dsl_sections import register_foreman_dsl_sections
from .foreman_template_resources import register_foreman_template_resources
from .hammer_docs import register_hammer_docs
from .hammer_resources import register_hammer_resources

# TODO: For some resources consider refactoring: fetch_resource tool, search_resource tool.
# TODO: Maybe local logs can be a resource?


def register_resources(mcp, foreman_api, get_context):
    """Register all Foreman resources with the MCP server."""
    register_foreman_api_resources(mcp, foreman_api, get_context)
    register_foreman_api_resource_docs(mcp, foreman_api, get_context)
    register_foreman_dsl_sections(mcp, foreman_api)
    register_foreman_dsl_docs(mcp, foreman_api, get_context)
    register_foreman_template_resources(mcp, foreman_api, get_context)
    register_hammer_docs(mcp, foreman_api, get_context)
    register_hammer_resources(mcp, foreman_api, get_context)
