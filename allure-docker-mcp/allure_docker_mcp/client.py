"""HTTP client for the Allure Docker Service REST API.

Wraps the REST API exposed by ``allure-docker-api`` (Flask). When the service is
started with ``SECURITY_ENABLED=1`` it protects every endpoint with a JWT stored
in cookies and enforces CSRF protection on mutating requests
(``JWT_COOKIE_CSRF_PROTECT=True``). This client transparently handles that flow:

* ``POST /login`` exchanges username/password for the ``access_token_cookie`` and
  ``csrf_access_token`` cookies, which are persisted in a single ``httpx.Client``
  cookie jar.
* For mutating methods (POST/PUT/PATCH/DELETE) the value of the
  ``csrf_access_token`` cookie is echoed back in the ``X-CSRF-TOKEN`` header,
  exactly as Flask-JWT-Extended expects.
* A single retry is performed on ``401`` responses (expired access token) by
  re-authenticating before the request is replayed.

When the service runs without security (the default), no login is attempted and
no CSRF header is sent.
"""

from __future__ import annotations

import base64
import threading
from typing import Any, Optional

import httpx

# Methods Flask-JWT-Extended subjects to CSRF protection by default
# (JWT_CSRF_METHODS). GET/HEAD/OPTIONS are exempt.
_CSRF_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Cookie set by the service on login; its value must be echoed in X-CSRF-TOKEN.
_CSRF_COOKIE_NAME = "csrf_access_token"


class AllureAPIError(RuntimeError):
    """Raised when the Allure Docker Service API returns an error response.

    The service returns a JSON body shaped like ``{"meta_data": {"message": ...}}``
    for errors; that message is surfaced here so the caller (and an LLM driving
    the MCP tool) gets an actionable explanation rather than a bare status code.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Allure API error {status_code}: {message}")


class AllureClient:
    """Thin, synchronous wrapper around the Allure Docker Service REST API."""

    def __init__(
        self,
        endpoint: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        ssl_verify: bool = True,
        timeout: float = 30.0,
    ) -> None:
        if not endpoint:
            raise ValueError("endpoint is required")
        self.endpoint = endpoint.rstrip("/")
        self.username = username or None
        self.password = password or None
        self._client = httpx.Client(
            verify=ssl_verify,
            timeout=timeout,
            follow_redirects=True,
        )
        self._logged_in = False
        # Tools run in worker threads (see server._tool), so guard the lazy
        # login / re-login against concurrent callers sharing this client.
        self._auth_lock = threading.Lock()

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AllureClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- auth --------------------------------------------------------------

    @property
    def security_enabled(self) -> bool:
        """True when credentials were supplied, i.e. the target uses security mode."""
        return bool(self.username and self.password)

    def login(self) -> None:
        """Authenticate and persist the JWT/CSRF cookies in the client cookie jar."""
        if not self.security_enabled:
            return
        resp = self._client.post(
            self._url("/login"),
            json={"username": self.username, "password": self.password},
        )
        self._raise_for_error(resp)
        self._logged_in = True

    def _ensure_auth(self) -> None:
        if not self.security_enabled or self._logged_in:
            return
        with self._auth_lock:
            if not self._logged_in:
                self.login()

    def _relogin(self) -> None:
        """Force a fresh login (e.g. after a 401), serialized across threads."""
        with self._auth_lock:
            self._logged_in = False
            self.login()

    def _csrf_header(self) -> dict[str, str]:
        token = self._client.cookies.get(_CSRF_COOKIE_NAME)
        return {"X-CSRF-TOKEN": token} if token else {}

    # -- request plumbing --------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.endpoint}/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
        follow_redirects: bool = True,
    ) -> httpx.Response:
        """Send a request, applying auth + CSRF and retrying once on 401.

        Set ``follow_redirects=False`` for endpoints (e.g. ``/latest-report``)
        whose useful payload is the ``Location`` header of a 3xx response rather
        than the redirected page body.
        """
        self._ensure_auth()
        url = self._url(path)
        params = {k: v for k, v in (params or {}).items() if v is not None}
        needs_csrf = method.upper() in _CSRF_METHODS

        # At most two attempts: the second only happens on a 401 in security mode,
        # where the access token has likely expired and we re-authenticate.
        for attempt in range(2):
            resp = self._client.request(
                method,
                url,
                params=params,
                json=json,
                headers=self._csrf_header() if needs_csrf else {},
                follow_redirects=follow_redirects,
            )
            if resp.status_code != 401 or not self.security_enabled or attempt == 1:
                break
            self._relogin()

        self._raise_for_error(resp)
        return resp

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> Any:
        """Send a request and return the parsed JSON body.

        Raises :class:`AllureAPIError` if the body is not JSON. The most common
        cause is ``ALLURE_ENDPOINT`` pointing at the web UI instead of the API
        base URL — the UI answers most paths with its SPA ``index.html``, which
        would otherwise be returned silently as opaque text.
        """
        resp = self.request(method, path, params=params, json=json)
        try:
            return resp.json()
        except ValueError:
            ctype = resp.headers.get("content-type", "") or "a non-JSON body"
            snippet = resp.text[:120].replace("\n", " ").strip()
            raise AllureAPIError(
                resp.status_code,
                f"Expected a JSON response from {path!r} but received {ctype} "
                f"(starts with: {snippet!r}). Verify ALLURE_ENDPOINT points at the "
                "Allure Docker Service API base URL (the 'full_allure_docker_api_url' "
                "value returned by GET /config), not the web UI.",
            )

    # -- error / parsing helpers ------------------------------------------

    @staticmethod
    def _extract_message(resp: httpx.Response) -> str:
        try:
            body = resp.json()
        except ValueError:
            text = resp.text.strip()
            return text or resp.reason_phrase or "unknown error"
        if isinstance(body, dict):
            meta = body.get("meta_data")
            if isinstance(meta, dict) and meta.get("message"):
                return str(meta["message"])
        return resp.reason_phrase or "unknown error"

    def _raise_for_error(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            raise AllureAPIError(resp.status_code, self._extract_message(resp))

    # -- base64 helper -----------------------------------------------------

    @staticmethod
    def encode_file(content: bytes) -> str:
        """Base64-encode raw file bytes for the ``content_base64`` field."""
        return base64.b64encode(content).decode("ascii")
