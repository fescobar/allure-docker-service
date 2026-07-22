"""MCP server exposing the Allure Docker Service REST API as tools.

The server wraps a running `allure-docker-service` instance so that an LLM agent
(via the Model Context Protocol) can manage projects, send test results, generate
and export Allure reports, and inspect service state.

Configuration is read from environment variables:

* ``ALLURE_ENDPOINT``    Base URL of the service. Default ``http://localhost:5050``.
                         If the service is exposed under a path prefix, include it,
                         e.g. ``http://host:5050/allure-docker-service`` (the
                         ``full_allure_docker_api_url`` value from ``GET /config``).
* ``ALLURE_USERNAME``    Username for security mode (optional).
* ``ALLURE_PASSWORD``    Password for security mode (optional).
* ``ALLURE_SSL_VERIFY``  ``false`` to disable TLS verification. Default ``true``.
* ``ALLURE_TIMEOUT``     Per-request timeout in seconds. Default ``30``.
* ``ALLURE_OUTPUT_DIR``  Directory the export tools may write into. Default
                         ``allure-exports`` (relative to the working directory).
                         Exports are confined to this directory.

Run with the ``stdio`` (default), ``streamable-http``, or ``sse`` transport,
selected via ``ALLURE_MCP_TRANSPORT`` — see ``main`` / the README.
"""

from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Any, Callable, Optional

import anyio
from mcp.server.fastmcp import FastMCP

from .client import AllureAPIError, AllureClient

__all__ = ["mcp", "build_client", "main"]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def build_client() -> AllureClient:
    """Construct an :class:`AllureClient` from environment configuration."""
    timeout_raw = os.environ.get("ALLURE_TIMEOUT", "30")
    try:
        timeout = float(timeout_raw)
    except ValueError:
        timeout = 30.0
    return AllureClient(
        endpoint=os.environ.get("ALLURE_ENDPOINT", "http://localhost:5050"),
        username=os.environ.get("ALLURE_USERNAME"),
        password=os.environ.get("ALLURE_PASSWORD"),
        ssl_verify=_env_bool("ALLURE_SSL_VERIFY", True),
        timeout=timeout,
    )


def _output_root() -> Path:
    """Directory the export tools are confined to (``ALLURE_OUTPUT_DIR``)."""
    return Path(os.environ.get("ALLURE_OUTPUT_DIR", "allure-exports")).expanduser().resolve()


mcp = FastMCP(
    "Allure Docker Service",
    instructions=(
        "Tools for managing Allure test reports through a running "
        "allure-docker-service instance: create/list/delete projects, send "
        "results, generate and export reports, and inspect service state. "
        "When a tool takes 'project_id' and you omit it, the service uses the "
        "'default' project."
    ),
)

# A single long-lived client so the auth/CSRF cookie jar persists across calls.
_client: Optional[AllureClient] = None


def _get_client() -> AllureClient:
    global _client
    if _client is None:
        _client = build_client()
    return _client


def _tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Register ``fn`` as an MCP tool, offloading its (blocking) body to a thread.

    FastMCP calls a synchronous tool inline on the asyncio event loop, so the
    blocking httpx/disk work in these tools would stall every other request
    under the ``streamable-http``/``sse`` transports. Wrapping the body in
    ``anyio.to_thread.run_sync`` keeps the loop responsive; ``functools.wraps``
    preserves the signature/docstring FastMCP introspects to build the schema.
    """

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await anyio.to_thread.run_sync(functools.partial(fn, *args, **kwargs))

    return mcp.tool()(wrapper)


# --------------------------------------------------------------------------
# Service info
# --------------------------------------------------------------------------


@_tool
def get_version() -> dict[str, Any]:
    """Return the Allure version used by the service."""
    return _get_client().request_json("GET", "/version")


@_tool
def get_config() -> dict[str, Any]:
    """Return the service configuration (check timing, security mode, etc.)."""
    return _get_client().request_json("GET", "/config")


# --------------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------------


@_tool
def list_projects() -> dict[str, Any]:
    """List all existing projects and the URIs to inspect each one."""
    return _get_client().request_json("GET", "/projects")


@_tool
def get_project(project_id: str) -> dict[str, Any]:
    """Get a single project, including the list of available reports.

    Args:
        project_id: Identifier of the project to fetch.
    """
    return _get_client().request_json("GET", f"/projects/{project_id}")


@_tool
def search_projects(query: str) -> dict[str, Any]:
    """Search for projects whose id matches the given query string.

    Args:
        query: Substring to match against project ids.
    """
    return _get_client().request_json("GET", "/projects/search", params={"id": query})


@_tool
def create_project(project_id: str) -> dict[str, Any]:
    """Create a new project.

    Args:
        project_id: New project id. Must be lowercase alphanumeric characters or
            hyphens (e.g. ``my-project-id``), max 100 chars, and not ``default``.
    """
    return _get_client().request_json("POST", "/projects", json={"id": project_id})


@_tool
def delete_project(project_id: str) -> dict[str, Any]:
    """Delete an existing project and all of its results/reports.

    Args:
        project_id: Identifier of the project to delete. The ``default`` project
            cannot be removed. Requires admin privileges in security mode.
    """
    return _get_client().request_json("DELETE", f"/projects/{project_id}")


# --------------------------------------------------------------------------
# Results & reports
# --------------------------------------------------------------------------


def _send_results(
    results: list[dict[str, str]],
    project_id: Optional[str],
    force_project_creation: bool,
) -> dict[str, Any]:
    """Shared POST /send-results call used by both send_results tools."""
    params = {
        "project_id": project_id,
        "force_project_creation": "true" if force_project_creation else None,
    }
    return _get_client().request_json(
        "POST", "/send-results", params=params, json={"results": results}
    )


@_tool
def send_results(
    results: list[dict[str, str]],
    project_id: Optional[str] = None,
    force_project_creation: bool = False,
) -> dict[str, Any]:
    """Send Allure result files (already base64-encoded) to a project.

    Args:
        results: List of result files. Each item must be
            ``{"file_name": "<name>", "content_base64": "<base64 content>"}``.
            File names must be unique within the request.
        project_id: Target project. Omit to use the ``default`` project.
        force_project_creation: When True, create the project if it does not exist.

    Returns:
        On success, the service summary of processed files (omitted when the
        service runs with ``API_RESPONSE_LESS_VERBOSE=1``). A file that fails to
        process makes the service return an error instead of a partial-success body.
    """
    return _send_results(results, project_id, force_project_creation)


@_tool
def send_results_from_directory(
    directory: str,
    project_id: Optional[str] = None,
    force_project_creation: bool = False,
) -> dict[str, Any]:
    """Read every file in a local directory, base64-encode it, and send as results.

    A convenience wrapper over :func:`send_results` for the common case of having
    an ``allure-results`` directory on disk. Every top-level regular file is
    uploaded to ``ALLURE_ENDPOINT``; symlinks are skipped so the tool cannot be
    pointed at a symlink that resolves to sensitive files outside the directory.

    Args:
        directory: Path to a local directory containing Allure result files.
        project_id: Target project. Omit to use the ``default`` project.
        force_project_creation: When True, create the project if it does not exist.
    """
    base = Path(directory).expanduser()
    if not base.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    results = [
        {
            "file_name": entry.name,
            "content_base64": AllureClient.encode_file(entry.read_bytes()),
        }
        for entry in sorted(base.iterdir())
        if entry.is_file() and not entry.is_symlink()
    ]
    if not results:
        raise ValueError(f"No regular files found in directory: {directory}")

    return _send_results(results, project_id, force_project_creation)


@_tool
def generate_report(
    project_id: Optional[str] = None,
    execution_name: Optional[str] = None,
    execution_from: Optional[str] = None,
    execution_type: Optional[str] = None,
) -> dict[str, Any]:
    """Generate a new Allure report from the project's current results.

    Args:
        project_id: Target project. Omit to use the ``default`` project.
        execution_name: Label shown for this execution in the report (e.g. a CI job name).
        execution_from: Link back to the source of the execution (e.g. a build URL).
        execution_type: Type of the execution source (e.g. ``github``, ``jenkins``).
    """
    params = {
        "project_id": project_id,
        "execution_name": execution_name,
        "execution_from": execution_from,
        "execution_type": execution_type,
    }
    return _get_client().request_json("GET", "/generate-report", params=params)


@_tool
def get_latest_report(project_id: Optional[str] = None) -> dict[str, Any]:
    """Get the URL of the latest generated report for a project.

    The service answers this endpoint with a redirect to the report's
    ``index.html``; this tool returns that target URL instead of following it.

    Args:
        project_id: Target project. Omit to use the ``default`` project.

    Returns:
        ``{"report_url": "<absolute url to the latest report>"}``.
    """
    resp = _get_client().request(
        "GET",
        "/latest-report",
        params={"project_id": project_id},
        follow_redirects=False,
    )
    # The endpoint answers with a 302 whose Location is the report; if there is
    # no redirect (older/edge cases) fall back to the final URL we landed on.
    location = resp.headers.get("location")
    report_url = str(resp.request.url.join(location)) if location else str(resp.url)
    return {"report_url": report_url}


@_tool
def clean_results(project_id: Optional[str] = None) -> dict[str, Any]:
    """Delete all pending results for a project (does not touch generated reports).

    Args:
        project_id: Target project. Omit to use the ``default`` project.
    """
    return _get_client().request_json(
        "GET", "/clean-results", params={"project_id": project_id}
    )


@_tool
def clean_history(project_id: Optional[str] = None) -> dict[str, Any]:
    """Delete the history and trends of a project's reports.

    Args:
        project_id: Target project. Omit to use the ``default`` project.
    """
    return _get_client().request_json(
        "GET", "/clean-history", params={"project_id": project_id}
    )


# --------------------------------------------------------------------------
# Exports (file-returning endpoints saved to local disk)
# --------------------------------------------------------------------------


def _resolve_output(output_path: str) -> Path:
    """Resolve ``output_path`` inside the export root, rejecting any escape.

    ``output_path`` is interpreted relative to ``ALLURE_OUTPUT_DIR``. Absolute
    paths and ``..`` segments that would land outside that root are refused, so
    a tool call cannot overwrite arbitrary files on the host.
    """
    root = _output_root()
    candidate = (root / output_path).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(
            f"Refusing to write outside the export root {root}: {output_path!r} "
            "escapes it. Pass a path inside the root, or set ALLURE_OUTPUT_DIR."
        )
    return candidate


def _download_to(output_path: str, api_path: str, project_id: Optional[str]) -> dict[str, Any]:
    out = _resolve_output(output_path)
    resp = _get_client().request("GET", api_path, params={"project_id": project_id})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(resp.content)
    return {
        "saved_to": str(out),
        "bytes": len(resp.content),
        "content_type": resp.headers.get("content-type", "application/octet-stream"),
    }


@_tool
def export_report(output_path: str, project_id: Optional[str] = None) -> dict[str, Any]:
    """Export the full Allure report as a ZIP archive saved to a local path.

    Args:
        output_path: Destination for the ``.zip`` archive, relative to
            ``ALLURE_OUTPUT_DIR`` (default ``allure-exports``). Paths that escape
            that directory are rejected.
        project_id: Target project. Omit to use the ``default`` project.

    Returns:
        Where the file was saved, its size in bytes, and the content type.
    """
    return _download_to(output_path, "/report/export", project_id)


@_tool
def export_emailable_report(
    output_path: str, project_id: Optional[str] = None
) -> dict[str, Any]:
    """Export the single-file emailable HTML report to a local path.

    Args:
        output_path: Destination for the ``.html`` report, relative to
            ``ALLURE_OUTPUT_DIR`` (default ``allure-exports``). Paths that escape
            that directory are rejected.
        project_id: Target project. Omit to use the ``default`` project.
    """
    return _download_to(output_path, "/emailable-report/export", project_id)


@_tool
def render_emailable_report(project_id: Optional[str] = None) -> str:
    """Render the emailable HTML report and return it as a string.

    Args:
        project_id: Target project. Omit to use the ``default`` project.

    Returns:
        The rendered HTML document.
    """
    resp = _get_client().request(
        "GET", "/emailable-report/render", params={"project_id": project_id}
    )
    return resp.text


def _configure_transport() -> str:
    """Resolve the transport and, for HTTP transports, apply the bind settings.

    FastMCP passes its own host/port defaults into ``Settings``, which take
    precedence over the ``FASTMCP_*`` env vars (pydantic-settings ranks explicit
    init kwargs above the environment). So the env vars are otherwise ignored;
    apply them explicitly here, before ``run`` reads ``mcp.settings``, so the HTTP
    transports actually bind where the operator asked.
    """
    transport = os.environ.get("ALLURE_MCP_TRANSPORT", "stdio").strip().lower()
    if transport != "stdio":
        host = os.environ.get("FASTMCP_HOST")
        port = os.environ.get("FASTMCP_PORT")
        if host:
            mcp.settings.host = host
        if port:
            mcp.settings.port = int(port)
    return transport


def main() -> None:
    """Entry point: run the MCP server over the configured transport."""
    mcp.run(transport=_configure_transport())  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
