from fastmcp.tools.tool import ToolResult

from ..utils.hammer_utils import (
    execute_hammer_command_for_tool,
)


def register_hammer_commands(mcp):
    @mcp.tool(
        description="Execute a hammer CLI command with any arguments and return its output. Use "
        "this ONLY when the user explicitly wants to execute a command on the MCP server's "
        "environment. A leading 'hammer' is NOT required in the command.",
        tags=("hammer", "cli", "command", "local"),
        annotations={
            "title": "Execute Hammer CLI Command",
            "readOnlyHint": False,
            "destructiveHint": True,  # Hammer can be destructive
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def execute_hammer(command: str) -> ToolResult:
        return await execute_hammer_command_for_tool(command)
