# TODO: Improve documentation of the method
# TODO: Imports might be used elsewhere, consider refactoring

def register_call_foreman_api(mcp, foreman_api):
  @mcp.tool
  def call_foreman_api(resource: str, action: str, params: dict) -> str:
    """Call an action on a Foreman API resource. Needs Foreman API resource to be available."""
    try:
      response = foreman_api.call(resource, action, params)
      return f"Action '{action}' on resource '{resource}' executed successfully. Response: {response}"
    except Exception as e:
      return f"Failed to execute action '{action}' on resource '{resource}': {str(e)}"
