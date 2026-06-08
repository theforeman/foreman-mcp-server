import logging
from types import SimpleNamespace

from foreman_mcp_server.middleware.logging import _SAFE_HEADERS, LoggingMiddleware


class TestLogClientInfo:
    def setup_method(self):
        self.middleware = LoggingMiddleware()

    def test_headers_are_sanitized(self, caplog):
        ctx = SimpleNamespace(
            request_context=SimpleNamespace(
                request=SimpleNamespace(
                    client=SimpleNamespace(host="127.0.0.1", port=12345),
                    headers={
                        "host": "foreman.example.com",
                        "foreman_token": "super-secret",
                    },
                ),
                session=SimpleNamespace(client_params={}),
            ),
            client_id="test-client",
        )
        with caplog.at_level(logging.DEBUG, logger="foreman_mcp_server"):
            self.middleware._log_client_info(ctx)

        header_line = next(m for m in caplog.messages if "Client headers" in m)
        assert "foreman.example.com" in header_line
        assert "super-secret" not in header_line
        assert "******" in header_line


class TestSanitizeHeaders:
    def setup_method(self):
        self.middleware = LoggingMiddleware()

    def test_allowed_headers_pass_through(self):
        headers = {
            "host": "foreman.example.com",
            "user-agent": "python/3.12",
            "content-type": "application/json",
        }
        result = self.middleware._sanitize_headers(headers)
        assert result == headers

    def test_sensitive_headers_are_masked(self):
        headers = {
            "foreman_token": "secret-token-123",
            "foreman_username": "admin",
            "authorization": "Bearer abc",
        }
        result = self.middleware._sanitize_headers(headers)
        assert result == {
            "foreman_token": "******",
            "foreman_username": "admin",
            "authorization": "******",
        }

    def test_case_insensitivity(self):
        headers = {
            "Host": "foreman.example.com",
            "CONTENT-TYPE": "application/json",
            "Foreman_Token": "secret",
        }
        result = self.middleware._sanitize_headers(headers)
        assert result["Host"] == "foreman.example.com"
        assert result["CONTENT-TYPE"] == "application/json"
        assert result["Foreman_Token"] == "******"

    def test_empty_headers(self):
        result = self.middleware._sanitize_headers({})
        assert result == {}

    def test_mixed_headers(self):
        headers = {
            "host": "foreman.example.com",
            "content-type": "application/json",
            "foreman_token": "secret-token",
            "foreman_username": "admin",
            "user-agent": "mcp-client/1.0",
        }
        result = self.middleware._sanitize_headers(headers)
        assert result["host"] == "foreman.example.com"
        assert result["content-type"] == "application/json"
        assert result["user-agent"] == "mcp-client/1.0"
        assert result["foreman_token"] == "******"
        assert result["foreman_username"] == "admin"

    def test_unknown_headers_are_masked(self):
        headers = {
            "x-custom-secret": "some-value",
            "x-api-key": "key-123",
            "not-necessarily-a-harmful-thing": "but-not-on-the-allowlist",
        }
        result = self.middleware._sanitize_headers(headers)
        assert result == {
            "x-custom-secret": "******",
            "x-api-key": "******",
            "not-necessarily-a-harmful-thing": "******",
        }

    def test_safe_headers_is_frozenset(self):
        assert isinstance(_SAFE_HEADERS, frozenset)
