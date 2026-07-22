"""Tests for the MCP tools, mocking the Allure REST API with respx."""

import base64
import json

import httpx
import pytest
import respx

from allure_docker_mcp import server
from allure_docker_mcp.client import AllureClient

ENDPOINT = "http://allure.test:5050"


def call(tool, *args, **kwargs):
    """Invoke a tool's synchronous core, bypassing the thread-offload wrapper.

    The ``@server._tool`` decorator wraps each tool in an async function that
    runs the body via ``anyio.to_thread``; ``functools.wraps`` exposes the
    original sync function as ``__wrapped__`` so unit tests can drive the logic
    directly without an event loop.
    """
    return tool.__wrapped__(*args, **kwargs)


@pytest.fixture
def client(monkeypatch):
    """Point the server's module-global client at the mocked endpoint."""
    c = AllureClient(endpoint=ENDPOINT)
    monkeypatch.setattr(server, "_client", c)
    yield c
    c.close()


@respx.mock
def test_get_version(client):
    respx.get(f"{ENDPOINT}/version").mock(
        return_value=httpx.Response(200, json={"data": {"version": "2.27.0"}})
    )
    assert call(server.get_version)["data"]["version"] == "2.27.0"


@respx.mock
def test_create_project_posts_id(client):
    route = respx.post(f"{ENDPOINT}/projects").mock(
        return_value=httpx.Response(201, json={"data": {"id": "demo"}})
    )
    result = call(server.create_project, "demo")
    assert result["data"]["id"] == "demo"
    assert json.loads(route.calls.last.request.read()) == {"id": "demo"}


@respx.mock
def test_delete_project_uses_path(client):
    route = respx.delete(f"{ENDPOINT}/projects/demo").mock(
        return_value=httpx.Response(200, json={"meta_data": {"message": "removed"}})
    )
    call(server.delete_project, "demo")
    assert route.called


@respx.mock
def test_get_latest_report_returns_redirect_url(client):
    # The service answers /latest-report with a 302 to the report index.html.
    respx.get(f"{ENDPOINT}/latest-report").mock(
        return_value=httpx.Response(
            302,
            headers={
                "location": "/allure-docker-service/projects/demo/reports/latest/index.html"
            },
        )
    )
    result = call(server.get_latest_report, "demo")
    assert result["report_url"] == (
        f"{ENDPOINT}/allure-docker-service/projects/demo/reports/latest/index.html"
    )


@respx.mock
def test_search_projects_passes_query(client):
    route = respx.get(f"{ENDPOINT}/projects/search").mock(
        return_value=httpx.Response(200, json={"data": {"projects": {}}})
    )
    call(server.search_projects, "dem")
    assert route.calls.last.request.url.params["id"] == "dem"


@respx.mock
def test_generate_report_omits_none_params(client):
    route = respx.get(f"{ENDPOINT}/generate-report").mock(
        return_value=httpx.Response(200, json={"data": {}})
    )
    call(server.generate_report, project_id="demo", execution_name="ci")
    params = route.calls.last.request.url.params
    assert params["project_id"] == "demo"
    assert params["execution_name"] == "ci"
    assert "execution_from" not in params  # None values are dropped


@respx.mock
def test_send_results_wraps_payload(client):
    route = respx.post(f"{ENDPOINT}/send-results").mock(
        return_value=httpx.Response(200, json={"meta_data": {"message": "ok"}})
    )
    results = [{"file_name": "a.json", "content_base64": "e30="}]
    call(server.send_results, results, project_id="demo", force_project_creation=True)
    req = route.calls.last.request
    assert req.url.params["force_project_creation"] == "true"
    assert req.url.params["project_id"] == "demo"
    assert json.loads(req.read())["results"] == results


@respx.mock
def test_send_results_from_directory_encodes_files(client, tmp_path):
    (tmp_path / "result-1.json").write_text('{"a": 1}')
    (tmp_path / "result-2.json").write_bytes(b"\x00\x01\x02")
    (tmp_path / "subdir").mkdir()  # ignored

    captured = {}

    def _capture(request):
        captured["body"] = json.loads(request.read())
        return httpx.Response(200, json={"meta_data": {"message": "ok"}})

    respx.post(f"{ENDPOINT}/send-results").mock(side_effect=_capture)
    call(server.send_results_from_directory, str(tmp_path), project_id="demo")

    sent = {r["file_name"]: r["content_base64"] for r in captured["body"]["results"]}
    assert set(sent) == {"result-1.json", "result-2.json"}
    assert base64.b64decode(sent["result-1.json"]) == b'{"a": 1}'
    assert base64.b64decode(sent["result-2.json"]) == b"\x00\x01\x02"


@respx.mock
def test_send_results_from_directory_skips_symlinks(client, tmp_path):
    # A regular result file plus a symlink pointing at a file OUTSIDE the dir.
    (tmp_path / "result.json").write_text("{}")
    store = tmp_path / "store"
    store.mkdir()
    secret = store / "secret"  # nested dir is not iterated at the top level
    secret.write_text("password")
    link = tmp_path / "leak.json"
    try:
        link.symlink_to(secret)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")

    captured = {}

    def _capture(request):
        captured["body"] = json.loads(request.read())
        return httpx.Response(200, json={"meta_data": {"message": "ok"}})

    respx.post(f"{ENDPOINT}/send-results").mock(side_effect=_capture)
    call(server.send_results_from_directory, str(tmp_path))

    names = {r["file_name"] for r in captured["body"]["results"]}
    assert names == {"result.json"}  # the symlink "leak.json" is excluded


def test_send_results_from_directory_rejects_missing_dir(client):
    with pytest.raises(ValueError, match="Not a directory"):
        call(server.send_results_from_directory, "/no/such/dir")


@respx.mock
def test_export_report_saves_zip(client, tmp_path, monkeypatch):
    monkeypatch.setenv("ALLURE_OUTPUT_DIR", str(tmp_path))
    respx.get(f"{ENDPOINT}/report/export").mock(
        return_value=httpx.Response(
            200, content=b"PK\x03\x04zip", headers={"content-type": "application/zip"}
        )
    )
    result = call(server.export_report, "report.zip", project_id="demo")
    payload = b"PK\x03\x04zip"
    assert (tmp_path / "report.zip").read_bytes() == payload
    assert result["bytes"] == len(payload)
    assert result["content_type"] == "application/zip"


def test_export_report_rejects_path_escape(client, tmp_path, monkeypatch):
    # No respx route: confinement must fail before any HTTP request is made.
    monkeypatch.setenv("ALLURE_OUTPUT_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="escapes"):
        call(server.export_report, "../escape.zip")
    with pytest.raises(ValueError, match="escapes"):
        call(server.export_report, "/etc/cron.d/evil")


def test_export_report_allows_nested_path_in_root(client, tmp_path, monkeypatch):
    monkeypatch.setenv("ALLURE_OUTPUT_DIR", str(tmp_path))
    with respx.mock:
        respx.get(f"{ENDPOINT}/report/export").mock(
            return_value=httpx.Response(200, content=b"zip", headers={"content-type": "application/zip"})
        )
        result = call(server.export_report, "sub/dir/report.zip", project_id="demo")
    assert (tmp_path / "sub" / "dir" / "report.zip").read_bytes() == b"zip"
    assert result["saved_to"].endswith("report.zip")


@respx.mock
def test_render_emailable_report_returns_html(client):
    respx.get(f"{ENDPOINT}/emailable-report/render").mock(
        return_value=httpx.Response(200, text="<html>report</html>")
    )
    assert call(server.render_emailable_report, "demo") == "<html>report</html>"


def test_configure_transport_applies_fastmcp_host_port(monkeypatch):
    # Guards the regression where FASTMCP_* env vars were silently ignored and
    # the HTTP server never bound to the requested host/port.
    orig = (server.mcp.settings.host, server.mcp.settings.port)
    monkeypatch.setenv("ALLURE_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("FASTMCP_HOST", "0.0.0.0")
    monkeypatch.setenv("FASTMCP_PORT", "8123")
    try:
        transport = server._configure_transport()
        assert transport == "streamable-http"
        assert server.mcp.settings.host == "0.0.0.0"
        assert server.mcp.settings.port == 8123
    finally:
        server.mcp.settings.host, server.mcp.settings.port = orig


def test_configure_transport_defaults_to_stdio(monkeypatch):
    monkeypatch.delenv("ALLURE_MCP_TRANSPORT", raising=False)
    assert server._configure_transport() == "stdio"
