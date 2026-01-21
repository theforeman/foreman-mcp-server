from .errata import register_errata_prompts
from .reporting import register_reporting_prompts
from .template_writing import register_template_writing_prompts


def register_prompts(mcp, foreman_api, get_context):
    """Register all prompts with the MCP server."""
    register_reporting_prompts(mcp, foreman_api, get_context)
    register_template_writing_prompts(mcp, foreman_api, get_context)
    register_errata_prompts(mcp, foreman_api, get_context)
