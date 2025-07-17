import apypie
from fastmcp.server.middleware import Middleware, MiddlewareContext

class AuthMiddleware(Middleware):
    def __init__(self, foreman_url: str):
        self.foreman_url = foreman_url

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        # Add the foreman_api to the context for use in tools
        if context.fastmcp_context:
            foreman_username = context.fastmcp_context.request_context.request.headers.get("foreman_username")
            foreman_password = context.fastmcp_context.request_context.request.headers.get("foreman_token")
            foreman_api = apypie.ForemanApi(
                uri=self.foreman_url,
                username=foreman_username,
                password=foreman_password,
                verify_ssl=False,
            )
            setattr(context.fastmcp_context, 'foreman_api', foreman_api)

        return await call_next(context)
