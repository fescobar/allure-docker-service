"""MCP (Model Context Protocol) server for Allure Docker Service."""

from .client import AllureAPIError, AllureClient
from .server import build_client, main, mcp

__version__ = "1.0.0"

__all__ = ["AllureAPIError", "AllureClient", "build_client", "main", "mcp", "__version__"]
