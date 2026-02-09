# TODO: Consider refactoring


from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from foreman_mcp_server.utils.utils import get_foreman_api


def register_foreman_template_resources(mcp):
    @mcp.resource(
        name="Foreman Template Kinds",
        description="Provides a list of all template kinds available in Foreman.",
        uri="foreman://template/kinds",
        mime_type="text/plain",
    )
    async def foreman_template_kinds(ctx: Context = CurrentContext()) -> str:
        try:
            # TODO: Consider saving it in cache. Revisit Resource notification mechanism.
            api = get_foreman_api(ctx)
            response = api.call("template_kinds", "index", {})
            kinds = [res.get("name") for res in response.get("results", [])]
            return ", ".join(kinds)
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.resource(
        name="Foreman Template Models",
        description="Provides a list of all template models available in Foreman.",
        uri="foreman://template/models",
        mime_type="text/plain",
    )
    async def foreman_template_models(ctx: Context = CurrentContext()) -> str:
        try:
            all_resources = await ctx.read_resource(
                "foreman://documentation/api/resources"
            )
            resource_list = all_resources[0].content.split(", ")
            models = (
                item.split("_")[0]
                for item in resource_list
                if item.endswith("_templates")
            )
            return ", ".join(
                {model.capitalize() + "Template" for model in models} - {"OsTemplate"}
            )
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.resource(
        name="Foreman Template Schema",
        description="Returns the schema of a Foreman template.",
        uri="foreman://template/schema",
        mime_type="text/plain",
    )
    def foreman_template_schema() -> str:
        schema = """<%#
kind: string # optional kind of the template, for the list of available kinds refer to foreman://template/kinds
name: string # required name of the template
model: ModelClass # required model of the template, for the list of available models refer to foreman://template/models
oses: list # optional list of operating systems (relevant for provisioning templates only)
description: text # optional description of the template, can be used to explain its inputs
snippet: boolean # optional flag indicating if the template is a snippet
template_inputs: list # optional list of inputs for the template. Any inputs used in the template must be defined here as:
- name: string # required name of the input
  required: boolean # required flag indicating if the input is mandatory
  input_type: string # required type of the input, e.g. user, host, or hostgroup
  description: text # optional description of the input
  advanced: boolean # optional flag indicating if the input is advanced
  value_type: string # required type of the value, e.g. plain, search, or resource
  options: string # optional list of options for the input, separated by \r\n
  default: string # optional default value for the input
  resource_type: string # optional type of the resource for the input, e.g. Host or Hostgroup
-%>
ERB content of the template, which can include limited Ruby code, any of Foreman DSL macros and plain text.
Refer to the Foreman DSL documentation for available macros and syntax at foreman://documentation/dsl/all.
For more information on writing templates, refer to the Foreman documentation at foreman://doumentation/dsl/help
    """
        return schema
