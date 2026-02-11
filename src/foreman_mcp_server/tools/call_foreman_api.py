import json
from typing import Any

from fastmcp.tools.tool import ToolResult
from requests.exceptions import HTTPError

from ..utils.content_utils import build_tool_result
from ..utils.utils import (
    assert_http_method,
    assert_resource,
    get_foreman_api,
    mcp_info_headers,
)


def _parse_params(params: str) -> dict:
    """Parse a JSON string into a dict for Foreman API params.

    Also normalises float values to int where appropriate,
    since some MCP clients send integers as floats (e.g. 3.0 instead of 3).
    """
    try:
        parsed = json.loads(params)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(
            f"'params' must be a valid JSON string, got: {params!r}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ValueError(
            f"'params' must be a JSON object (dict), got {type(parsed).__name__}"
        )
    return _normalize_numeric_values(parsed)


def _normalize_numeric_values(obj):
    """Recursively convert float values that are whole numbers to int."""
    if isinstance(obj, dict):
        return {k: _normalize_numeric_values(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_numeric_values(item) for item in obj]
    if isinstance(obj, float) and obj.is_integer():
        return int(obj)
    return obj


# TODO: Probably split it into multiple tools (read-only, destructive, etc)
def register_foreman_api_methods(mcp, foreman_api, get_context):
    @mcp.tool(
        description=(
            "Calls GET action on Foreman API. "
            "The 'params' argument must be a JSON string representing "
            "the request parameters, e.g. "
            '\'{"search": "name ~ test", "per_page": 20}\' or '
            '\'{"id": 1}\'.'
        ),
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
        resource: str, action: str, params: str
    ) -> ToolResult:
        try:
            parsed_params = _parse_params(params)
            api = foreman_api or get_foreman_api(get_context)
            await assert_resource(
                resource,
                {"name": "Resource", "list_name": "resources", "type": "api"},
                get_context,
            )
            assert_http_method(
                api,
                {"name": action, "resource": resource, "params": parsed_params},
                "get",
            )
            response = api.call(
                resource, action, parsed_params, mcp_info_headers(get_context)
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
