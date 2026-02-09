import apypie
from fastmcp.server.middleware import Middleware, MiddlewareContext


class AuthMiddleware(Middleware):
    def __init__(
        self, foreman_url: str, verify_ssl: bool, foreman_api: apypie.ForemanApi | None
    ):
        # TODO: user_map can grow indefinitely, consider using a more efficient structure or cleanup mechanism
        self.user_map = {}
        self.foreman_url = foreman_url
        self.verify_ssl = verify_ssl
        self.foreman_api = foreman_api

    async def on_request(self, context: MiddlewareContext, call_next):
        if context.fastmcp_context:
            foreman_api = self.foreman_api or self.get_foreman_api_from_request(context)
            if foreman_api:
                context.fastmcp_context.foreman_api = foreman_api

        return await call_next(context)

    def get_foreman_api_from_request(
        self, context: MiddlewareContext
    ) -> apypie.ForemanApi | None:
        # Add the foreman_api to the context for use in tools
        if context.fastmcp_context and context.fastmcp_context.request_context:
            foreman_username = (
                context.fastmcp_context.request_context.request.headers.get(
                    "foreman_username"
                )
            )
            foreman_token = context.fastmcp_context.request_context.request.headers.get(
                "foreman_token"
            )
            if not foreman_username or not foreman_token:
                raise RuntimeError(
                    "Foreman username and token must be provided in headers."
                )
            session_id = context.fastmcp_context.request_context.request.headers.get(
                "mcp-session-id"
            )
            if session_id not in self.user_map.get(foreman_username, {}):
                # Reset foreman_api for the user keeping the same credentials for the same session
                foreman_api = apypie.ForemanApi(
                    uri=self.foreman_url,
                    username=foreman_username,
                    password=foreman_token,
                    verify_ssl=self.verify_ssl,
                )
                self.user_map[foreman_username] = {}
                self.user_map[foreman_username][session_id] = foreman_api

            return self.user_map[foreman_username][session_id]
