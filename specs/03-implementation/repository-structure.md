# Repository Structure

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Complete Directory Layout

```
gmail-multi-user-mcp/
│
├── README.md                           # Quick start guide, badges, overview
├── LICENSE                             # MIT License
├── CHANGELOG.md                        # Version history
├── CONTRIBUTING.md                     # Contribution guidelines
├── pyproject.toml                      # Python package configuration
├── gmail_config.yaml.example           # Example configuration file
├── .gitignore                          # Git ignore patterns
├── .pre-commit-config.yaml             # Pre-commit hooks
│
├── gmail_multi_user/                   # Core library package
│   ├── __init__.py                     # Public API exports
│   ├── client.py                       # GmailClient, AsyncGmailClient
│   ├── service.py                      # GmailService (orchestration)
│   ├── config.py                       # Configuration loading
│   ├── types.py                        # Data types (dataclasses)
│   ├── exceptions.py                   # Custom exceptions
│   ├── py.typed                        # PEP 561 typed marker
│   │
│   ├── oauth/                          # OAuth 2.0 implementation
│   │   ├── __init__.py
│   │   ├── manager.py                  # OAuthManager class
│   │   ├── pkce.py                     # PKCE implementation
│   │   ├── state.py                    # OAuth state management
│   │   └── local_server.py             # Local OAuth callback server
│   │
│   ├── storage/                        # Storage backends
│   │   ├── __init__.py
│   │   ├── base.py                     # StorageBackend abstract class
│   │   ├── factory.py                  # StorageFactory
│   │   ├── sqlite.py                   # SQLiteBackend
│   │   ├── supabase.py                 # SupabaseBackend
│   │   └── migrations.py               # Migration runner
│   │
│   ├── gmail/                          # Gmail API wrapper
│   │   ├── __init__.py
│   │   ├── client.py                   # GmailAPIClient
│   │   ├── messages.py                 # Message operations
│   │   ├── drafts.py                   # Draft operations
│   │   ├── labels.py                   # Label operations
│   │   ├── attachments.py              # Attachment handling
│   │   └── parser.py                   # MIME parsing utilities
│   │
│   └── tokens/                         # Token management
│       ├── __init__.py
│       ├── manager.py                  # TokenManager class
│       └── encryption.py               # Fernet encryption wrapper
│
├── gmail_mcp_server/                   # MCP server package
│   ├── __init__.py
│   ├── __main__.py                     # Entry point: python -m gmail_mcp_server
│   ├── server.py                       # FastMCP server setup
│   ├── cli.py                          # Typer CLI commands
│   │
│   ├── tools/                          # MCP tool definitions
│   │   ├── __init__.py
│   │   ├── setup.py                    # gmail_check_setup, gmail_init_config
│   │   ├── auth.py                     # gmail_get_auth_url, gmail_list_connections
│   │   ├── read.py                     # gmail_search, gmail_get_message
│   │   ├── write.py                    # gmail_send, gmail_create_draft
│   │   └── manage.py                   # gmail_modify_labels, gmail_trash
│   │
│   ├── resources/                      # MCP resource definitions
│   │   ├── __init__.py
│   │   ├── config.py                   # config://status, config://schema
│   │   ├── users.py                    # users://list, users://{id}/connections
│   │   ├── gmail.py                    # gmail://{id}/labels, gmail://{id}/profile
│   │   └── docs.py                     # docs://setup, docs://troubleshooting
│   │
│   └── prompts/                        # MCP prompt definitions
│       ├── __init__.py
│       ├── setup.py                    # setup-gmail prompt
│       ├── connect.py                  # connect-test-account prompt
│       ├── diagnose.py                 # diagnose-connection prompt
│       ├── generate_ui.py              # generate-oauth-ui prompt
│       └── build_agent.py              # build-email-agent prompt
│
├── migrations/                         # Database migrations
│   ├── sqlite/
│   │   └── 001_initial.sql             # Initial SQLite schema
│   └── supabase/
│       └── 001_initial.sql             # Initial Supabase schema
│
├── templates/                          # HTML templates for OAuth
│   ├── oauth_success.html              # "Gmail connected successfully"
│   ├── oauth_error.html                # "Connection failed: {error}"
│   └── base.html                       # Base template
│
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   │
│   ├── unit/                           # Unit tests
│   │   ├── __init__.py
│   │   ├── test_config.py              # Configuration tests
│   │   ├── test_oauth.py               # OAuth flow tests
│   │   ├── test_tokens.py              # Token management tests
│   │   ├── test_storage_sqlite.py      # SQLite backend tests
│   │   ├── test_storage_supabase.py    # Supabase backend tests
│   │   ├── test_gmail_api.py           # Gmail API wrapper tests
│   │   └── test_client.py              # Client interface tests
│   │
│   ├── integration/                    # Integration tests
│   │   ├── __init__.py
│   │   ├── test_mcp_tools.py           # MCP tool integration tests
│   │   ├── test_mcp_resources.py       # MCP resource tests
│   │   └── test_full_flow.py           # End-to-end flow tests
│   │
│   ├── e2e/                            # End-to-end tests (real Gmail)
│   │   ├── __init__.py
│   │   └── test_real_gmail.py          # Tests with real Gmail account
│   │
│   └── mocks/                          # Mock implementations
│       ├── __init__.py
│       ├── gmail_api.py                # Mock Gmail API responses
│       └── storage.py                  # Mock storage backend
│
├── docs/                               # Documentation
│   ├── index.md                        # Documentation home
│   ├── quickstart.md                   # 5-minute getting started
│   ├── google-setup.md                 # Google Cloud setup guide
│   ├── supabase-setup.md               # Supabase setup guide
│   ├── configuration.md                # Full config reference
│   ├── api-reference.md                # Library API docs
│   ├── mcp-tools.md                    # MCP tool reference
│   ├── deployment.md                   # Production deployment
│   ├── troubleshooting.md              # Common issues
│   └── examples/                       # Code examples
│       ├── basic_usage.py
│       ├── multi_account.py
│       └── async_example.py
│
├── examples/                           # Standalone examples
│   ├── basic_usage.py                  # Simple library usage
│   ├── multi_account.py                # Multiple Gmail accounts
│   ├── batch_operations.py             # Efficient bulk operations
│   ├── async_example.py                # Async usage
│   ├── fastapi_integration.py          # FastAPI integration
│   └── claude_desktop_config.json      # Claude Desktop config example
│
├── scripts/                            # Development scripts
│   ├── setup_dev.sh                    # Set up development environment
│   ├── run_tests.sh                    # Run test suite
│   └── generate_docs.sh                # Generate documentation
│
├── docker/                             # Docker support
│   ├── Dockerfile                      # Main Dockerfile
│   ├── Dockerfile.dev                  # Development Dockerfile
│   └── docker-compose.yml              # Local development compose
│
└── .github/                            # GitHub configuration
    ├── workflows/
    │   ├── test.yml                    # Run tests on PR
    │   ├── publish.yml                 # Publish to PyPI on release
    │   └── docs.yml                    # Build and deploy docs
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## File Descriptions

### Root Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quick start, badges |
| `LICENSE` | MIT License text |
| `CHANGELOG.md` | Version history following Keep a Changelog |
| `CONTRIBUTING.md` | How to contribute, code style, PR process |
| `pyproject.toml` | Python package config (deps, scripts, tools) |
| `gmail_config.yaml.example` | Template configuration file |

### Core Library (gmail_multi_user/)

| File/Directory | Purpose |
|----------------|---------|
| `__init__.py` | Public exports: clients, types, exceptions |
| `client.py` | `GmailClient` (sync) and `AsyncGmailClient` (async) |
| `service.py` | `GmailService` - core orchestration logic |
| `config.py` | `Config`, `ConfigLoader` - configuration handling |
| `types.py` | Dataclasses: `Message`, `Connection`, `SearchResult`, etc. |
| `exceptions.py` | `GmailMCPError` hierarchy |
| `py.typed` | PEP 561 marker for type checking |
| `oauth/` | OAuth 2.0 with PKCE, state management |
| `storage/` | Abstract backend with SQLite/Supabase implementations |
| `gmail/` | Gmail API wrapper, MIME parsing |
| `tokens/` | Token encryption and refresh management |

### MCP Server (gmail_mcp_server/)

| File/Directory | Purpose |
|----------------|---------|
| `__init__.py` | Package init |
| `__main__.py` | `python -m gmail_mcp_server` entry point |
| `server.py` | FastMCP server setup (~200 lines) |
| `cli.py` | Typer CLI: `gmail-mcp serve`, `gmail-mcp health` |
| `tools/` | MCP tool definitions (18 tools) |
| `resources/` | MCP resource definitions (8 resources) |
| `prompts/` | MCP prompt definitions (5 prompts) |

### Migrations (migrations/)

| File | Purpose |
|------|---------|
| `sqlite/001_initial.sql` | Create tables for SQLite |
| `supabase/001_initial.sql` | Create tables for Supabase |

### Tests (tests/)

| Directory | Purpose |
|-----------|---------|
| `unit/` | Unit tests for individual components |
| `integration/` | Integration tests for MCP tools |
| `e2e/` | End-to-end tests with real Gmail (CI only) |
| `mocks/` | Mock implementations for testing |

### Documentation (docs/)

| File | Purpose |
|------|---------|
| `quickstart.md` | 5-minute getting started |
| `google-setup.md` | Google Cloud OAuth setup with screenshots |
| `configuration.md` | Full configuration reference |
| `api-reference.md` | Library API documentation |
| `mcp-tools.md` | MCP tool reference |
| `deployment.md` | Production deployment guide |
| `troubleshooting.md` | Common issues and solutions |

---

## Module Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Module Dependency Graph                                 │
│                                                                                  │
│   gmail_mcp_server/                                                              │
│   ├── server.py ───────────────────────────────────────────┐                    │
│   ├── tools/ ──────────────────────────────────────────────┤                    │
│   ├── resources/ ──────────────────────────────────────────┤                    │
│   └── prompts/ ────────────────────────────────────────────┤                    │
│                                                            │                    │
│                                                            ▼                    │
│   gmail_multi_user/                                                              │
│   ├── client.py ──────────────────────────────┐                                 │
│   │                                           │                                 │
│   │                                           ▼                                 │
│   ├── service.py ─────────────────────────────┤                                 │
│   │       │                                   │                                 │
│   │       ├──────────────┐                    │                                 │
│   │       │              │                    │                                 │
│   │       ▼              ▼                    ▼                                 │
│   ├── oauth/ ────────► storage/ ◄──────── gmail/                                │
│   │       │              │                    │                                 │
│   │       │              │                    │                                 │
│   │       ▼              ▼                    ▼                                 │
│   ├── tokens/ ◄──────────┴────────────────────┤                                 │
│   │       │                                   │                                 │
│   │       ▼                                   │                                 │
│   ├── config.py ◄─────────────────────────────┤                                 │
│   │       │                                   │                                 │
│   │       ▼                                   ▼                                 │
│   ├── types.py ◄──────────────────────────────┤                                 │
│   │                                           │                                 │
│   │                                           ▼                                 │
│   └── exceptions.py ◄─────────────────────────┘                                 │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Import Examples

### Using the Library

```python
# Minimal import
from gmail_multi_user import GmailClient

# Full import for typed usage
from gmail_multi_user import (
    GmailClient,
    AsyncGmailClient,
    Config,
    ConfigLoader,
    Message,
    SearchResult,
    GmailMCPError,
    TokenError,
)

# Async usage
from gmail_multi_user import AsyncGmailClient

async def main():
    async with AsyncGmailClient() as client:
        messages = await client.search(connection_id="...", query="is:unread")
```

### Running the MCP Server

```bash
# Via CLI (recommended)
gmail-mcp serve --transport stdio

# Via Python module
python -m gmail_mcp_server serve

# With HTTP transport
gmail-mcp serve --transport http --port 8000
```
