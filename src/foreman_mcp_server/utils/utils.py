# TODO: Needs refactoring, better error handling or entire removal.

import json


async def api_prompt(get_context) -> str:
    """Checks if the Foreman API is accessible and returns a prompt accordingly."""

    ctx = get_context()
    api_resource = await ctx.read_resource("foreman://api")
    result = json.loads(api_resource[0].content)
    if result.get("status") == "ok":
        return (
            "You have access to the Foreman API accessible through provided tools."
            " Use it to gather the information you need to provide the response."
        )
    else:
        return "Foreman API is not available. Suggest using other methods to gather the required information."


async def dsl_prompt(section, get_context) -> str:
    """Checks if the Foreman DSL documentation is available and returns a prompt accordingly."""

    ctx = get_context()
    dsl_resource = await ctx.read_resource(f"foreman://documentation/dsl/{section}")
    docs = json.loads(dsl_resource[0].content)
    if docs.get("error"):
        return (
            f"Foreman DSL documentation for section '{section}' is not available. Try to fetch it first."
            f" After fetching, re-trigger the prompt to access the documentation or read it in foreman://documentation/dsl/{section} resource."
        )
    else:
        return (
            "You have access to the Foreman DSL documentation. Use it to understand available macros for template writing."
            " The documentation is available in JSON format based on the provided section."
            f" Documentation location for '{section}' section is foreman://documentation/dsl/{section}."
        )
