# gmail-multi-user-mcp

[![PyPI version](https://badge.fury.io/py/gmail-multi-user-mcp.svg)](https://pypi.org/project/gmail-multi-user-mcp/)
[![CI](https://github.com/RTinkslinger/gmail-mcp-multi-use/actions/workflows/ci.yml/badge.svg)](https://github.com/RTinkslinger/gmail-mcp-multi-use/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Multi-user Gmail integration library and MCP server for AI agents and consumer applications.**

Build email-capable AI agents, automate Gmail workflows, or add multi-user email to your SaaS—all with secure OAuth 2.0 and automatic token management.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Hybrid Distribution** | Use as Python library or standalone MCP server |
| **Multi-User OAuth** | End-users authenticate with their own Gmail accounts |
| **Automatic Token Management** | Fernet encryption, auto-refresh, secure storage |
| **Full Gmail Operations** | Search, read, send, drafts, labels, attachments (18 tools) |
| **Flexible Storage** | SQLite for development, Supabase for production |
| **Dual API** | Both sync (`GmailClient`) and async (`AsyncGmailClient`) |

---

## Quick Start

### Installation

```bash
pip install gmail-multi-user-mcp
```

### 1. Google Cloud Setup

1. Create a [Google Cloud Project](https://console.cloud.google.com/)
2. Enable the [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
3. Create [OAuth 2.0 credentials](https://console.cloud.google.com/apis/credentials) (Desktop or Web application)
4. Add authorized redirect URI: `http://localhost:8000/oauth/callback`

### 2. Configuration

```bash
# Generate config file with wizard
gmail-mcp init
```

Or create `gmail_config.yaml` manually:

```yaml
encryption_key: "your-64-char-hex-key"  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"

google:
  client_id: "your-client-id.apps.googleusercontent.com"
  client_secret: "your-client-secret"
  redirect_uri: "http://localhost:8000/oauth/callback"
  scopes:
    - "https://www.googleapis.com/auth/gmail.readonly"
    - "https://www.googleapis.com/auth/gmail.send"
    - "https://www.googleapis.com/auth/gmail.modify"
    - "https://www.googleapis.com/auth/userinfo.email"

storage:
  type: sqlite  # or "supabase" for production
  sqlite:
    path: "gmail_mcp.db"
```

### 3. Usage

#### As Python Library

```python
from gmail_multi_user import GmailClient

client = GmailClient()

# Generate OAuth URL for a user
auth = client.get_auth_url(user_id="user_123")
print(f"Please visit: {auth.auth_url}")

# After OAuth callback completes...
messages = client.search(
    connection_id="conn_abc",
    query="is:unread from:important@example.com",
    max_results=10
)

for msg in messages.messages:
    print(f"{msg.subject} - {msg.from_.email}")

# Send an email
client.send(
    connection_id="conn_abc",
    to=["recipient@example.com"],
    subject="Hello from Gmail MCP",
    body="This email was sent programmatically!"
)
```

#### As MCP Server

```bash
# Start with stdio transport (for Claude Desktop)
gmail-mcp serve

# Start with HTTP transport (for web apps)
gmail-mcp serve --transport http --port 8000
```

**Claude Desktop configuration** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "gmail": {
      "command": "gmail-mcp",
      "args": ["serve"]
    }
  }
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Application                        │
├─────────────────────────────────────────────────────────────┤
│  GmailClient (sync)  │  AsyncGmailClient  │  MCP Server    │
├─────────────────────────────────────────────────────────────┤
│                     GmailService                            │
│         (orchestration, validation, error handling)         │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ OAuthManager │ TokenManager │ GmailAPIClient│ ConfigLoader │
│   (PKCE)     │ (encryption) │  (REST API)   │   (YAML/env) │
├──────────────┴──────────────┴──────────────┴───────────────┤
│              StorageBackend (abstract)                      │
│         SQLiteBackend  │  SupabaseBackend                  │
└─────────────────────────────────────────────────────────────┘
```

**Design Principles:**
- **Library-first**: 95% of logic in reusable `gmail_multi_user` package
- **MCP server is thin**: ~200 lines wrapping the library
- **Sync wraps async**: `GmailClient` internally uses `AsyncGmailClient`

---

## MCP Tools (18 total)

### Setup & Configuration
| Tool | Description |
|------|-------------|
| `gmail_check_setup` | Verify configuration and connectivity |
| `gmail_init_config` | Create config file interactively |
| `gmail_test_connection` | Test database and OAuth setup |
| `gmail_run_migrations` | Initialize/update database schema |

### OAuth & User Management
| Tool | Description |
|------|-------------|
| `gmail_get_auth_url` | Generate OAuth URL for user |
| `gmail_handle_oauth_callback` | Process OAuth callback |
| `gmail_list_connections` | List user's Gmail connections |
| `gmail_check_connection` | Verify connection health |
| `gmail_disconnect` | Revoke access and delete tokens |

### Gmail Operations
| Tool | Description |
|------|-------------|
| `gmail_search` | Search with Gmail query syntax |
| `gmail_get_message` | Fetch message with full content |
| `gmail_get_thread` | Get all messages in conversation |
| `gmail_send` | Send email (supports HTML, attachments) |
| `gmail_create_draft` | Create draft email |
| `gmail_send_draft` | Send existing draft |
| `gmail_modify_labels` | Add/remove labels |
| `gmail_archive` | Archive message |
| `gmail_trash` | Move to trash |
| `gmail_get_attachment` | Download attachment |

---

## MCP Resources

| Resource URI | Description |
|--------------|-------------|
| `config://status` | Configuration and health status |
| `config://schema` | Full config schema with documentation |
| `users://list` | All users with Gmail connections |
| `users://{user_id}/connections` | Specific user's connections |
| `gmail://{connection_id}/labels` | Available labels for account |
| `gmail://{connection_id}/profile` | Gmail profile and quota info |
| `docs://setup` | Quick setup guide |
| `docs://google-oauth` | Google OAuth setup walkthrough |

---

## MCP Prompts

| Prompt | Description |
|--------|-------------|
| `setup-gmail` | Complete setup wizard workflow |
| `connect-test-account` | Guide for connecting developer's Gmail |
| `diagnose-connection` | Debug failing connections |
| `generate-oauth-ui` | Generate OAuth UI (React/Vue/NextJS/HTML) |
| `build-email-agent` | Scaffold email agent (LangChain/CrewAI/Vercel-AI) |

---

## Security

### OAuth 2.0 + PKCE
- **PKCE flow**: Prevents authorization code interception
- **State parameter**: 32-byte cryptographic random for CSRF protection
- **One-time use**: State tokens consumed after callback
- **10-minute TTL**: Automatic expiration of unused states

### Token Security
- **Fernet encryption**: AES-128-CBC + HMAC-SHA256 for tokens at rest
- **Auto-refresh**: 5-minute buffer before expiry
- **TLS 1.2+**: All external connections encrypted
- **Zero-trust**: Token validation on every operation

### Access Control
- **Connection isolation**: Users can only access their own connections
- **Scope enforcement**: Operations validated against granted OAuth scopes
- **No token exposure**: Tokens never logged or returned to clients

---

## Configuration Reference

### Configuration Priority (highest to lowest)
1. Environment variables (`GMAIL_MCP_*`)
2. `GMAIL_MCP_CONFIG` env var (explicit path)
3. `./gmail_config.yaml` (project directory)
4. `~/.gmail_mcp/config.yaml` (user home)

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GMAIL_MCP_ENCRYPTION_KEY` | Fernet encryption key (64-char hex) |
| `GMAIL_MCP_GOOGLE__CLIENT_ID` | Google OAuth client ID |
| `GMAIL_MCP_GOOGLE__CLIENT_SECRET` | Google OAuth client secret |
| `GMAIL_MCP_GOOGLE__REDIRECT_URI` | OAuth callback URL |
| `GMAIL_MCP_STORAGE__TYPE` | `sqlite` or `supabase` |
| `GMAIL_MCP_STORAGE__SQLITE__PATH` | SQLite database path |
| `GMAIL_MCP_STORAGE__SUPABASE__URL` | Supabase project URL |
| `GMAIL_MCP_STORAGE__SUPABASE__KEY` | Supabase service role key |

---

## CLI Reference

```bash
# Server
gmail-mcp serve [--transport stdio|http] [--host HOST] [--port PORT]
gmail-mcp health

# Configuration
gmail-mcp init [--database sqlite|supabase] [--output PATH]

# Connections
gmail-mcp connections list [--user-id TEXT]
gmail-mcp connections revoke <connection_id>
gmail-mcp connections test <connection_id>

# Database
gmail-mcp migrate [--dry-run]
```

---

## Storage Backends

### SQLite (Development)
```yaml
storage:
  type: sqlite
  sqlite:
    path: "gmail_mcp.db"  # or ":memory:" for testing
```

### Supabase (Production)
```yaml
storage:
  type: supabase
  supabase:
    url: "https://xxx.supabase.co"
    key: "your-service-role-key"  # Not anon key!
```

Run migrations in Supabase SQL Editor:
```sql
-- See migrations/supabase/001_initial.sql
```

---

## Use Cases

- **AI Email Agents**: Build assistants that read, summarize, and draft emails
- **Multi-User SaaS**: Add Gmail integration to your application
- **Workflow Automation**: Automate email processing pipelines
- **CRM Integration**: Log and categorize emails automatically
- **Notification Systems**: Send alerts and updates via Gmail

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/unit -v
pytest tests/integration -v

# Linting & formatting
ruff check .
ruff format .
mypy gmail_multi_user gmail_mcp_server

# Run all checks (pre-commit)
pre-commit run --all-files
```

### Project Structure

```
gmail-multi-user-mcp/
├── gmail_multi_user/       # Core library (95% of logic)
│   ├── client.py           # Public GmailClient, AsyncGmailClient
│   ├── service.py          # GmailService orchestration
│   ├── oauth/              # OAuth 2.0 + PKCE
│   ├── tokens/             # Encryption & refresh
│   ├── storage/            # SQLite & Supabase backends
│   └── gmail/              # Gmail API wrapper
├── gmail_mcp_server/       # MCP server (~200 lines wrapper)
│   ├── server.py           # FastMCP server
│   ├── tools/              # 18 MCP tools
│   ├── resources/          # 8 MCP resources
│   └── prompts/            # 5 MCP prompts
├── tests/
│   ├── unit/
│   └── integration/
└── specs/                  # Design documentation
```

---

## Requirements

- **Python**: 3.10+
- **OS**: Linux, macOS, Windows
- **External Services**:
  - Google Cloud (OAuth credentials + Gmail API)
  - Supabase (optional, for production)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! Please read the specs in `specs/` for architecture context before submitting PRs.

1. Fork the repository
2. Create a feature branch
3. Run tests and linting
4. Submit a pull request

---

## Links

- [PyPI Package](https://pypi.org/project/gmail-multi-user-mcp/)
- [GitHub Repository](https://github.com/RTinkslinger/gmail-mcp-multi-use)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Gmail API Reference](https://developers.google.com/gmail/api/reference/rest)
