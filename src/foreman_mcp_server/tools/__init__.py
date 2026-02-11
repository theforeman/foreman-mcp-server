from .call_foreman_api import register_foreman_api_methods
from .content_views import register_content_view_tools
from .fetch_foreman_dsl_docs import register_fetch_foreman_dsl_docs
from .get_foreman_api_resource_docs import register_get_foreman_api_resource_docs
from .get_foreman_dsl_docs import register_get_foreman_dsl_docs
from .remote_execution import register_remote_execution_tools
from .tasks import register_task_tools

# TODO: Maybe hammer can be a tool?
# TODO: Maybe foreman-maintain can be a tool?


def register_tools(mcp, allowed_rex_features=None):
    """Register all tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
        allowed_rex_features: Optional list of allowed remote execution feature labels
    """

    register_foreman_api_methods(mcp)
    register_content_view_tools(mcp)
    register_fetch_foreman_dsl_docs(mcp)
    # TODO: Remove when Claude Desktop supports Resource with parameters
    register_get_foreman_api_resource_docs(mcp)
    register_get_foreman_dsl_docs(mcp)
    register_remote_execution_tools(mcp, allowed_rex_features)
    register_task_tools(mcp)
