from .call_foreman_api import register_foreman_api_methods
from .fetch_foreman_dsl_docs import register_fetch_foreman_dsl_docs
from .get_foreman_api_resource_docs import register_get_foreman_api_resource_docs
from .get_foreman_dsl_docs import register_get_foreman_dsl_docs

# TODO: Maybe hammer can be a tool?
# TODO: Maybe foreman-maintain can be a tool?


def register_tools(mcp, foreman_api, get_context):
    """Register all tools with the MCP server."""

    register_foreman_api_methods(mcp, foreman_api, get_context)
    register_fetch_foreman_dsl_docs(mcp, foreman_api, get_context)
    # TODO: Remove when Claude Desktop supports Resource with parameters
    register_get_foreman_api_resource_docs(mcp, foreman_api, get_context)
    register_get_foreman_dsl_docs(mcp, foreman_api, get_context)
