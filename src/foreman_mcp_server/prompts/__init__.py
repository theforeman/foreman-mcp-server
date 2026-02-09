from .reporting import register_reporting_prompts
from .template_writing import register_template_writing_prompts


def register_prompts(mcp):
    """Register all reporting related prompts with the MCP server."""
    register_reporting_prompts(mcp)
    register_template_writing_prompts(mcp)
