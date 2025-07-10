from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.utilities.logging import get_logger


class LoggingMiddleware(Middleware):
    """Middleware that logs all MCP operations."""

    def __init__(
        self,
    ):
        self.logger = get_logger("foreman_mcp_server")

    async def on_message(self, context: MiddlewareContext, call_next):
        if context.fastmcp_context:
            try:
                self.logger.debug(
                    f"[{context.type}] [{context.fastmcp_context.request_id}] from [{context.source}] - [{context.method}]"
                )
                match context.method:
                    case "tools/call":
                        self.logger.debug(
                            f"  Tool: {context.message.name}"
                            f"  Args: {context.message.arguments}"
                        )
                    case "resources/read":
                        self.logger.debug(f"  Resource: {context.message.uri}")
                    case "prompts/get":
                        self.logger.debug(
                            ""
                            f"  Prompt: {context.message.name}"
                            f"  Args: {context.message.arguments}"
                        )
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
            f"  Client headers: {fastmcp_context.request_context.request.headers}"
        )
        self.logger.debug(f"  Client ID: {fastmcp_context.client_id}")
        self.logger.debug(
            f"  Client params: {fastmcp_context.request_context.session.client_params}"
        )
