"""MCP tool definitions for gmail-mcp-server.

This package contains all MCP tools organized by category:
- setup: Configuration and diagnostic tools
- auth: OAuth and user management tools
- read: Gmail read operations
- write: Gmail write operations (send, drafts)
- manage: Label management, archive, trash
"""

from gmail_mcp_server.tools import auth, manage, read, setup, write

__all__ = ["setup", "auth", "read", "write", "manage"]
