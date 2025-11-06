import asyncio

from fastmcp.tools.tool import ToolResult

from ..utils.content_utils import build_tool_result


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


def register_hammer_commands(mcp, _foreman_api, _get_context):
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
        process = await asyncio.create_subprocess_exec(
            "hammer",
            *command.split(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        # Decode output
        stdout_text = stdout.decode("utf-8") if stdout else ""
        stderr_text = stderr.decode("utf-8") if stderr else ""

        if process.returncode == 0:
            return build_tool_result(
                build_success_structured_content(
                    command, stdout_text, process.returncode
                )
            )
        else:
            return build_tool_result(
                build_failure_structured_content(
                    command, stdout_text, stderr_text, process.returncode
                )
            )
