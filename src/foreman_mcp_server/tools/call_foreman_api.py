from typing import Any

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from requests.exceptions import HTTPError

from ..utils.utils import assert_resource


# TODO: Probably split it into multiple tools (read-only, destructive, etc)
def register_call_foreman_api(mcp, foreman_api, get_context):
    @mcp.tool(
        description="Calls an action on a Foreman API resource.",
        tags=("foreman", "api", "action", "resource", "remote"),
        annotations={
            "title": "Call Foreman API Action",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def call_foreman_api(resource: str, action: str, params: dict) -> ToolResult:
        try:
            await assert_resource(
                resource,
                {"name": "Resource", "list_name": "resources", "type": "api"},
                get_context,
            )
            response = foreman_api.call(resource, action, params)
            return format_success_response(resource, action, response)
        except Exception as e:
            return format_failure_response(resource, action, e)


def format_success_response(resource: str, action: str, response: str) -> ToolResult:
    structured_content = build_success_structured_content(resource, action, response)
    content = derive_legacy_content(structured_content)
    return ToolResult(
        content=[TextContent(type="text", text=content)],
        structured_content=structured_content,
    )


def format_failure_response(
    resource: str, action: str, exception: Exception
) -> ToolResult:
    structured_content = build_failure_structured_content(resource, action, exception)
    content = derive_legacy_content(structured_content)
    return ToolResult(
        content=[TextContent(type="text", text=content)],
        structured_content=structured_content,
    )


def build_success_structured_content(resource: str, action: str, response: Any) -> dict:
    return {
        "message": f"Action '{action}' on resource '{resource}' executed successfully.",
        "response": response,
    }


def build_failure_structured_content(
    resource: str, action: str, exception: Exception
) -> dict:
    message = f"Failed to execute action '{action}' on resource '{resource}'"
    structured_content = {
        "message": message,
        "error": str(exception),
    }
    if isinstance(exception, HTTPError):
        structured_content["response"] = exception.response.text
    return structured_content


def derive_legacy_content(structured_content: dict) -> str:
    parts = [
        f"# {key.capitalize()}\n{value}\n" for key, value in structured_content.items()
    ]
    return "\n".join(parts)
