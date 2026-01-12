"""Gmail Multi-User MCP Server.

This package provides an MCP server for multi-user Gmail integration.
It exposes Gmail operations as MCP tools, resources, and prompts.

Usage:
    # Run the server
    gmail-mcp serve

    # Or in Python
    from gmail_mcp_server import mcp
    mcp.run(transport="stdio")
"""

from gmail_mcp_server.server import mcp, state

__version__ = "0.1.0"

__all__ = ["mcp", "state", "__version__"]
