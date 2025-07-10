import json
from typing import Any

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent


def to_markdown_like(key: str, value: Any) -> str:
    """Convert a key-value pair to markdown-like format."""
    if isinstance(value, dict | list):
        value = f"```json\n{json.dumps(value, indent=2)}\n```"
    return f"# {key.capitalize()}\n{value}\n"


def derive_legacy_content(structured_content: dict) -> str:
    """Convert structured content dictionary to markdown-like string."""
    parts = [to_markdown_like(key, value) for key, value in structured_content.items()]
    return "\n".join(parts)


def build_tool_result(structured_content: dict) -> ToolResult:
    """Build a ToolResult with both structured content and derived text content."""
    content = derive_legacy_content(structured_content)
    return ToolResult(
        content=[TextContent(type="text", text=content)],
        structured_content=structured_content,
    )
