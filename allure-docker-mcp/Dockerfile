FROM python:3.12-slim

LABEL org.opencontainers.image.title="allure-docker-mcp" \
      org.opencontainers.image.description="MCP server for Allure Docker Service" \
      org.opencontainers.image.source="https://github.com/fescobar/allure-docker-service"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ALLURE_ENDPOINT=http://localhost:5050 \
    ALLURE_MCP_TRANSPORT=streamable-http \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8000

WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY allure_docker_mcp ./allure_docker_mcp

RUN pip install --no-cache-dir .

# Run as an unprivileged user.
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

ENTRYPOINT ["allure-docker-mcp"]
