from fastmcp.tools.tool import ToolResult

from ..utils.content_utils import build_tool_result
from ..utils.hammer_utils import execute_hammer_command, get_user_credentials


def build_success_structured_content(
    command: str, output: str, returncode: int
) -> dict:
    """Build structured content for a successful hammer command execution."""
    return {
        "message": f"Hammer command executed successfully: hammer {command}",
        "command": f"hammer {command}",
        "output": output,
        "returncode": returncode,
    }


def build_failure_structured_content(
    command: str, output: str, error: str, returncode: int
) -> dict:
    """Build structured content for a failed hammer command execution."""
    return {
        "message": f"Hammer command failed: hammer {command}",
        "command": f"hammer {command}",
        "output": output,
        "error": error,
        "returncode": returncode,
    }


def register_hammer_commands(mcp, foreman_api, _get_context):
    """Register hammer CLI command execution tools."""

    @mcp.tool(
        description="Execute a hammer CLI command with any arguments and return its output. Use "
        "this ONLY when the user explicitly wants to execute a command on the MCP server's "
        "environment. If the user just wants to know what hammer command to run, suggest it in "
        "your response without calling this tool. A leading 'hammer' is NOT required in the command.",
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
        # Get user credentials
        username, password, foreman_url = get_user_credentials(
            _get_context, foreman_api
        )

        # Execute hammer command using shared utility
        success, output, *rest = await execute_hammer_command(
            command, username, password, foreman_url
        )

        if success:
            returncode = rest[0] if rest else 0
            return build_tool_result(
                build_success_structured_content(command, output, returncode)
            )
        else:
            error = rest[0] if rest else ""
            returncode = rest[1] if len(rest) > 1 else 1
            return build_tool_result(
                build_failure_structured_content(command, output, error, returncode)
            )
