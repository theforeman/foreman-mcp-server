import asyncio

from fastmcp.tools.tool import ToolResult

from ..utils.content_utils import build_tool_result


def lifecycle_environment_create(
    organization_name: str,
    lifecycle_environment_name: str,
    prior_lifecycle_environment_name: str,
) -> str:
    """Build hammer command for creating a lifecycle environment (without 'hammer' prefix)."""
    return f'lifecycle-environment create --organization "{organization_name}" --name "{lifecycle_environment_name}" --prior "{prior_lifecycle_environment_name}" --description "Created by Foreman MCP Server"'


def lifecycle_environment_delete(
    organization_name: str, lifecycle_environment_name: str
) -> str:
    """Build hammer command for deleting a lifecycle environment (without 'hammer' prefix)."""
    return f'lifecycle-environment delete --organization "{organization_name}" --name "{lifecycle_environment_name}"'


async def execute_hammer_command_for_tool(command: str) -> ToolResult:
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
            build_success_structured_content(command, stdout_text, process.returncode)
        )
    else:
        return build_tool_result(
            build_failure_structured_content(
                command, stdout_text, stderr_text, process.returncode
            )
        )


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


def register_hammer_commands(mcp):
    """Register hammer CLI command execution tools."""

    @mcp.tool(
        description="Execute a hammer CLI command with any arguments and return its output. A leading 'hammer' is NOT required in the command.",
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

    @mcp.tool(
        description="Create a new lifecycle environment in Foreman. Requires organization name, "
        "new lifecycle environment name, and the name of the prior lifecycle environment.",
        tags=("hammer", "lifecycle-environment", "create", "destructive"),
        annotations={
            "title": "Execute Hammer CLI Lifecycle Environment Create",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def execute_hammer_lifecycle_environment_create(
        organization_name: str,
        lifecycle_environment_name: str,
        prior_lifecycle_environment_name: str = "Library",
    ) -> ToolResult:
        command = lifecycle_environment_create(
            organization_name,
            lifecycle_environment_name,
            prior_lifecycle_environment_name,
        )
        return await execute_hammer_command_for_tool(command)

    @mcp.tool(
        description="Delete a lifecycle environment in Foreman. Requires organization name and lifecycle environment name.",
        tags=("hammer", "lifecycle-environment", "delete", "destructive"),
        annotations={
            "title": "Execute Hammer CLI Lifecycle Environment Delete",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def execute_hammer_lifecycle_environment_delete(
        organization_name: str, lifecycle_environment_name: str
    ) -> ToolResult:
        command = lifecycle_environment_delete(
            organization_name, lifecycle_environment_name
        )
        return await execute_hammer_command_for_tool(command)
