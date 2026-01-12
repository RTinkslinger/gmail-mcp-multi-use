"""MCP prompt definitions for gmail-mcp-server.

This package contains all MCP prompts:
- setup: Complete setup wizard
- connect: Connect test Gmail account
- diagnose: Debug failing connections
- generate_ui: Generate OAuth UI components
- build_agent: Scaffold email-capable AI agents
"""

from gmail_mcp_server.prompts import build_agent, connect, diagnose, generate_ui, setup

__all__ = ["setup", "connect", "diagnose", "generate_ui", "build_agent"]
