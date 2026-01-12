"""Configuration-related MCP resources.

These resources provide configuration status and schema information.
"""

from __future__ import annotations

import json

from gmail_mcp_server.server import mcp


@mcp.resource("config://status")
async def get_config_status() -> str:
    """Get current configuration status and health.

    Returns JSON with:
    - configured: bool
    - config_path: str | null
    - database: {type, connected}
    - google_oauth: {configured}
    - encryption: {key_set}
    - server: {running, transport}
    """
    from gmail_mcp_server.tools.setup import check_setup_impl

    # Reuse the check_setup impl logic directly
    status = await check_setup_impl()

    result = {
        "configured": status["ready"],
        "config_path": status["config_path"],
        "database": {
            "type": status["database_type"],
            "connected": status["database_connected"],
        },
        "google_oauth": {
            "configured": status["google_oauth_configured"],
        },
        "encryption": {
            "key_set": status["encryption_key_set"],
        },
        "server": {
            "running": True,
            "transport": "stdio",  # Will be updated based on actual transport
        },
        "issues": status["issues"],
    }

    return json.dumps(result, indent=2)


@mcp.resource("config://schema")
async def get_config_schema() -> str:
    """Get full configuration schema with documentation.

    Returns YAML schema showing all configuration options.
    """
    schema = """# Gmail Multi-User MCP Configuration Schema
# All fields support environment variable overrides with GMAIL_MCP_ prefix

# Security
encryption_key: str
  # Required: Fernet encryption key for token storage
  # Format: 44-character base64 string or 64-character hex string
  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  # Env: GMAIL_MCP_ENCRYPTION_KEY

# Google OAuth Configuration
google:
  client_id: str
    # Required: Google OAuth 2.0 client ID
    # Get from: https://console.cloud.google.com/apis/credentials
    # Env: GMAIL_MCP_GOOGLE__CLIENT_ID

  client_secret: str
    # Required: Google OAuth 2.0 client secret
    # Env: GMAIL_MCP_GOOGLE__CLIENT_SECRET

  redirect_uri: str = "http://localhost:8000/oauth/callback"
    # OAuth redirect URI - must match Google Console configuration
    # Env: GMAIL_MCP_GOOGLE__REDIRECT_URI

  scopes: list[str]
    # Default scopes to request during OAuth
    # Common scopes:
    #   - https://www.googleapis.com/auth/gmail.readonly
    #   - https://www.googleapis.com/auth/gmail.send
    #   - https://www.googleapis.com/auth/gmail.modify
    #   - https://www.googleapis.com/auth/userinfo.email

# Storage Backend Configuration
storage:
  type: "sqlite" | "supabase"
    # Storage backend type
    # Env: GMAIL_MCP_STORAGE__TYPE

  sqlite:
    path: str = "gmail_mcp.db"
      # Path to SQLite database file
      # Env: GMAIL_MCP_STORAGE__SQLITE__PATH

  supabase:
    url: str
      # Supabase project URL
      # Env: GMAIL_MCP_STORAGE__SUPABASE__URL

    key: str
      # Supabase service role key (not anon key!)
      # Env: GMAIL_MCP_STORAGE__SUPABASE__KEY

# OAuth Settings
oauth_state_ttl_seconds: int = 600
  # OAuth state expiration time (default: 10 minutes)
  # Env: GMAIL_MCP_OAUTH_STATE_TTL_SECONDS

token_refresh_buffer_seconds: int = 300
  # Refresh tokens this many seconds before expiry (default: 5 minutes)
  # Env: GMAIL_MCP_TOKEN_REFRESH_BUFFER_SECONDS
"""
    return schema
