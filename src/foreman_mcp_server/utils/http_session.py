from http.cookiejar import DefaultCookiePolicy

import requests


def cookieless_session() -> requests.Session:
    """Returns a requests session that never stores cookies.

    Foreman answers a successful API login with a session cookie whose expiry
    it checks before credentials. Once the session has been idle past
    Foreman's idle_timeout, the next request carrying that cookie gets a 401,
    even with valid credentials. Without the cookie, every request
    authenticates with its own credentials.
    """
    session = requests.Session()
    session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
    return session
