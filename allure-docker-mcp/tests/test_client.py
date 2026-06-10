"""Tests for the AllureClient HTTP/auth/CSRF behaviour."""

import base64

import httpx
import pytest
import respx

from allure_docker_mcp.client import AllureAPIError, AllureClient

ENDPOINT = "http://allure.test:5050"


def test_url_joins_without_double_slash():
    client = AllureClient(endpoint=ENDPOINT + "/")
    assert client._url("/version") == f"{ENDPOINT}/version"
    assert client._url("version") == f"{ENDPOINT}/version"
    client.close()


@respx.mock
def test_get_request_returns_json():
    route = respx.get(f"{ENDPOINT}/version").mock(
        return_value=httpx.Response(200, json={"data": {"version": "2.27.0"}})
    )
    with AllureClient(endpoint=ENDPOINT) as client:
        body = client.request_json("GET", "/version")
    assert route.called
    assert body["data"]["version"] == "2.27.0"


@respx.mock
def test_get_does_not_send_csrf_header():
    route = respx.get(f"{ENDPOINT}/projects").mock(
        return_value=httpx.Response(200, json={"data": {"projects": {}}})
    )
    with AllureClient(endpoint=ENDPOINT) as client:
        # Pretend a csrf cookie exists; GET must still not send the header.
        client._client.cookies.set("csrf_access_token", "tok", domain="allure.test")
        client.request_json("GET", "/projects")
    assert "X-CSRF-TOKEN" not in route.calls.last.request.headers


@respx.mock
def test_error_message_extracted_from_meta_data():
    respx.post(f"{ENDPOINT}/projects").mock(
        return_value=httpx.Response(
            400, json={"meta_data": {"message": "project_id 'x' is existent"}}
        )
    )
    with AllureClient(endpoint=ENDPOINT) as client:
        with pytest.raises(AllureAPIError) as exc:
            client.request_json("POST", "/projects", json={"id": "x"})
    assert exc.value.status_code == 400
    assert "is existent" in exc.value.message


@respx.mock
def test_security_mode_logs_in_and_sends_csrf_on_post():
    login = respx.post(f"{ENDPOINT}/login").mock(
        return_value=httpx.Response(
            200,
            json={"data": {}},
            headers=[
                ("set-cookie", "access_token_cookie=jwt; Path=/"),
                ("set-cookie", "csrf_access_token=csrf123; Path=/"),
            ],
        )
    )
    send = respx.post(f"{ENDPOINT}/send-results").mock(
        return_value=httpx.Response(200, json={"meta_data": {"message": "ok"}})
    )
    with AllureClient(endpoint=ENDPOINT, username="admin", password="pw") as client:
        assert client.security_enabled is True
        client.request_json(
            "POST",
            "/send-results",
            json={"results": [{"file_name": "a.json", "content_base64": "e30="}]},
        )

    assert login.called
    assert send.called
    assert send.calls.last.request.headers.get("X-CSRF-TOKEN") == "csrf123"


@respx.mock
def test_401_triggers_reauth_and_retry():
    respx.post(f"{ENDPOINT}/login").mock(
        return_value=httpx.Response(
            200,
            json={"data": {}},
            headers=[("set-cookie", "csrf_access_token=fresh; Path=/")],
        )
    )
    route = respx.get(f"{ENDPOINT}/config").mock(
        side_effect=[
            httpx.Response(401, json={"meta_data": {"message": "expired"}}),
            httpx.Response(200, json={"data": {"version": "2.27.0"}}),
        ]
    )
    with AllureClient(endpoint=ENDPOINT, username="admin", password="pw") as client:
        body = client.request_json("GET", "/config")
    assert route.call_count == 2
    assert body["data"]["version"] == "2.27.0"


@respx.mock
def test_html_response_raises_helpful_error():
    # Mis-pointed endpoint (UI SPA) returns HTML; must fail loudly, not silently.
    respx.get(f"{ENDPOINT}/projects").mock(
        return_value=httpx.Response(
            200,
            text="<!doctype html><html><head><title>UI</title></head></html>",
            headers={"content-type": "text/html"},
        )
    )
    with AllureClient(endpoint=ENDPOINT) as client:
        with pytest.raises(AllureAPIError) as exc:
            client.request_json("GET", "/projects")
    assert "ALLURE_ENDPOINT" in exc.value.message
    assert "text/html" in exc.value.message


def test_encode_file_roundtrip():
    raw = b'{"name": "test"}'
    encoded = AllureClient.encode_file(raw)
    assert base64.b64decode(encoded) == raw
