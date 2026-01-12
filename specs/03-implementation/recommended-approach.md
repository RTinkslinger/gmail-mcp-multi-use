# Recommended Implementation Approach

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [Approach Summary](#1-approach-summary)
2. [Core Library Implementation](#2-core-library-implementation)
3. [MCP Server Implementation](#3-mcp-server-implementation)
4. [Sync/Async Strategy](#4-syncasync-strategy)
5. [Configuration System](#5-configuration-system)
6. [Storage Abstraction](#6-storage-abstraction)
7. [Local OAuth Server](#7-local-oauth-server)

---

## 1. Approach Summary

### 1.1 Library-First Architecture

Build the core functionality as a Python library (`gmail_multi_user/`), then wrap it with a thin MCP server layer (`gmail_mcp_server/`).

```
gmail-multi-user-mcp/
│
├── gmail_multi_user/          # Core library (THE VALUE)
│   ├── __init__.py            # Public API exports
│   ├── client.py              # GmailClient, AsyncGmailClient
│   ├── service.py             # GmailService (orchestration)
│   ├── config.py              # Configuration loading
│   ├── types.py               # Data types and result classes
│   ├── exceptions.py          # Custom exceptions
│   │
│   ├── oauth/                 # OAuth 2.0 implementation
│   ├── storage/               # Storage backends
│   ├── gmail/                 # Gmail API wrapper
│   └── tokens/                # Token encryption and refresh
│
└── gmail_mcp_server/          # MCP wrapper (~200 lines)
    ├── __init__.py
    ├── server.py              # FastMCP server with tools
    ├── resources.py           # MCP resources
    ├── prompts.py             # MCP prompts
    └── cli.py                 # CLI commands
```

### 1.2 Key Principles

| Principle | Implementation |
|-----------|----------------|
| **Library owns all logic** | MCP server has no business logic |
| **Async at core** | AsyncGmailClient is native; GmailClient wraps it |
| **Single configuration** | Same config works for library and MCP |
| **Storage is pluggable** | Abstract interface; SQLite/Supabase implementations |

---

## 2. Core Library Implementation

### 2.1 Public API (gmail_multi_user/__init__.py)

```python
"""
gmail-multi-user-mcp: Multi-user Gmail integration library.

Usage:
    from gmail_multi_user import GmailClient

    client = GmailClient()
    messages = client.search(connection_id="conn_123", query="is:unread")
"""

from gmail_multi_user.client import GmailClient, AsyncGmailClient
from gmail_multi_user.config import Config, ConfigLoader
from gmail_multi_user.types import (
    AuthUrlResult,
    CallbackResult,
    Connection,
    ConnectionStatus,
    Message,
    Thread,
    SearchResult,
    SendResult,
    DraftResult,
    Label,
    Attachment,
    AttachmentData,
    AttachmentInput,
    Contact,
)
from gmail_multi_user.exceptions import (
    GmailMCPError,
    ConfigError,
    AuthError,
    TokenError,
    ConnectionError,
    GmailAPIError,
    RateLimitError,
)

__version__ = "1.0.0"

__all__ = [
    # Clients
    "GmailClient",
    "AsyncGmailClient",
    # Config
    "Config",
    "ConfigLoader",
    # Types
    "AuthUrlResult",
    "CallbackResult",
    "Connection",
    "ConnectionStatus",
    "Message",
    "Thread",
    "SearchResult",
    "SendResult",
    "DraftResult",
    "Label",
    "Attachment",
    "AttachmentData",
    "AttachmentInput",
    "Contact",
    # Exceptions
    "GmailMCPError",
    "ConfigError",
    "AuthError",
    "TokenError",
    "ConnectionError",
    "GmailAPIError",
    "RateLimitError",
]
```

### 2.2 Service Layer (gmail_multi_user/service.py)

```python
"""
GmailService: Core orchestration layer.

This is where all the business logic lives. Both GmailClient and
AsyncGmailClient delegate to this service.
"""

from gmail_multi_user.oauth import OAuthManager
from gmail_multi_user.tokens import TokenManager
from gmail_multi_user.gmail import GmailAPIClient
from gmail_multi_user.storage import StorageBackend, StorageFactory


class GmailService:
    """
    Orchestrates Gmail operations.

    Responsibilities:
    - Coordinate OAuth flow
    - Manage token lifecycle
    - Execute Gmail API calls
    - Handle errors consistently
    """

    def __init__(self, config: Config):
        self._config = config
        self._storage = StorageFactory.create(config)
        self._oauth = OAuthManager(config, self._storage)
        self._token_manager = TokenManager(config, self._storage)
        self._gmail = GmailAPIClient()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize storage connection."""
        if not self._initialized:
            await self._storage.initialize()
            self._initialized = True

    async def close(self) -> None:
        """Close storage connection."""
        if self._initialized:
            await self._storage.close()
            self._initialized = False

    # === OAuth Methods ===

    async def get_auth_url(
        self,
        user_id: str,
        scopes: list[str] | None = None,
        redirect_uri: str | None = None,
    ) -> AuthUrlResult:
        """Generate OAuth URL for user authentication."""
        await self.initialize()
        return await self._oauth.get_auth_url(user_id, scopes, redirect_uri)

    async def handle_oauth_callback(
        self,
        code: str,
        state: str,
    ) -> CallbackResult:
        """Process OAuth callback."""
        await self.initialize()
        return await self._oauth.handle_callback(code, state)

    # === Gmail Methods ===

    async def search(
        self,
        connection_id: str,
        query: str,
        max_results: int = 10,
        include_body: bool = False,
        page_token: str | None = None,
    ) -> SearchResult:
        """Search emails."""
        await self.initialize()

        # Get connection and valid token
        connection = await self._storage.get_connection(connection_id)
        if connection is None:
            raise ConnectionError(code="connection_not_found", message="Connection not found")

        access_token = await self._token_manager.get_valid_token(connection)

        # Call Gmail API
        return await self._gmail.search(
            access_token=access_token,
            query=query,
            max_results=max_results,
            include_body=include_body,
            page_token=page_token,
        )

    # ... other methods follow same pattern
```

### 2.3 Client Layer (gmail_multi_user/client.py)

```python
"""
GmailClient and AsyncGmailClient: Public interfaces.
"""

import asyncio
from typing import Literal

from gmail_multi_user.config import Config, ConfigLoader
from gmail_multi_user.service import GmailService
from gmail_multi_user.types import *


class AsyncGmailClient:
    """
    Asynchronous Gmail client.

    Native async implementation for use with asyncio, FastAPI, etc.

    Example:
        async def main():
            client = AsyncGmailClient()
            messages = await client.search(
                connection_id="conn_123",
                query="is:unread"
            )
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize async Gmail client.

        Args:
            config: Optional configuration. If not provided, loads automatically.
        """
        self._config = config or ConfigLoader.load()
        self._service = GmailService(self._config)

    async def __aenter__(self) -> "AsyncGmailClient":
        """Context manager entry."""
        await self._service.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        await self._service.close()

    # === OAuth Methods ===

    async def get_auth_url(
        self,
        user_id: str,
        scopes: list[str] | None = None,
        redirect_uri: str | None = None,
    ) -> AuthUrlResult:
        """Generate OAuth URL for user authentication."""
        return await self._service.get_auth_url(user_id, scopes, redirect_uri)

    async def handle_oauth_callback(
        self,
        code: str,
        state: str,
    ) -> CallbackResult:
        """Process OAuth callback."""
        return await self._service.handle_oauth_callback(code, state)

    # === Gmail Methods ===

    async def search(
        self,
        connection_id: str,
        query: str,
        max_results: int = 10,
        include_body: bool = False,
        page_token: str | None = None,
    ) -> SearchResult:
        """Search emails using Gmail query syntax."""
        return await self._service.search(
            connection_id, query, max_results, include_body, page_token
        )

    # ... other async methods


class GmailClient:
    """
    Synchronous Gmail client.

    Wraps AsyncGmailClient for use in synchronous code.
    Creates its own event loop internally.

    Example:
        client = GmailClient()
        messages = client.search(connection_id="conn_123", query="is:unread")
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize sync Gmail client.

        Args:
            config: Optional configuration. If not provided, loads automatically.
        """
        self._async_client = AsyncGmailClient(config)
        self._loop = asyncio.new_event_loop()

    def __enter__(self) -> "GmailClient":
        """Context manager entry."""
        self._loop.run_until_complete(self._async_client._service.initialize())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self._loop.run_until_complete(self._async_client._service.close())
        self._loop.close()

    def _run(self, coro):
        """Run async coroutine in sync context."""
        return self._loop.run_until_complete(coro)

    # === OAuth Methods ===

    def get_auth_url(
        self,
        user_id: str,
        scopes: list[str] | None = None,
        redirect_uri: str | None = None,
    ) -> AuthUrlResult:
        """Generate OAuth URL for user authentication."""
        return self._run(
            self._async_client.get_auth_url(user_id, scopes, redirect_uri)
        )

    def handle_oauth_callback(self, code: str, state: str) -> CallbackResult:
        """Process OAuth callback."""
        return self._run(self._async_client.handle_oauth_callback(code, state))

    # === Gmail Methods ===

    def search(
        self,
        connection_id: str,
        query: str,
        max_results: int = 10,
        include_body: bool = False,
        page_token: str | None = None,
    ) -> SearchResult:
        """Search emails using Gmail query syntax."""
        return self._run(
            self._async_client.search(
                connection_id, query, max_results, include_body, page_token
            )
        )

    # ... other sync methods (all call self._run with async version)
```

---

## 3. MCP Server Implementation

### 3.1 Server Setup (gmail_mcp_server/server.py)

```python
"""
MCP Server: Thin wrapper around gmail_multi_user library.

This file should remain ~200 lines. All business logic lives in the library.
"""

from fastmcp import FastMCP
from gmail_multi_user import AsyncGmailClient, ConfigLoader

# Initialize
mcp = FastMCP("gmail-multi-user-mcp")
client: AsyncGmailClient | None = None


def get_client() -> AsyncGmailClient:
    """Lazy initialization of client."""
    global client
    if client is None:
        client = AsyncGmailClient()
    return client


# === Setup Tools ===

@mcp.tool()
async def gmail_check_setup() -> dict:
    """Check if gmail-multi-user-mcp is properly configured."""
    try:
        config = ConfigLoader.load()
        return {
            "config_found": True,
            "config_path": str(ConfigLoader.get_config_path()),
            "database_connected": True,  # Would test connection
            "database_type": config.database.type,
            "google_oauth_configured": bool(config.google.client_id),
            "encryption_key_set": bool(config.encryption.key),
            "issues": [],
            "ready": True,
        }
    except Exception as e:
        return {
            "config_found": False,
            "issues": [str(e)],
            "ready": False,
        }


# === OAuth Tools ===

@mcp.tool()
async def gmail_get_auth_url(
    user_id: str,
    scopes: list[str] | None = None,
    redirect_uri: str | None = None,
) -> dict:
    """Generate OAuth URL for user to connect Gmail."""
    result = await get_client().get_auth_url(user_id, scopes, redirect_uri)
    return {
        "auth_url": result.auth_url,
        "state": result.state,
        "expires_in": int((result.expires_at - datetime.utcnow()).total_seconds()),
    }


@mcp.tool()
async def gmail_list_connections(
    user_id: str | None = None,
    include_inactive: bool = False,
) -> dict:
    """List Gmail connections."""
    connections = await get_client().list_connections(user_id, include_inactive)
    return {
        "connections": [
            {
                "id": c.id,
                "user_id": c.user_id,
                "gmail_address": c.gmail_address,
                "scopes": c.scopes,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat(),
                "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
            }
            for c in connections
        ]
    }


# === Gmail Operation Tools ===

@mcp.tool()
async def gmail_search(
    connection_id: str,
    query: str,
    max_results: int = 10,
    include_body: bool = False,
) -> dict:
    """
    Search emails using Gmail query syntax.

    Common queries:
    - is:unread
    - from:alice@example.com
    - subject:invoice
    - has:attachment
    - newer_than:7d
    """
    result = await get_client().search(
        connection_id=connection_id,
        query=query,
        max_results=max_results,
        include_body=include_body,
    )
    return {
        "messages": [msg.to_dict() for msg in result.messages],
        "total_estimate": result.total_estimate,
    }


@mcp.tool()
async def gmail_get_message(
    connection_id: str,
    message_id: str,
    format: str = "full",
) -> dict:
    """Get a single email message with full content."""
    message = await get_client().get_message(
        connection_id=connection_id,
        message_id=message_id,
        format=format,
    )
    return message.to_dict()


@mcp.tool()
async def gmail_send(
    connection_id: str,
    to: list[str],
    subject: str,
    body: str,
    body_html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_message_id: str | None = None,
) -> dict:
    """Send an email."""
    result = await get_client().send(
        connection_id=connection_id,
        to=to,
        subject=subject,
        body=body,
        body_html=body_html,
        cc=cc,
        bcc=bcc,
        reply_to_message_id=reply_to_message_id,
    )
    return {
        "success": result.success,
        "message_id": result.message_id,
        "thread_id": result.thread_id,
    }


# ... additional tools follow same pattern


# === Resources ===

@mcp.resource("config://status")
async def config_status() -> str:
    """Current configuration status."""
    status = await gmail_check_setup()
    return json.dumps(status, indent=2)


@mcp.resource("users://list")
async def users_list() -> str:
    """All users with Gmail connections."""
    # Implementation
    pass


# === Prompts ===

@mcp.prompt()
async def setup_gmail() -> str:
    """Complete setup wizard for gmail-multi-user-mcp."""
    return """
    I'll help you set up gmail-multi-user-mcp. Let's go through this step by step:

    1. First, let me check your current configuration status.
    2. If needed, I'll help you create a config file.
    3. Then we'll set up Google OAuth credentials.
    4. Finally, we'll test the connection.

    Let me start by checking your setup...
    """
```

---

## 4. Sync/Async Strategy

### 4.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                 │
│                                                                     │
│   ┌──────────────────────┐     ┌──────────────────────────────────┐│
│   │    GmailClient       │     │      AsyncGmailClient            ││
│   │    (Sync API)        │     │      (Async API)                 ││
│   │                      │     │                                  ││
│   │  def search(...):    │     │  async def search(...):          ││
│   │    return self._run( │     │    return await self._service... ││
│   │      self._async...  │     │                                  ││
│   │    )                 │     │                                  ││
│   └──────────┬───────────┘     └──────────────────┬───────────────┘│
│              │                                    │                │
│              │                                    │                │
│              └────────────────────────────────────┘                │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Service Layer                                 │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐ │
│   │                     GmailService                              │ │
│   │                     (Always Async)                            │ │
│   │                                                               │ │
│   │  async def search(self, ...):                                 │ │
│   │      connection = await self._storage.get_connection(...)     │ │
│   │      token = await self._token_manager.get_valid_token(...)   │ │
│   │      return await self._gmail.search(...)                     │ │
│   └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Why This Pattern

1. **Core is async**: All I/O operations (storage, Gmail API) are async
2. **Sync wraps async**: GmailClient creates event loop, runs async methods
3. **No code duplication**: Sync API calls same code path as async
4. **Clear usage**: Users choose the API style that fits their code

---

## 5. Configuration System

### 5.1 Loading Priority

```python
class ConfigLoader:
    """Load configuration from multiple sources."""

    @classmethod
    def load(cls) -> Config:
        """
        Load configuration with priority:
        1. Environment variables
        2. File from GMAIL_MCP_CONFIG env var
        3. Project-local files
        4. User home directory
        """
        # Start with empty config
        config_dict = {}

        # 1. Try to load from file
        config_path = cls._find_config_file()
        if config_path:
            config_dict = cls._load_yaml(config_path)

        # 2. Override with environment variables
        config_dict = cls._apply_env_overrides(config_dict)

        # 3. Validate and return
        return Config.from_dict(config_dict)

    @classmethod
    def _find_config_file(cls) -> Path | None:
        """Find config file in priority order."""
        # Check GMAIL_MCP_CONFIG env var
        if env_path := os.environ.get("GMAIL_MCP_CONFIG"):
            path = Path(env_path)
            if path.exists():
                return path

        # Check project-local files
        for filename in ["gmail_config.yaml", "gmail_config.yml", ".gmail_config.yaml"]:
            if Path(filename).exists():
                return Path(filename)

        # Check home directory
        home_path = cls._get_home_config_path()
        if home_path.exists():
            return home_path

        return None
```

---

## 6. Storage Abstraction

### 6.1 Interface

```python
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize connection."""

    @abstractmethod
    async def close(self) -> None:
        """Close connection."""

    # User operations
    @abstractmethod
    async def get_or_create_user(self, external_user_id: str) -> User: ...

    # Connection operations
    @abstractmethod
    async def create_connection(self, ...) -> Connection: ...

    @abstractmethod
    async def get_connection(self, connection_id: str) -> Connection | None: ...

    @abstractmethod
    async def list_connections(self, user_id: str | None = None) -> list[Connection]: ...

    # OAuth state operations
    @abstractmethod
    async def create_oauth_state(self, ...) -> None: ...

    @abstractmethod
    async def get_oauth_state(self, state: str) -> OAuthState | None: ...
```

### 6.2 Factory

```python
class StorageFactory:
    """Create storage backend based on config."""

    @staticmethod
    def create(config: Config) -> StorageBackend:
        if config.database.type == "sqlite":
            return SQLiteBackend(config.database.sqlite_path)
        elif config.database.type == "supabase":
            return SupabaseBackend(
                config.database.supabase_url,
                config.database.supabase_service_key,
            )
        else:
            raise ConfigError(f"Unknown database type: {config.database.type}")
```

---

## 7. Local OAuth Server

### 7.1 Purpose

When using MCP server in stdio mode (Claude Code), users can't easily complete web OAuth flows. The local OAuth server provides a seamless experience.

### 7.2 Implementation

```python
class LocalOAuthServer:
    """
    Temporary HTTP server for OAuth callback in CLI/MCP mode.

    Flow:
    1. Find available port (8000-9000)
    2. Start temporary HTTP server
    3. Open browser to OAuth URL
    4. Wait for callback (up to 5 minutes)
    5. Process callback and return result
    6. Shutdown server
    """

    def __init__(self, client: AsyncGmailClient):
        self._client = client
        self._callback_event = asyncio.Event()
        self._callback_data: dict | None = None

    async def run_oauth_flow(self, user_id: str) -> CallbackResult:
        """Run complete OAuth flow with local server."""
        # 1. Find available port
        port = await self._find_available_port()

        # 2. Generate auth URL with local redirect
        redirect_uri = f"http://localhost:{port}/oauth/callback"
        auth_result = await self._client.get_auth_url(
            user_id=user_id,
            redirect_uri=redirect_uri,
        )

        # 3. Start server
        server = await self._start_server(port)

        try:
            # 4. Open browser
            webbrowser.open(auth_result.auth_url)
            print(f"Opened browser for authentication...")
            print(f"If browser didn't open, visit: {auth_result.auth_url}")

            # 5. Wait for callback
            await asyncio.wait_for(
                self._callback_event.wait(),
                timeout=300,  # 5 minutes
            )

            # 6. Process callback
            if self._callback_data:
                return await self._client.handle_oauth_callback(
                    code=self._callback_data["code"],
                    state=self._callback_data["state"],
                )
            else:
                raise AuthError("OAuth callback not received")

        finally:
            # 7. Shutdown server
            await server.shutdown()

    async def _handle_callback(self, request):
        """Handle OAuth callback request."""
        self._callback_data = {
            "code": request.query_params.get("code"),
            "state": request.query_params.get("state"),
        }
        self._callback_event.set()

        # Return success page
        return HTMLResponse("""
            <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>Gmail Connected!</h1>
                <p>You can close this window and return to Claude Code.</p>
            </body>
            </html>
        """)
```
