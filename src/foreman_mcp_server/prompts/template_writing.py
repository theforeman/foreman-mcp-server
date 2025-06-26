from pydantic import Field

from ..utils.utils import dsl_prompt

def register_template_writing_prompts(mcp, _foreman_api, get_context):
  @mcp.prompt(
    name="Basic Template Writing",
    description="A prompt for writing a basic template in Foreman",
  )
  async def basic_template_writing(
    kind: str = Field(description="The kind of the template to ask for.")
  ) -> str:
    prompt = f"Do you know how to write Foreman templates, such as {kind} templates?"
    return prompt
