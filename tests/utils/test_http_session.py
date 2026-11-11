import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
import requests

from foreman_mcp_server.utils.http_session import cookieless_session


class SessionCookieHandler(BaseHTTPRequestHandler):
    received_cookie_headers: list[str | None] = []

    def do_GET(self):
        SessionCookieHandler.received_cookie_headers.append(self.headers.get("Cookie"))
        self.send_response(200)
        self.send_header("Set-Cookie", "_session_id=abc123; path=/; HttpOnly")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture
def server_url():
    SessionCookieHandler.received_cookie_headers = []
    server = HTTPServer(("127.0.0.1", 0), SessionCookieHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/api/status"
    server.shutdown()
    server.server_close()


def cookie_headers_over_two_requests(session: requests.Session, url: str) -> list:
    session.get(url)
    session.get(url)
    return SessionCookieHandler.received_cookie_headers


class TestCookielessSession:
    def test_default_session_sends_back_session_cookie(self, server_url):
        assert cookie_headers_over_two_requests(requests.Session(), server_url) == [
            None,
            "_session_id=abc123",
        ]

    def test_does_not_send_back_session_cookie(self, server_url):
        assert cookie_headers_over_two_requests(cookieless_session(), server_url) == [
            None,
            None,
        ]
