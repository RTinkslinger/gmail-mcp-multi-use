"""Sandbox mode for testing without real Google credentials.

This module provides mock implementations for development and testing:
- Mock OAuth flow that simulates Google authentication
- Mock Gmail API responses with sample data
- Configurable via GMAIL_MCP_SANDBOX=true environment variable

Example:
    # Enable sandbox mode via environment
    export GMAIL_MCP_SANDBOX=true

    # Or programmatically
    from gmail_multi_user.sandbox import enable_sandbox_mode
    enable_sandbox_mode()
"""

from gmail_multi_user.sandbox.mode import (
    SandboxConfig,
    disable_sandbox_mode,
    enable_sandbox_mode,
    get_sandbox_config,
    is_sandbox_mode,
)
from gmail_multi_user.sandbox.mock_gmail import MockGmailAPIClient
from gmail_multi_user.sandbox.mock_oauth import MockGoogleOAuthClient

__all__ = [
    "SandboxConfig",
    "disable_sandbox_mode",
    "enable_sandbox_mode",
    "get_sandbox_config",
    "is_sandbox_mode",
    "MockGmailAPIClient",
    "MockGoogleOAuthClient",
]
