# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of gmail-multi-user-mcp

## [0.1.0] - 2026-01-12

### Added

#### Core Library (`gmail_multi_user/`)
- **Configuration System**
  - Pydantic-settings based configuration with multi-source support
  - Environment variable overrides with `GMAIL_MCP_` prefix
  - YAML configuration file support
  - Fernet encryption key support (base64 or hex format)

- **Storage Backends**
  - SQLite backend for local development
  - Supabase (PostgreSQL) backend for production
  - StorageBackend abstraction for pluggable storage
  - StorageFactory for dynamic backend creation

- **OAuth 2.0 Implementation**
  - Google OAuth 2.0 with PKCE support
  - Single-use states with 10-minute TTL
  - Local HTTP server for CLI OAuth callback
  - Token encryption with Fernet (AES-128-CBC)
  - Automatic token refresh with 5-minute buffer

- **Gmail API Client**
  - Full Gmail API coverage for read operations
  - Search with Gmail query syntax
  - Message retrieval (full, metadata, minimal formats)
  - Thread retrieval
  - Attachment download
  - Label listing
  - Profile information

- **Gmail Write Operations**
  - Send emails (plain text and HTML)
  - Reply to messages (single and reply-all)
  - Create, update, send, and delete drafts
  - Attachment support via MIME building

- **Gmail Management Operations**
  - Label modification (add/remove)
  - Archive messages
  - Mark read/unread
  - Trash/untrash messages
  - Batch operations support

- **MIME Handling**
  - MessageParser for recursive MIME parsing
  - Support for nested multipart messages
  - Attachment metadata extraction
  - MessageComposer for MIME message building
  - Support for multipart/alternative (text + HTML)

#### MCP Server (`gmail_mcp_server/`)
- **FastMCP Integration**
  - 18 MCP tools for Gmail operations
  - 8 MCP resources for data access
  - 5 MCP prompts for guided workflows
  - Lifespan management for proper resource cleanup
  - ServerState pattern for lazy initialization

- **Setup Tools**
  - `gmail_check_setup` - Configuration status check
  - `gmail_init_config` - Configuration file creation
  - `gmail_test_connection` - Database and OAuth testing
  - `gmail_run_migrations` - Database migration runner

- **Authentication Tools**
  - `gmail_get_auth_url` - OAuth URL generation
  - `gmail_handle_oauth_callback` - OAuth callback processing
  - `gmail_list_connections` - Connection listing
  - `gmail_check_connection` - Connection health check
  - `gmail_disconnect` - Account disconnection

- **Read Tools**
  - `gmail_search` - Email search with Gmail query syntax
  - `gmail_get_message` - Single message retrieval
  - `gmail_get_thread` - Thread retrieval
  - `gmail_get_attachment` - Attachment download

- **Write Tools**
  - `gmail_send` - Email sending
  - `gmail_create_draft` - Draft creation
  - `gmail_send_draft` - Draft sending

- **Management Tools**
  - `gmail_modify_labels` - Label modification
  - `gmail_archive` - Message archiving
  - `gmail_trash` - Message trashing

- **Resources**
  - `config://status` - Configuration status
  - `config://schema` - Full configuration schema
  - `users://list` - User listing
  - `users://{user_id}/connections` - User connections
  - `gmail://{connection_id}/labels` - Gmail labels
  - `gmail://{connection_id}/profile` - Gmail profile
  - `docs://setup` - Setup documentation
  - `docs://google-oauth` - OAuth setup guide
  - `docs://troubleshooting` - Troubleshooting guide

- **Prompts**
  - `setup_gmail` - Complete setup wizard
  - `connect_test_account` - Test account connection
  - `diagnose_connection` - Connection debugging
  - `generate_oauth_ui` - OAuth UI component generation
  - `build_email_agent` - Email agent scaffolding

#### CLI (`gmail-mcp`)
- `serve` - Start MCP server (stdio or http transport)
- `health` - Configuration health check
- `init` - Configuration file creation
- `migrate` - Database migration runner
- `connections list` - List Gmail connections
- `connections test` - Test a connection
- `connections revoke` - Revoke a connection

#### Documentation
- API reference for library, MCP tools, resources, and prompts
- User guides: quickstart, OAuth setup, multi-user, deployment, MCP integration
- Supabase migration SQL

### Technical Details
- Python 3.10+ required
- AsyncIO-based architecture
- Type hints throughout codebase
- 198 unit tests with >90% coverage

### Dependencies
- fastmcp - MCP server framework
- pydantic-settings - Configuration management
- httpx - Async HTTP client
- cryptography - Fernet encryption
- typer - CLI framework
- rich - Terminal output formatting
- PyYAML - YAML configuration parsing
- supabase - Supabase client (optional)

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 0.1.0 | 2026-01-12 | Initial release |

---

## Migration Guides

### Upgrading to Future Versions

This section will document breaking changes and migration steps for future versions.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
