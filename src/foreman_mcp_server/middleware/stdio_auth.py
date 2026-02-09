from apypie import ForemanApi
from fastmcp.server.middleware import Middleware, MiddlewareContext


class StdioAuthMiddleware(Middleware):
    """Middleware that injects a pre-created ForemanApi instance into the context for stdio transport.

    This middleware provides a unified way to access the ForemanApi instance
    across both stdio and streamable-http transports. For stdio, the API is
    created once at startup with credentials from CLI args/env vars.
    """

    def __init__(self, foreman_api: ForemanApi):
        self.foreman_api = foreman_api

    async def on_request(self, context: MiddlewareContext, call_next):
        if context.fastmcp_context:
            context.fastmcp_context.foreman_api = self.foreman_api

        return await call_next(context)
