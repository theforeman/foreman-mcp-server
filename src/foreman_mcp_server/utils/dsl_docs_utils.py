import json
from pathlib import Path
from typing import Any

import aiofiles


def resolve_default(param: dict[str, Any]) -> str:
    """Resolves default values for parameters."""

    def_value = param.get("default")

    if def_value is None:
        return "nil"
    elif isinstance(def_value, dict):
        return "{}"
    elif isinstance(def_value, str):
        if def_value == "":
            return '""'
        return f'"{def_value}"'
    else:
        return str(def_value)


def method_returns(method: dict[str, Any]) -> str:
    """Generates return description for a method."""

    returns_info = method.get("returns", {})
    ret_object = returns_info.get("object", {})

    # Handle Hash return object with nested description (TODO: add support for Hash return object)
    if ret_object.get("class") == "Hash" and isinstance(ret_object.get("data"), list):
        return "Object"

    ret_meta = ret_object.get("meta", "").replace("_", " ").capitalize()
    ret_data = json.dumps(ret_object.get("data")).replace("null", "nil")
    returns = ret_object.get("class") if ret_object.get("data") is None else ret_data

    return f"{ret_meta}: {returns}"


def _process_optional_param(param: dict[str, Any]) -> str:
    """Process optional parameter for method signature."""

    param_name = param.get("name", "")

    if param.get("expected_type") == "list":
        return f"*{param_name}"
    else:
        default_val = resolve_default(param)
        return f"{param_name} = {default_val}"


def _process_keyword_param(param: dict[str, Any]) -> str:
    """Process keyword parameter for method signature."""

    param_name = param.get("name", "")
    default_val = resolve_default(param)

    return f"{param_name}: {default_val}"


def method_signature(method: dict[str, Any]) -> str:
    """Generates a method signature string based on the method definition."""

    params = method.get("params", [])
    if not params:
        return method["name"]

    processed_params = []

    for param in params:
        param_type = param.get("type")
        param_name = param.get("name", "")

        if param_type == "required":
            # Does not need special processing, just append the name
            processed_params.append(param_name)
        elif param_type == "optional":
            param_str = _process_optional_param(param)
            processed_params.append(param_str)
        elif param_type == "keyword":
            param_str = _process_keyword_param(param)
            processed_params.append(param_str)

    param_string = ", ".join(processed_params)

    block_param = next((p for p in params if p.get("type") == "block"), None)

    # Build signature parts
    parts = [method["name"]]
    if processed_params:
        parts.append(f"({param_string})")
    if block_param:
        parts.append(f" {block_param.get('schema', '')}")

    return "".join(parts)


def _format_method_documentation(
    method: dict[str, Any], is_property: bool = False
) -> list[str]:
    """Format a single method or property for documentation."""

    lines = []

    signature = method_signature(method)
    description = method.get("short_description", "No description available")
    returns = method_returns(method)

    lines.append(f"- `{signature}` - {description}")
    lines.append(f"  - Returns: {returns}")

    if is_property:
        lines.append(f"  - Usage: obj.{signature}")
    else:
        lines.append(f"  - Usage: {signature}")

    examples = method.get("examples", [])
    if examples:
        lines.append("  - Examples:")
        for example in examples:
            example_desc = example.get("desc", "")
            example_code = example.get("example", "")
            if example_desc:
                lines.append(f"    - {example_desc}")
            if example_code:
                lines.append("      ```erb")
                lines.append(f"      {example_code}")
                lines.append("      ```")

    lines.append("")  # Empty line
    return lines


def _format_class_documentation(
    class_name: str, class_desc: dict[str, Any]
) -> list[str]:
    """Format a single class and its methods/properties for documentation."""

    lines = [f"### {class_name}"]

    methods = class_desc.get("methods", [])
    if methods:
        lines.append("**Methods:**")
        for method in methods:
            lines.extend(_format_method_documentation(method, False))

    properties = class_desc.get("properties", [])
    if properties:
        lines.append("**Properties:**")
        for prop in properties:
            lines.extend(_format_method_documentation(prop, True))

    lines.append("")  # Empty line between classes
    return lines


# Based on https://github.com/theforeman/foreman/blob/develop/webpack/assets/javascripts/react_app/components/Editor/EditorHelpers.js#L93
def parse_dsl_docs(cache_content: str) -> str:
    """
    Parses DSL documentation JSON and returns a formatted Markdown string.
    """

    header = "# Foreman DSL Documentation"
    if not cache_content:
        return f"{header}\n\nNo documentation available."

    output_lines = [header, "", "## ERB Templates"]

    # These are not part of the DSL documentation
    erb_templates = [
        ("<% code %>", "Executes code, but does not insert a value"),
        ("<%= expression %>", "Inserts the value of an expression"),
        (
            "<% code -%>",
            "Executes code, but does not insert a value, trims the following line break",
        ),
        (
            "<%= expression -%>",
            "Inserts the value of an expression, trims the following line break",
        ),
        (
            "<%# comment -%>",
            "Comment, removed from the final output, trims the following line break",
        ),
    ]

    for snippet, description in erb_templates:
        output_lines.append(f"- `{snippet}` - {description}")

    output_lines.extend(["", "## DSL Macros", ""])

    try:
        cache_data = json.loads(cache_content)
        classes = cache_data.get("docs", {}).get("classes", {})

        for class_name, class_desc in classes.items():
            output_lines.extend(_format_class_documentation(class_name, class_desc))

    except (json.JSONDecodeError, KeyError) as e:
        output_lines.extend(["", f"Error parsing documentation: {str(e)}", ""])

    return "\n".join(output_lines)


def get_dsldocs_path(cache_dir, cache_file) -> str:
    """Returns the path to the DSL documentation cache file."""

    dsldoc_cache_dir = Path(cache_dir) / "dsldoc"
    if not dsldoc_cache_dir.exists():
        dsldoc_cache_dir.mkdir(parents=True, exist_ok=True)

    return str(dsldoc_cache_dir / cache_file)


async def save_dsl_docs_as_markdown(cache_dir, cache_file, docs) -> None:
    """Saves the DSL documentation as formatted Markdown."""

    try:
        # Convert JSON docs to Markdown format
        markdown_content = parse_dsl_docs(json.dumps(docs))

        async with aiofiles.open(get_dsldocs_path(cache_dir, cache_file), "w") as file:
            await file.write(markdown_content)
    except Exception as e:
        raise RuntimeError(f"Failed to save DSL documentation: {str(e)}") from e


async def read_dsl_docs_from_markdown(cache_dir, cache_file) -> str:
    """Reads the DSL documentation from a Markdown file."""

    dsldoc_cache_file = get_dsldocs_path(cache_dir, cache_file)
    try:
        async with aiofiles.open(dsldoc_cache_file) as file:
            return await file.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"DSL documentation file '{dsldoc_cache_file}' not found."
        ) from None
    except Exception as e:
        raise RuntimeError(f"Failed to read DSL documentation: {str(e)}") from e
