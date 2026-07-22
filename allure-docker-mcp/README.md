# Allure Docker Service — MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that
exposes a running [`allure-docker-service`](https://github.com/fescobar/allure-docker-service)
instance as tools an LLM agent can call. Manage projects, send test results,
generate and export [Allure](https://allurereport.org/) reports, and inspect
service state — all through natural-language driven tool calls in MCP-compatible
clients such as Claude Desktop, Claude Code, or any MCP host.

This server is a **client** of the Allure Docker Service REST API — it does not
replace it. Run `allure-docker-service` as usual, then point this MCP server at it.

## Features

The server wraps the full REST API. Each tool maps to one endpoint:

| Tool | Endpoint | Description |
| --- | --- | --- |
| `get_version` | `GET /version` | Allure version used by the service |
| `get_config` | `GET /config` | Service configuration |
| `list_projects` | `GET /projects` | List all projects |
| `get_project` | `GET /projects/{id}` | Get a project and its reports |
| `search_projects` | `GET /projects/search` | Search projects by id |
| `create_project` | `POST /projects` | Create a new project |
| `delete_project` | `DELETE /projects/{id}` | Delete a project |
| `send_results` | `POST /send-results` | Send base64-encoded result files |
| `send_results_from_directory` | `POST /send-results` | Encode + send a local results directory |
| `generate_report` | `GET /generate-report` | Generate a report from current results |
| `get_latest_report` | `GET /latest-report` | URL of the latest report |
| `clean_results` | `GET /clean-results` | Delete pending results |
| `clean_history` | `GET /clean-history` | Delete history & trends |
| `export_report` | `GET /report/export` | Export full report as a ZIP to disk |
| `export_emailable_report` | `GET /emailable-report/export` | Export emailable HTML to disk |
| `render_emailable_report` | `GET /emailable-report/render` | Return emailable HTML as a string |

It also transparently handles the service's optional **security mode**
(`SECURITY_ENABLED=1`): it logs in, persists the JWT cookies, and echoes the
`csrf_access_token` cookie in the `X-CSRF-TOKEN` header on mutating requests.

## Installation

Requires Python 3.10+.

```bash
cd allure-docker-mcp
pip install .
# or, for development (adds pytest + respx):
pip install -e ".[dev]"
```

This installs an `allure-docker-mcp` console script.

## Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Default | Description |
| --- | --- | --- |
| `ALLURE_ENDPOINT` | `http://localhost:5050` | Base URL of the **API**. Include any path prefix — use the `full_allure_docker_api_url` value reported by `GET /config`, not the web UI root. |
| `ALLURE_USERNAME` | — | Username (only for security mode) |
| `ALLURE_PASSWORD` | — | Password (only for security mode) |
| `ALLURE_SSL_VERIFY` | `true` | Set `false` to skip TLS verification |
| `ALLURE_TIMEOUT` | `30` | Per-request timeout (seconds) |
| `ALLURE_OUTPUT_DIR` | `allure-exports` | Directory the export tools may write into. Exports are confined here; paths that escape it are rejected. |
| `ALLURE_MCP_TRANSPORT` | `stdio` | `stdio`, `streamable-http`, or `sse` |
| `FASTMCP_HOST` | `127.0.0.1` | Bind address for the HTTP transports |
| `FASTMCP_PORT` | `8000` | Bind port for the HTTP transports |

> **Tip:** point `ALLURE_ENDPOINT` at the API base, not the UI. Many deployments
> serve a web UI at the root and the API under a prefix (e.g. `…/allure-api/allure-docker-service`).
> If a tool returns an "Expected a JSON response … not the web UI" error, fetch
> `GET /config` and use its `full_allure_docker_api_url`.

## Usage

### Claude Desktop / Claude Code (stdio)

Add to your MCP client config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "allure": {
      "command": "allure-docker-mcp",
      "env": {
        "ALLURE_ENDPOINT": "http://localhost:5050"
      }
    }
  }
}
```

Or run the module directly without installing the script:

```bash
ALLURE_ENDPOINT=http://localhost:5050 python -m allure_docker_mcp
```

### Streamable HTTP

```bash
ALLURE_MCP_TRANSPORT=streamable-http \
FASTMCP_HOST=0.0.0.0 FASTMCP_PORT=8000 \
allure-docker-mcp
```

### Docker

A prebuilt image is published to Docker Hub as
[`frankescobar/allure-docker-mcp`](https://hub.docker.com/r/frankescobar/allure-docker-mcp)
(`:latest` for tagged releases, `:edge` from `master`):

```bash
docker run --rm -p 8000:8000 \
  -e ALLURE_ENDPOINT=http://host.docker.internal:5050 \
  frankescobar/allure-docker-mcp
```

Or build it locally:

```bash
docker build -t allure-docker-mcp ./allure-docker-mcp
docker run --rm -p 8000:8000 \
  -e ALLURE_ENDPOINT=http://host.docker.internal:5050 \
  allure-docker-mcp
```

The image defaults to the `streamable-http` transport on port `8000`.

### Security note for the HTTP transports

The `streamable-http` and `sse` transports are **unauthenticated** — anyone who
can reach the port can invoke every tool, including the file-touching ones
(`send_results_from_directory` reads local files; `export_*` write into
`ALLURE_OUTPUT_DIR`). Bind to `127.0.0.1` for local use, and only expose the
port behind an authenticating reverse proxy or a network policy. For untrusted
or desktop use, prefer the `stdio` transport, which has no network surface.

## Scope

Every REST endpoint has a corresponding tool **except** `GET /projects/{id}/reports/{path}`,
which streams individual report artifacts (HTML/JSON files). Raw artifact
retrieval is intentionally out of scope — use `get_project` / `get_latest_report`
to obtain report URLs, or `export_report` to download a full report archive.

## Example interactions

> "Create a project called `regression-suite`, then send the results from
> `./allure-results` and generate a report."

The agent calls `create_project("regression-suite")`,
`send_results_from_directory("./allure-results", project_id="regression-suite")`,
then `generate_report(project_id="regression-suite")` and reports the
`get_latest_report` URL.

## Development

```bash
pip install -e ".[dev]"
pytest
```

The tests mock the REST API with [`respx`](https://lundberg.github.io/respx/) — no
running `allure-docker-service` instance is required.

## License

Apache-2.0, same as the parent project.
