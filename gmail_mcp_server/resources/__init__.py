"""MCP resource definitions for gmail-mcp-server.

This package contains all MCP resources:
- config: Configuration status and schema
- users: User and connection information
- gmail: Gmail labels and profiles
- docs: Embedded documentation
"""

from gmail_mcp_server.resources import config, users, gmail, docs

__all__ = ["config", "users", "gmail", "docs"]
