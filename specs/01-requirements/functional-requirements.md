# Functional Requirements

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [Library API Requirements](#1-library-api-requirements)
2. [MCP Tools Requirements](#2-mcp-tools-requirements)
3. [MCP Resources Requirements](#3-mcp-resources-requirements)
4. [MCP Prompts Requirements](#4-mcp-prompts-requirements)
5. [CLI Commands Requirements](#5-cli-commands-requirements)
6. [Configuration Requirements](#6-configuration-requirements)
7. [Storage Backend Requirements](#7-storage-backend-requirements)

---

## 1. Library API Requirements

### 1.1 Client Initialization

#### FR-LIB-001: Dual API Support
The library SHALL provide both synchronous and asynchronous client interfaces.

```python
# Synchronous API
from gmail_multi_user import GmailClient
client = GmailClient()

# Asynchronous API
from gmail_multi_user import AsyncGmailClient
client = AsyncGmailClient()
```

#### FR-LIB-002: Auto-Configuration Loading
The client SHALL automatically load configuration from the following sources (in priority order):
1. Environment variables (`GMAIL_MCP_*`)
2. File path from `GMAIL_MCP_CONFIG` environment variable
3. Project-local files: `./gmail_config.yaml`, `./gmail_config.yml`, `./.gmail_config.yaml`
4. User home directory (OS-specific)

#### FR-LIB-003: Explicit Configuration
The client SHALL accept explicit configuration via constructor parameter.

```python
from gmail_multi_user import GmailClient, Config

config = Config(
    database_type="sqlite",
    sqlite_path="./tokens.db",
    google_client_id="...",
    google_client_secret="...",
    encryption_key="..."
)
client = GmailClient(config=config)
```

### 1.2 OAuth Operations

#### FR-LIB-010: Generate OAuth URL
```python
def get_auth_url(
    self,
    user_id: str,
    scopes: list[str] | None = None,  # Default: ["gmail.readonly", "gmail.send"]
    redirect_uri: str | None = None,   # Override config default
    state: str | None = None           # Custom state (auto-generated if None)
) -> AuthUrlResult:
    """
    Returns:
        AuthUrlResult with:
        - auth_url: str (URL to redirect user to)
        - state: str (CSRF protection token)
        - expires_at: datetime (when this URL expires)
    """
```

#### FR-LIB-011: Handle OAuth Callback
```python
def handle_oauth_callback(
    self,
    code: str,
    state: str
) -> CallbackResult:
    """
    Exchanges authorization code for tokens and stores them.

    Returns:
        CallbackResult with:
        - success: bool
        - connection_id: str | None
        - user_id: str | None
        - gmail_address: str | None
        - error: str | None
    """
```

#### FR-LIB-012: List User Connections
```python
def list_connections(
    self,
    user_id: str | None = None,      # Filter by user, or all if None
    include_inactive: bool = False    # Include revoked/expired
) -> list[Connection]:
    """
    Returns list of Connection objects with:
    - id: str
    - user_id: str
    - gmail_address: str
    - scopes: list[str]
    - is_active: bool
    - created_at: datetime
    - last_used_at: datetime | None
    """
```

#### FR-LIB-013: Check Connection Health
```python
def check_connection(
    self,
    connection_id: str
) -> ConnectionStatus:
    """
    Returns ConnectionStatus with:
    - valid: bool
    - gmail_address: str
    - scopes: list[str]
    - token_expires_in: int | None (seconds)
    - needs_reauth: bool
    - error: str | None
    """
```

#### FR-LIB-014: Disconnect Account
```python
def disconnect(
    self,
    connection_id: str,
    revoke_google_access: bool = True  # Also revoke at Google
) -> DisconnectResult:
    """
    Revokes access and deletes stored tokens.

    Returns:
        DisconnectResult with:
        - success: bool
        - gmail_address: str
    """
```

### 1.3 Gmail Read Operations

#### FR-LIB-020: Search Messages
```python
def search(
    self,
    connection_id: str,
    query: str,                    # Gmail search syntax
    max_results: int = 10,         # 1-100
    include_body: bool = False,    # Include full body (slower)
    page_token: str | None = None  # Pagination
) -> SearchResult:
    """
    Returns SearchResult with:
    - messages: list[Message]
    - next_page_token: str | None
    - total_estimate: int
    """
```

#### FR-LIB-021: Get Single Message
```python
def get_message(
    self,
    connection_id: str,
    message_id: str,
    format: Literal["full", "metadata", "minimal"] = "full"
) -> Message:
    """
    Returns Message with:
    - id: str
    - thread_id: str
    - subject: str
    - from_: Contact (name, email)
    - to: list[Contact]
    - cc: list[Contact]
    - bcc: list[Contact]
    - date: datetime
    - body_plain: str
    - body_html: str | None
    - labels: list[str]
    - attachments: list[Attachment]
    - headers: dict[str, str]
    """
```

#### FR-LIB-022: Get Thread
```python
def get_thread(
    self,
    connection_id: str,
    thread_id: str
) -> Thread:
    """
    Returns Thread with:
    - id: str
    - subject: str
    - message_count: int
    - messages: list[Message]
    """
```

#### FR-LIB-023: List Labels
```python
def list_labels(
    self,
    connection_id: str
) -> list[Label]:
    """
    Returns list of Label with:
    - id: str
    - name: str
    - type: Literal["system", "user"]
    - message_count: int | None
    - unread_count: int | None
    """
```

#### FR-LIB-024: Get Attachment
```python
def get_attachment(
    self,
    connection_id: str,
    message_id: str,
    attachment_id: str
) -> AttachmentData:
    """
    Returns AttachmentData with:
    - filename: str
    - mime_type: str
    - size: int
    - data: bytes
    """
```

### 1.4 Gmail Write Operations

#### FR-LIB-030: Send Email
```python
def send(
    self,
    connection_id: str,
    to: list[str],
    subject: str,
    body: str,
    body_html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_message_id: str | None = None,  # For threading
    attachments: list[AttachmentInput] | None = None
) -> SendResult:
    """
    Returns SendResult with:
    - success: bool
    - message_id: str
    - thread_id: str
    """
```

#### FR-LIB-031: Create Draft
```python
def create_draft(
    self,
    connection_id: str,
    to: list[str],
    subject: str,
    body: str,
    body_html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_message_id: str | None = None
) -> DraftResult:
    """
    Returns DraftResult with:
    - draft_id: str
    - message_id: str
    """
```

#### FR-LIB-032: Update Draft
```python
def update_draft(
    self,
    connection_id: str,
    draft_id: str,
    to: list[str] | None = None,
    subject: str | None = None,
    body: str | None = None,
    body_html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None
) -> DraftResult
```

#### FR-LIB-033: Send Draft
```python
def send_draft(
    self,
    connection_id: str,
    draft_id: str
) -> SendResult
```

#### FR-LIB-034: Delete Draft
```python
def delete_draft(
    self,
    connection_id: str,
    draft_id: str
) -> bool
```

### 1.5 Gmail Management Operations

#### FR-LIB-040: Modify Labels
```python
def modify_labels(
    self,
    connection_id: str,
    message_id: str,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None
) -> list[str]:  # Returns current labels
```

#### FR-LIB-041: Archive Message
```python
def archive(
    self,
    connection_id: str,
    message_id: str
) -> bool
```

#### FR-LIB-042: Trash Message
```python
def trash(
    self,
    connection_id: str,
    message_id: str
) -> bool
```

#### FR-LIB-043: Untrash Message
```python
def untrash(
    self,
    connection_id: str,
    message_id: str
) -> bool
```

#### FR-LIB-044: Mark as Read
```python
def mark_read(
    self,
    connection_id: str,
    message_ids: list[str]
) -> bool
```

#### FR-LIB-045: Mark as Unread
```python
def mark_unread(
    self,
    connection_id: str,
    message_ids: list[str]
) -> bool
```

### 1.6 Batch Operations

#### FR-LIB-050: Batch Get Messages
```python
def batch_get_messages(
    self,
    connection_id: str,
    message_ids: list[str],
    format: Literal["full", "metadata", "minimal"] = "metadata"
) -> list[Message]
```

#### FR-LIB-051: Batch Modify Labels
```python
def batch_modify_labels(
    self,
    connection_id: str,
    message_ids: list[str],
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None
) -> bool
```

---

## 2. MCP Tools Requirements

### 2.1 Setup & Configuration Tools

#### FR-MCP-001: gmail_check_setup
| Field | Value |
|-------|-------|
| **Name** | `gmail_check_setup` |
| **Description** | Check if gmail-multi-user-mcp is properly configured |
| **Inputs** | None |
| **Outputs** | `config_found: bool`, `config_path: str?`, `database_connected: bool`, `database_type: str`, `google_oauth_configured: bool`, `encryption_key_set: bool`, `issues: list[str]`, `ready: bool` |

#### FR-MCP-002: gmail_init_config
| Field | Value |
|-------|-------|
| **Name** | `gmail_init_config` |
| **Description** | Create a gmail_config.yaml file with provided settings |
| **Inputs** | `database_type: "sqlite" | "supabase"`, `sqlite_path?: str`, `supabase_url?: str`, `supabase_key?: str`, `google_client_id?: str`, `google_client_secret?: str`, `redirect_uri: str = "http://localhost:8000/oauth/callback"`, `generate_encryption_key: bool = true` |
| **Outputs** | `config_path: str`, `encryption_key?: str`, `next_steps: list[str]` |

#### FR-MCP-003: gmail_test_connection
| Field | Value |
|-------|-------|
| **Name** | `gmail_test_connection` |
| **Description** | Test database and Google OAuth configuration |
| **Inputs** | `verbose: bool = false` |
| **Outputs** | `database_ok: bool`, `database_error?: str`, `google_oauth_ok: bool`, `google_oauth_error?: str`, `test_auth_url?: str` |

#### FR-MCP-004: gmail_run_migrations
| Field | Value |
|-------|-------|
| **Name** | `gmail_run_migrations` |
| **Description** | Run database migrations (idempotent) |
| **Inputs** | None |
| **Outputs** | `migrations_run: list[str]`, `already_applied: list[str]`, `current_version: str` |

### 2.2 OAuth & User Management Tools

#### FR-MCP-010: gmail_get_auth_url
| Field | Value |
|-------|-------|
| **Name** | `gmail_get_auth_url` |
| **Description** | Generate OAuth URL for user to connect Gmail |
| **Inputs** | `user_id: str`, `scopes: list[str] = ["gmail.readonly", "gmail.send"]`, `redirect_uri?: str` |
| **Outputs** | `auth_url: str`, `state: str`, `expires_in: int` |

#### FR-MCP-011: gmail_handle_oauth_callback
| Field | Value |
|-------|-------|
| **Name** | `gmail_handle_oauth_callback` |
| **Description** | Process OAuth callback and store tokens |
| **Inputs** | `code: str`, `state: str` |
| **Outputs** | `success: bool`, `connection_id?: str`, `user_id?: str`, `gmail_address?: str`, `error?: str` |

#### FR-MCP-012: gmail_list_connections
| Field | Value |
|-------|-------|
| **Name** | `gmail_list_connections` |
| **Description** | List Gmail connections |
| **Inputs** | `user_id?: str`, `include_inactive: bool = false` |
| **Outputs** | `connections: list[{id, user_id, gmail_address, scopes, is_active, created_at, last_used_at}]` |

#### FR-MCP-013: gmail_check_connection
| Field | Value |
|-------|-------|
| **Name** | `gmail_check_connection` |
| **Description** | Check if a connection is valid |
| **Inputs** | `connection_id: str` |
| **Outputs** | `valid: bool`, `gmail_address: str`, `scopes: list[str]`, `token_expires_in?: int`, `needs_reauth: bool`, `error?: str` |

#### FR-MCP-014: gmail_disconnect
| Field | Value |
|-------|-------|
| **Name** | `gmail_disconnect` |
| **Description** | Disconnect Gmail account and delete tokens |
| **Inputs** | `connection_id: str`, `revoke_google_access: bool = true` |
| **Outputs** | `success: bool`, `gmail_address: str` |

### 2.3 Gmail Operation Tools

#### FR-MCP-020: gmail_search
| Field | Value |
|-------|-------|
| **Name** | `gmail_search` |
| **Description** | Search emails using Gmail query syntax |
| **Inputs** | `connection_id: str`, `query: str`, `max_results: int = 10`, `include_body: bool = false` |
| **Outputs** | `messages: list[Message]`, `total_estimate: int` |

#### FR-MCP-021: gmail_get_message
| Field | Value |
|-------|-------|
| **Name** | `gmail_get_message` |
| **Description** | Get single message with full content |
| **Inputs** | `connection_id: str`, `message_id: str`, `format: "full" | "metadata" | "minimal" = "full"` |
| **Outputs** | Full Message object |

#### FR-MCP-022: gmail_get_thread
| Field | Value |
|-------|-------|
| **Name** | `gmail_get_thread` |
| **Description** | Get all messages in a thread |
| **Inputs** | `connection_id: str`, `thread_id: str` |
| **Outputs** | Thread object with messages |

#### FR-MCP-023: gmail_send
| Field | Value |
|-------|-------|
| **Name** | `gmail_send` |
| **Description** | Send email |
| **Inputs** | `connection_id: str`, `to: list[str]`, `subject: str`, `body: str`, `body_html?: str`, `cc?: list[str]`, `bcc?: list[str]`, `reply_to_message_id?: str`, `attachments?: list[AttachmentInput]` |
| **Outputs** | `success: bool`, `message_id: str`, `thread_id: str` |

#### FR-MCP-024: gmail_create_draft
| Field | Value |
|-------|-------|
| **Name** | `gmail_create_draft` |
| **Description** | Create draft email |
| **Inputs** | Same as gmail_send (except attachments) |
| **Outputs** | `draft_id: str`, `message_id: str` |

#### FR-MCP-025: gmail_send_draft
| Field | Value |
|-------|-------|
| **Name** | `gmail_send_draft` |
| **Description** | Send existing draft |
| **Inputs** | `connection_id: str`, `draft_id: str` |
| **Outputs** | `success: bool`, `message_id: str`, `thread_id: str` |

#### FR-MCP-026: gmail_modify_labels
| Field | Value |
|-------|-------|
| **Name** | `gmail_modify_labels` |
| **Description** | Add/remove labels from message |
| **Inputs** | `connection_id: str`, `message_id: str`, `add_labels: list[str]`, `remove_labels: list[str]` |
| **Outputs** | `success: bool`, `current_labels: list[str]` |

#### FR-MCP-027: gmail_archive
| Field | Value |
|-------|-------|
| **Name** | `gmail_archive` |
| **Description** | Archive message (remove from inbox) |
| **Inputs** | `connection_id: str`, `message_id: str` |
| **Outputs** | `success: bool` |

#### FR-MCP-028: gmail_trash
| Field | Value |
|-------|-------|
| **Name** | `gmail_trash` |
| **Description** | Move message to trash |
| **Inputs** | `connection_id: str`, `message_id: str` |
| **Outputs** | `success: bool` |

#### FR-MCP-029: gmail_get_attachment
| Field | Value |
|-------|-------|
| **Name** | `gmail_get_attachment` |
| **Description** | Download attachment |
| **Inputs** | `connection_id: str`, `message_id: str`, `attachment_id: str` |
| **Outputs** | `filename: str`, `mime_type: str`, `size: int`, `content_base64: str` |

---

## 3. MCP Resources Requirements

#### FR-RES-001: config://status
| Field | Value |
|-------|-------|
| **URI** | `config://status` |
| **MIME Type** | `application/json` |
| **Description** | Current configuration status and health |
| **Content** | `configured`, `config_path`, `database.type/connected`, `google_oauth.configured`, `encryption.key_set`, `server.running/transport` |

#### FR-RES-002: config://schema
| Field | Value |
|-------|-------|
| **URI** | `config://schema` |
| **MIME Type** | `text/yaml` |
| **Description** | Full configuration schema with documentation |

#### FR-RES-003: users://list
| Field | Value |
|-------|-------|
| **URI** | `users://list` |
| **MIME Type** | `application/json` |
| **Description** | All users with Gmail connections |
| **Content** | List of `{id, external_user_id, email, connection_count, created_at}` |

#### FR-RES-004: users://{user_id}/connections
| Field | Value |
|-------|-------|
| **URI Template** | `users://{user_id}/connections` |
| **MIME Type** | `application/json` |
| **Description** | All Gmail connections for specific user |

#### FR-RES-005: gmail://{connection_id}/labels
| Field | Value |
|-------|-------|
| **URI Template** | `gmail://{connection_id}/labels` |
| **MIME Type** | `application/json` |
| **Description** | All labels for a Gmail connection |

#### FR-RES-006: gmail://{connection_id}/profile
| Field | Value |
|-------|-------|
| **URI Template** | `gmail://{connection_id}/profile` |
| **MIME Type** | `application/json` |
| **Description** | Gmail profile info (email, quota) |
| **Content** | `email_address`, `messages_total`, `threads_total`, `history_id` |

#### FR-RES-007: docs://setup
| Field | Value |
|-------|-------|
| **URI** | `docs://setup` |
| **MIME Type** | `text/markdown` |
| **Description** | Quick setup guide |

#### FR-RES-008: docs://google-oauth
| Field | Value |
|-------|-------|
| **URI** | `docs://google-oauth` |
| **MIME Type** | `text/markdown` |
| **Description** | Step-by-step Google Cloud OAuth setup guide |

#### FR-RES-009: docs://troubleshooting
| Field | Value |
|-------|-------|
| **URI** | `docs://troubleshooting` |
| **MIME Type** | `text/markdown` |
| **Description** | Common issues and fixes |

---

## 4. MCP Prompts Requirements

#### FR-PRM-001: setup-gmail
| Field | Value |
|-------|-------|
| **Name** | `setup-gmail` |
| **Description** | Complete setup wizard |
| **Arguments** | None |
| **Workflow** | 1. Check setup status → 2. Create config if missing → 3. Guide Google OAuth setup → 4. Run migrations → 5. Test configuration → 6. Offer test account connection |

#### FR-PRM-002: connect-test-account
| Field | Value |
|-------|-------|
| **Name** | `connect-test-account` |
| **Description** | Connect developer's Gmail for testing |
| **Arguments** | None |
| **Workflow** | 1. Verify setup complete → 2. Generate OAuth URL → 3. Guide through authorization → 4. Verify connection → 5. Test with search |

#### FR-PRM-003: diagnose-connection
| Field | Value |
|-------|-------|
| **Name** | `diagnose-connection` |
| **Description** | Debug failing Gmail connection |
| **Arguments** | `connection_id?: str` |
| **Workflow** | 1. List connections if not specified → 2. Check status → 3. Identify issue → 4. Provide solution → 5. Test fix |

#### FR-PRM-004: generate-oauth-ui
| Field | Value |
|-------|-------|
| **Name** | `generate-oauth-ui` |
| **Description** | Generate OAuth UI components |
| **Arguments** | `framework: "react" | "vue" | "nextjs" | "html"`, `style?: "tailwind" | "css" | "shadcn"` |
| **Workflow** | 1. Generate Connect button → 2. Generate callback handler → 3. Generate status component → 4. Generate API routes → 5. Add TypeScript types |

#### FR-PRM-005: build-email-agent
| Field | Value |
|-------|-------|
| **Name** | `build-email-agent` |
| **Description** | Scaffold email-capable AI agent |
| **Arguments** | `framework: "langchain" | "crewai" | "vercel-ai" | "custom"`, `use_case: str` |
| **Workflow** | 1. Verify Gmail setup → 2. Recommend tools → 3. Generate agent code → 4. Create test scenarios → 5. Document usage |

---

## 5. CLI Commands Requirements

#### FR-CLI-001: gmail-mcp serve
```bash
gmail-mcp serve [OPTIONS]

Options:
  --transport [stdio|http]  Transport mode (default: http)
  --host TEXT               Host to bind (default: 127.0.0.1)
  --port INTEGER            Port to bind (default: 8000)
  --config PATH             Config file path
  --debug                   Enable debug logging
```

#### FR-CLI-002: gmail-mcp health
```bash
gmail-mcp health

Outputs: Configuration status, database connection, Google OAuth status
```

#### FR-CLI-003: gmail-mcp connections
```bash
gmail-mcp connections list [--user-id TEXT] [--include-inactive]
gmail-mcp connections revoke <connection_id> [--no-google-revoke]
gmail-mcp connections test <connection_id>
```

#### FR-CLI-004: gmail-mcp migrate
```bash
gmail-mcp migrate [--dry-run]

Runs database migrations. --dry-run shows what would be applied.
```

#### FR-CLI-005: gmail-mcp init
```bash
gmail-mcp init [--database sqlite|supabase] [--output PATH]

Creates gmail_config.yaml template with prompts for required values.
```

---

## 6. Configuration Requirements

#### FR-CFG-001: Configuration File Format
The configuration file SHALL be YAML format with the following structure:

```yaml
database:
  type: sqlite | supabase
  sqlite_path: str          # Required if type: sqlite
  supabase_url: str         # Required if type: supabase
  supabase_service_key: str # Required if type: supabase

google:
  client_id: str            # Required
  client_secret: str        # Required
  redirect_uri: str         # Required

encryption:
  key: str                  # Required: 64-character hex string

server:
  host: str                 # Optional, default: 127.0.0.1
  port: int                 # Optional, default: 8000
  auth_token: str           # Optional: Bearer token for HTTP transport
```

#### FR-CFG-002: Environment Variable Mapping
| Environment Variable | Config Path |
|---------------------|-------------|
| `GMAIL_MCP_CONFIG` | File path override |
| `GMAIL_MCP_DATABASE_TYPE` | `database.type` |
| `GMAIL_MCP_SQLITE_PATH` | `database.sqlite_path` |
| `GMAIL_MCP_SUPABASE_URL` | `database.supabase_url` |
| `GMAIL_MCP_SUPABASE_KEY` | `database.supabase_service_key` |
| `GMAIL_MCP_GOOGLE_CLIENT_ID` | `google.client_id` |
| `GMAIL_MCP_GOOGLE_CLIENT_SECRET` | `google.client_secret` |
| `GMAIL_MCP_GOOGLE_REDIRECT_URI` | `google.redirect_uri` |
| `GMAIL_MCP_ENCRYPTION_KEY` | `encryption.key` |
| `GMAIL_MCP_SERVER_HOST` | `server.host` |
| `GMAIL_MCP_SERVER_PORT` | `server.port` |
| `GMAIL_MCP_SERVER_AUTH_TOKEN` | `server.auth_token` |

---

## 7. Storage Backend Requirements

#### FR-STG-001: Storage Backend Interface
All storage backends SHALL implement the following interface:

```python
class StorageBackend(Protocol):
    async def initialize(self) -> None: ...
    async def close(self) -> None: ...

    # Users
    async def get_or_create_user(self, external_user_id: str, email: str | None = None) -> User: ...
    async def get_user_by_external_id(self, external_user_id: str) -> User | None: ...
    async def list_users(self) -> list[User]: ...

    # Connections
    async def create_connection(self, user_id: str, gmail_address: str, access_token: str, refresh_token: str, expires_at: datetime, scopes: list[str]) -> Connection: ...
    async def get_connection(self, connection_id: str) -> Connection | None: ...
    async def list_connections(self, user_id: str | None = None, include_inactive: bool = False) -> list[Connection]: ...
    async def update_connection_tokens(self, connection_id: str, access_token: str, expires_at: datetime) -> None: ...
    async def deactivate_connection(self, connection_id: str) -> None: ...
    async def delete_connection(self, connection_id: str) -> None: ...

    # OAuth State
    async def create_oauth_state(self, state: str, user_id: str, scopes: list[str], redirect_uri: str, code_verifier: str, expires_at: datetime) -> None: ...
    async def get_oauth_state(self, state: str) -> OAuthState | None: ...
    async def delete_oauth_state(self, state: str) -> None: ...
    async def cleanup_expired_states(self) -> int: ...
```

#### FR-STG-002: SQLite Backend
- SHALL store data in a single SQLite file
- SHALL support `:memory:` for testing
- SHALL encrypt tokens before storage

#### FR-STG-003: Supabase Backend
- SHALL connect via Supabase Python client
- SHALL use service key for authentication
- SHALL encrypt tokens before storage
- SHALL support connection pooling
