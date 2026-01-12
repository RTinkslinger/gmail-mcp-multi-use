# System Design

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Component Architecture](#2-component-architecture)
3. [Data Flow Diagrams](#3-data-flow-diagrams)
4. [Deployment Topology](#4-deployment-topology)
5. [Integration Points](#5-integration-points)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           gmail-multi-user-mcp                                   │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                         PUBLIC INTERFACES                                  │ │
│  │                                                                             │ │
│  │   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐   │ │
│  │   │  GmailClient    │    │ AsyncGmailClient│    │    MCP Server       │   │ │
│  │   │  (Sync API)     │    │  (Async API)    │    │    (Tools/Res)      │   │ │
│  │   └────────┬────────┘    └────────┬────────┘    └──────────┬──────────┘   │ │
│  │            │                      │                        │              │ │
│  │            └──────────────────────┼────────────────────────┘              │ │
│  │                                   │                                        │ │
│  └───────────────────────────────────┼────────────────────────────────────────┘ │
│                                      │                                          │
│  ┌───────────────────────────────────┼────────────────────────────────────────┐ │
│  │                            CORE LIBRARY                                    │ │
│  │                                   ▼                                        │ │
│  │   ┌─────────────────────────────────────────────────────────────────────┐ │ │
│  │   │                        GmailService                                  │ │ │
│  │   │   (Orchestrates all operations)                                      │ │ │
│  │   └─────────────────────────────────────────────────────────────────────┘ │ │
│  │            │                   │                   │                       │ │
│  │            ▼                   ▼                   ▼                       │ │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐       │ │
│  │   │ OAuthManager │    │ TokenManager │    │    GmailAPIClient    │       │ │
│  │   │              │    │              │    │                      │       │ │
│  │   │ - Auth URLs  │    │ - Encryption │    │ - Search/Read        │       │ │
│  │   │ - Callbacks  │    │ - Refresh    │    │ - Send/Draft         │       │ │
│  │   │ - PKCE       │    │ - Storage    │    │ - Labels/Manage      │       │ │
│  │   └──────────────┘    └──────────────┘    └──────────────────────┘       │ │
│  │            │                   │                   │                       │ │
│  │            └───────────────────┼───────────────────┘                       │ │
│  │                                ▼                                           │ │
│  │   ┌─────────────────────────────────────────────────────────────────────┐ │ │
│  │   │                      ConfigLoader                                    │ │ │
│  │   │   (Env vars → Config file → Home dir)                               │ │ │
│  │   └─────────────────────────────────────────────────────────────────────┘ │ │
│  │                                │                                           │ │
│  └────────────────────────────────┼───────────────────────────────────────────┘ │
│                                   │                                             │
│  ┌────────────────────────────────┼───────────────────────────────────────────┐ │
│  │                         STORAGE LAYER                                      │ │
│  │                                ▼                                           │ │
│  │   ┌─────────────────────────────────────────────────────────────────────┐ │ │
│  │   │                  StorageBackend (Abstract)                           │ │ │
│  │   └─────────────────────────────────────────────────────────────────────┘ │ │
│  │            │                                          │                    │ │
│  │            ▼                                          ▼                    │ │
│  │   ┌──────────────────────┐              ┌──────────────────────────────┐  │ │
│  │   │   SQLiteBackend      │              │     SupabaseBackend          │  │ │
│  │   │   (Local/Dev)        │              │     (Production)             │  │ │
│  │   └──────────────────────┘              └──────────────────────────────┘  │ │
│  │                                                                            │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │                                           │
                    ▼                                           ▼
          ┌──────────────────┐                       ┌──────────────────────┐
          │   Google APIs    │                       │  SQLite / Supabase   │
          │   - OAuth 2.0    │                       │   (External Storage) │
          │   - Gmail API    │                       └──────────────────────┘
          └──────────────────┘
```

### 1.2 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Library-First** | Core logic in library; MCP is thin wrapper |
| **Async-Native** | All I/O async; sync API wraps async |
| **Storage Agnostic** | Abstract interface; SQLite/Supabase implementations |
| **Config Flexibility** | Layered config: env > file > home |
| **Zero-Trust Tokens** | Encrypt at rest; validate on use |

---

## 2. Component Architecture

### 2.1 Core Components

#### 2.1.1 GmailClient / AsyncGmailClient

**Purpose:** Public interface for developers

```python
class GmailClient:
    """Synchronous Gmail client (wraps AsyncGmailClient)."""

    def __init__(self, config: Config | None = None):
        self._async_client = AsyncGmailClient(config)
        self._loop = asyncio.new_event_loop()

    def search(self, connection_id: str, query: str, ...) -> SearchResult:
        return self._loop.run_until_complete(
            self._async_client.search(connection_id, query, ...)
        )

class AsyncGmailClient:
    """Asynchronous Gmail client (native async)."""

    def __init__(self, config: Config | None = None):
        self._config = config or ConfigLoader.load()
        self._service = GmailService(self._config)

    async def search(self, connection_id: str, query: str, ...) -> SearchResult:
        return await self._service.search(connection_id, query, ...)
```

#### 2.1.2 GmailService

**Purpose:** Orchestrates operations, handles cross-cutting concerns

```python
class GmailService:
    """Core orchestration layer."""

    def __init__(self, config: Config):
        self._config = config
        self._storage = StorageFactory.create(config)
        self._oauth = OAuthManager(config)
        self._token_manager = TokenManager(config, self._storage)
        self._gmail_api = GmailAPIClient()

    async def search(self, connection_id: str, query: str, ...) -> SearchResult:
        # 1. Get connection from storage
        connection = await self._storage.get_connection(connection_id)

        # 2. Ensure valid token
        access_token = await self._token_manager.get_valid_token(connection)

        # 3. Call Gmail API
        return await self._gmail_api.search(access_token, query, ...)
```

#### 2.1.3 OAuthManager

**Purpose:** Handle OAuth flow (URL generation, callback processing)

```python
class OAuthManager:
    """OAuth 2.0 flow management with PKCE."""

    async def get_auth_url(self, user_id: str, scopes: list[str], ...) -> AuthUrlResult:
        # Generate PKCE code verifier/challenge
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64url(sha256(code_verifier))

        # Generate state for CSRF
        state = secrets.token_urlsafe(32)

        # Store state for callback validation
        await self._storage.create_oauth_state(state, user_id, scopes, code_verifier, ...)

        # Build Google OAuth URL
        return AuthUrlResult(auth_url=build_url(...), state=state, ...)

    async def handle_callback(self, code: str, state: str) -> CallbackResult:
        # Validate state
        oauth_state = await self._storage.get_oauth_state(state)
        if not oauth_state or oauth_state.is_expired:
            return CallbackResult(success=False, error="Invalid or expired state")

        # Exchange code for tokens
        tokens = await self._exchange_code(code, oauth_state.code_verifier)

        # Store encrypted tokens
        connection = await self._storage.create_connection(
            user_id=oauth_state.user_id,
            gmail_address=tokens.email,
            access_token=self._encrypt(tokens.access_token),
            refresh_token=self._encrypt(tokens.refresh_token),
            ...
        )

        return CallbackResult(success=True, connection_id=connection.id, ...)
```

#### 2.1.4 TokenManager

**Purpose:** Token lifecycle (encryption, refresh, validation)

```python
class TokenManager:
    """Token encryption and refresh management."""

    def __init__(self, config: Config, storage: StorageBackend):
        self._fernet = Fernet(config.encryption_key)
        self._storage = storage

    async def get_valid_token(self, connection: Connection) -> str:
        # Decrypt current access token
        access_token = self._decrypt(connection.access_token_encrypted)

        # Check if refresh needed (within 5 min of expiry)
        if connection.token_expires_at < datetime.utcnow() + timedelta(minutes=5):
            access_token = await self._refresh_token(connection)

        return access_token

    async def _refresh_token(self, connection: Connection) -> str:
        # Decrypt refresh token
        refresh_token = self._decrypt(connection.refresh_token_encrypted)

        # Call Google refresh endpoint
        new_tokens = await self._google_refresh(refresh_token)

        # Store updated tokens
        await self._storage.update_connection_tokens(
            connection.id,
            self._encrypt(new_tokens.access_token),
            new_tokens.expires_at
        )

        return new_tokens.access_token
```

#### 2.1.5 GmailAPIClient

**Purpose:** Gmail API communication

```python
class GmailAPIClient:
    """Gmail API wrapper."""

    async def search(self, access_token: str, query: str, max_results: int) -> list[Message]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"q": query, "maxResults": max_results}
            )
            # Parse and return messages

    async def send(self, access_token: str, message: MIMEMessage) -> SendResult:
        # Encode message as base64
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"raw": raw}
            )
            # Parse and return result
```

### 2.2 MCP Server Components

#### 2.2.1 Server Setup

```python
# gmail_mcp_server/server.py
from fastmcp import FastMCP
from gmail_multi_user import AsyncGmailClient

mcp = FastMCP("gmail-multi-user-mcp")
client = AsyncGmailClient()

@mcp.tool()
async def gmail_search(connection_id: str, query: str, max_results: int = 10) -> dict:
    """Search emails using Gmail query syntax."""
    result = await client.search(connection_id, query, max_results)
    return result.to_dict()

@mcp.resource("config://status")
async def config_status() -> str:
    """Current configuration status."""
    status = await client.check_setup()
    return json.dumps(status)

# ... more tools and resources
```

#### 2.2.2 Local OAuth Server

```python
# gmail_mcp_server/local_oauth.py
class LocalOAuthServer:
    """Temporary HTTP server for OAuth callback in CLI mode."""

    async def run_oauth_flow(self, auth_url: str) -> CallbackResult:
        # 1. Find available port
        port = find_available_port(8000, 9000)

        # 2. Start temporary server
        server = await self._start_server(port)

        # 3. Open browser
        webbrowser.open(auth_url.replace("REDIRECT_PORT", str(port)))

        # 4. Wait for callback (with timeout)
        callback_data = await self._wait_for_callback(timeout=300)

        # 5. Stop server
        await server.shutdown()

        # 6. Process callback
        return await self._process_callback(callback_data)
```

---

## 3. Data Flow Diagrams

### 3.1 OAuth Connection Flow

```
┌──────────┐     ┌──────────────┐     ┌────────────┐     ┌────────────┐
│Developer │     │gmail-multi-  │     │  Google    │     │  Storage   │
│  App     │     │user-mcp      │     │  OAuth     │     │ (SQLite/   │
│          │     │              │     │            │     │ Supabase)  │
└────┬─────┘     └──────┬───────┘     └─────┬──────┘     └─────┬──────┘
     │                  │                   │                  │
     │ 1. get_auth_url  │                   │                  │
     │ (user_id)        │                   │                  │
     ├─────────────────>│                   │                  │
     │                  │                   │                  │
     │                  │ 2. Generate PKCE  │                  │
     │                  │    code_verifier  │                  │
     │                  │    + state        │                  │
     │                  │                   │                  │
     │                  │ 3. Store state ───────────────────────>
     │                  │                   │                  │
     │ 4. auth_url +    │                   │                  │
     │    state         │                   │                  │
     │<─────────────────│                   │                  │
     │                  │                   │                  │
     │ 5. Redirect user to auth_url ─────────>                 │
     │                  │                   │                  │
     │                  │    6. User logs   │                  │
     │                  │       in, consents│                  │
     │                  │                   │                  │
     │ 7. Callback: code + state <───────────                  │
     │                  │                   │                  │
     │ 8. handle_callback                   │                  │
     │    (code, state) │                   │                  │
     ├─────────────────>│                   │                  │
     │                  │                   │                  │
     │                  │ 9. Validate state ─────────────────────>
     │                  │<───────────────────────────────────────
     │                  │                   │                  │
     │                  │ 10. Exchange code ─>                 │
     │                  │     for tokens    │                  │
     │                  │<─────────────────────────────────────│
     │                  │                   │                  │
     │                  │ 11. Encrypt tokens│                  │
     │                  │                   │                  │
     │                  │ 12. Store connection ─────────────────>
     │                  │                   │                  │
     │ 13. connection_id│                   │                  │
     │     gmail_address│                   │                  │
     │<─────────────────│                   │                  │
     │                  │                   │                  │
```

### 3.2 Gmail Operation Flow

```
┌──────────┐     ┌──────────────┐     ┌────────────┐     ┌────────────┐
│Developer │     │gmail-multi-  │     │  Google    │     │  Storage   │
│  App     │     │user-mcp      │     │ Gmail API  │     │            │
└────┬─────┘     └──────┬───────┘     └─────┬──────┘     └─────┬──────┘
     │                  │                   │                  │
     │ 1. search(       │                   │                  │
     │    conn_id,      │                   │                  │
     │    query)        │                   │                  │
     ├─────────────────>│                   │                  │
     │                  │                   │                  │
     │                  │ 2. Get connection ─────────────────────>
     │                  │<───────────────────────────────────────
     │                  │                   │                  │
     │                  │ 3. Decrypt tokens │                  │
     │                  │                   │                  │
     │                  │ 4. Check expiry   │                  │
     │                  │    (refresh if    │                  │
     │                  │     needed)       │                  │
     │                  │                   │                  │
     │                  │ 5. API request ───>                  │
     │                  │    with token     │                  │
     │                  │<─────────────────────────────────────│
     │                  │                   │                  │
     │                  │ 6. Parse response │                  │
     │                  │                   │                  │
     │ 7. SearchResult  │                   │                  │
     │<─────────────────│                   │                  │
     │                  │                   │                  │
```

### 3.3 Token Refresh Flow

```
┌──────────────┐     ┌────────────┐     ┌────────────┐
│TokenManager  │     │  Google    │     │  Storage   │
│              │     │  OAuth     │     │            │
└──────┬───────┘     └─────┬──────┘     └─────┬──────┘
       │                   │                  │
       │ 1. Token expires  │                  │
       │    in < 5 min     │                  │
       │                   │                  │
       │ 2. Decrypt refresh token             │
       │                   │                  │
       │ 3. Refresh request>                  │
       │    (refresh_token)│                  │
       │<──────────────────│                  │
       │ 4. New tokens     │                  │
       │                   │                  │
       │ 5. Encrypt new    │                  │
       │    access_token   │                  │
       │                   │                  │
       │ 6. Update storage ─────────────────────>
       │                   │                  │
       │ 7. Return valid   │                  │
       │    access_token   │                  │
       │                   │                  │
```

---

## 4. Deployment Topology

### 4.1 Local Development (SQLite)

```
┌─────────────────────────────────────────────────────────┐
│                   Developer Machine                      │
│                                                          │
│   ┌─────────────────────────────────────────────────┐   │
│   │              Developer's App                     │   │
│   │                    │                            │   │
│   │                    ▼                            │   │
│   │   ┌────────────────────────────────────────┐   │   │
│   │   │        gmail-multi-user-mcp            │   │   │
│   │   │   (Library or MCP Server on stdio)     │   │   │
│   │   └────────────────────────────────────────┘   │   │
│   │                    │                            │   │
│   │                    ▼                            │   │
│   │   ┌────────────────────────────────────────┐   │   │
│   │   │   gmail_tokens.db (SQLite file)        │   │   │
│   │   └────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │  Google APIs  │
                   │  (Internet)   │
                   └───────────────┘
```

### 4.2 Production (Supabase + Library Import)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Production Environment                          │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                      Application Server(s)                        │  │
│   │                                                                   │  │
│   │   ┌───────────────────┐   ┌───────────────────┐                  │  │
│   │   │   App Instance 1  │   │   App Instance 2  │   ...            │  │
│   │   │                   │   │                   │                  │  │
│   │   │  ┌─────────────┐  │   │  ┌─────────────┐  │                  │  │
│   │   │  │GmailClient  │  │   │  │GmailClient  │  │                  │  │
│   │   │  │(library)    │  │   │  │(library)    │  │                  │  │
│   │   │  └─────────────┘  │   │  └─────────────┘  │                  │  │
│   │   └─────────┬─────────┘   └─────────┬─────────┘                  │  │
│   │             │                       │                            │  │
│   └─────────────┼───────────────────────┼────────────────────────────┘  │
│                 │                       │                               │
│                 └───────────┬───────────┘                               │
│                             │                                           │
│                             ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    Supabase (Managed)                            │  │
│   │                                                                  │  │
│   │   ┌─────────────────┐   ┌─────────────────────────────────┐     │  │
│   │   │   PostgreSQL    │   │  Connection Pooling (PgBouncer) │     │  │
│   │   │   - users       │   │                                 │     │  │
│   │   │   - connections │   │                                 │     │  │
│   │   │   - oauth_states│   │                                 │     │  │
│   │   └─────────────────┘   └─────────────────────────────────┘     │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
                           ┌───────────────┐
                           │  Google APIs  │
                           └───────────────┘
```

### 4.3 Production (Remote MCP Server for Non-Python Apps)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Production Environment                          │
│                                                                          │
│   ┌────────────────────────────────┐   ┌─────────────────────────────┐  │
│   │   TypeScript/Go/Rust App       │   │    MCP Server (Sidecar)     │  │
│   │                                │   │                             │  │
│   │   ┌────────────────────────┐   │   │  ┌─────────────────────┐   │  │
│   │   │   MCP Client           │   │   │  │  gmail-mcp serve    │   │  │
│   │   │   (HTTP transport)     │ ───────> │  --transport http   │   │  │
│   │   └────────────────────────┘   │   │  └─────────────────────┘   │  │
│   │                                │   │            │               │  │
│   └────────────────────────────────┘   │            │               │  │
│                                        │            ▼               │  │
│                                        │  ┌─────────────────────┐   │  │
│                                        │  │   GmailClient       │   │  │
│                                        │  │   (library)         │   │  │
│                                        │  └─────────────────────┘   │  │
│                                        └─────────────┬───────────────┘  │
│                                                      │                  │
│                                                      ▼                  │
│                         ┌────────────────────────────────────────────┐  │
│                         │              Supabase                       │  │
│                         └────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Integration Points

### 5.1 External Dependencies

| Dependency | Purpose | Protocol |
|------------|---------|----------|
| Google OAuth 2.0 | User authentication | HTTPS |
| Gmail API v1 | Email operations | HTTPS (REST) |
| Supabase | Token storage (prod) | HTTPS (REST/WebSocket) |
| SQLite | Token storage (dev) | File I/O |

### 5.2 Internal Interfaces

| Interface | Components | Method |
|-----------|------------|--------|
| Public API | Client → GmailService | Method calls |
| Storage | GmailService → StorageBackend | Abstract interface |
| OAuth | OAuthManager → Storage | Async methods |
| Gmail | GmailAPIClient → Google | HTTP requests |
| MCP | MCP Server → Client | Tool/Resource handlers |

### 5.3 Authentication Boundaries

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   DEVELOPER'S INFRASTRUCTURE                                            │
│   ─────────────────────────────                                         │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    gmail-multi-user-mcp                          │   │
│   │                                                                  │   │
│   │   Auth: None (library) or Bearer token (HTTP MCP)               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│                                │ Service Key                            │
│                                ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                       Supabase                                   │   │
│   │                                                                  │   │
│   │   Auth: Service Role Key (server-to-server)                     │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 │ OAuth 2.0 Tokens
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   GOOGLE'S INFRASTRUCTURE                                               │
│   ───────────────────────────                                           │
│                                                                          │
│   Auth: OAuth 2.0 access tokens (per end-user)                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```
