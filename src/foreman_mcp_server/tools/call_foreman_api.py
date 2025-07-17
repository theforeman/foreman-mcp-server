import json
from typing import Any

from fastmcp.tools.tool import ToolResult
from requests.exceptions import HTTPError

from ..utils.content_utils import build_tool_result
from ..utils.utils import assert_http_method, assert_resource, mcp_info_headers


# TODO: Probably split it into multiple tools (read-only, destructive, etc)
def register_foreman_api_methods(mcp, foreman_api, get_context):
    @mcp.tool(
        description="Calls GET action on Foreman API.",
        tags=("foreman", "api", "get", "resource", "remote"),
        annotations={
            "title": "Call Foreman API GET Action",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def call_foreman_api_get(
        resource: str, action: str, params: dict
    ) -> ToolResult:
        try:
            ctx = get_context()
            foreman_api = getattr(ctx, 'foreman_api')
            await assert_resource(
                resource,
                {"name": "Resource", "list_name": "resources", "type": "api"},
                get_context,
            )
            assert_http_method(
                foreman_api,
                {"name": action, "resource": resource, "params": params},
                "get",
            )
            response = foreman_api.call(
                resource, action, params, mcp_info_headers(get_context)
            )
            return format_success_response(resource, action, response)
        except Exception as e:
            return format_failure_response(resource, action, e)


def format_success_response(resource: str, action: str, response: str) -> ToolResult:
    structured_content = build_success_structured_content(resource, action, response)
    return build_tool_result(structured_content)


def format_failure_response(
    resource: str, action: str, exception: Exception
) -> ToolResult:
    structured_content = build_failure_structured_content(resource, action, exception)
    return build_tool_result(structured_content)


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
        text = getattr(exception.response, "text", None)
        if text:
            try:
                structured_content["response"] = json.loads(text)
            except json.JSONDecodeError:
                structured_content["response"] = text
    return structured_content
