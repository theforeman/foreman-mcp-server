import logging

import apypie
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext


class AuthMiddleware(Middleware):
    def __init__(
        self, foreman_url: str, verify_ssl: bool, foreman_api: apypie.ForemanApi | None
    ):
        self.foreman_url = foreman_url
        self.verify_ssl = verify_ssl
        self.foreman_api = foreman_api
        self.logger = logging.getLogger("foreman_mcp_server")

    async def on_request(self, context: MiddlewareContext, call_next):
        if context.fastmcp_context:
            foreman_api = self.foreman_api or self.get_foreman_api_from_request()
            if foreman_api:
                # Store in _request_state so it is inherited by the tool's context.
                # call_tool() creates a fresh Context for tool execution but child
                # contexts inherit _request_state from their parent.
                context.fastmcp_context._request_state["foreman_api"] = foreman_api

        return await call_next(context)

    def get_foreman_api_from_request(self) -> apypie.ForemanApi | None:
        try:
            request = get_http_request()
        except RuntimeError:
            self.logger.debug("No HTTP context available (stdio transport)")
            return None
        foreman_username = request.headers.get("foreman_username")
        foreman_token = request.headers.get("foreman_token")
        if not foreman_username or not foreman_token:
            raise RuntimeError(
                "Foreman username and token must be provided in headers."
            )
        return apypie.ForemanApi(
            uri=self.foreman_url,
            username=foreman_username,
            password=foreman_token,
            verify_ssl=self.verify_ssl,
        )
