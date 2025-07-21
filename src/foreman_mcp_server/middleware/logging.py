import logging

from fastmcp.server.middleware import Middleware, MiddlewareContext


class LoggingMiddleware(Middleware):
    """Middleware that logs all MCP operations."""

    def __init__(
        self,
    ):
        self.logger = logging.getLogger("foreman_mcp_server")

    async def on_message(self, context: MiddlewareContext, call_next):
        if context.fastmcp_context:
            try:
                if context.source == "client":
                    self._log_client_info(context.fastmcp_context)
            except Exception:
                pass
        return await call_next(context)

    def _log_client_info(self, fastmcp_context):
        self.logger.debug(
            f"  Client host: {fastmcp_context.request_context.request.client.host}:{fastmcp_context.request_context.request.client.port}"
        )
        self.logger.debug(
            f"  Client headers: {self._sanitize_headers(fastmcp_context.request_context.request.headers)}"
        )
        self.logger.debug(f"  Client ID: {fastmcp_context.client_id}")
        self.logger.debug(
            f"  Client params: {fastmcp_context.request_context.session.client_params}"
        )

    def _sanitize_headers(self, headers):
        """Sanitize headers to avoid logging sensitive information."""
        sanitized_headers = {}
        for key, value in headers.items():
            if key.lower() in [
                "foreman_password",
                "foreman_token",
                "password",
                "token",
            ]:
                sanitized_headers[key] = "******"
            else:
                sanitized_headers[key] = value
        return sanitized_headers
