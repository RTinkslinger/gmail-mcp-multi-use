# Build Traces

## Project Summary

**Current State:** Phase 7 complete (Documentation & Polish). All core functionality complete, including documentation, logging, and sandbox mode.

**Key Architectural Decisions:**
- Pydantic-settings for multi-source config (env vars + YAML files)
- SQLite for local storage, Supabase for production via StorageBackend abstraction
- StorageFactory creates backend based on config.storage.type
- Fernet encryption for token storage (base64 or hex keys)
- OAuth 2.0 with PKCE, single-use states, 10-minute TTL
- Local HTTP server (Starlette/uvicorn) for CLI OAuth flow
- GmailService layer orchestrates token management + API calls
- MessageParser handles recursive MIME parsing for nested multipart
- MessageComposer builds MIME messages (text, HTML, multipart/alternative, attachments)
- Types: Message uses body_plain/body_html/labels (not body/label_ids)
- FastMCP for MCP server with lifespan management
- Tool impl functions separated for CLI reuse (avoid FunctionTool wrapper issues)
- MCP tools, resources, prompts registered via decorators on module import

**Test Coverage:** 234 unit tests passing (MCP layer has manual E2E testing via CLI)

## Milestone Index

| # | Iterations | Focus | Key Decisions |
|---|------------|-------|---------------|
| 1 | 1-3 | Foundation & OAuth | Pydantic config, SQLite storage, PKCE OAuth, userinfo.email scope |

*Full details: `traces/archive/milestone-N.md`*

---

## Current Work (Milestone 2 in progress)

### Iteration 4 - 2026-01-12
**Phase:** Phase 3: Gmail Read Operations
**Focus:** Gmail API client, MIME parser, service layer, unit tests

**Changes:**
- `gmail_multi_user/gmail/client.py` - GmailAPIClient with search, get_message, get_thread, list_labels, get_attachment, get_profile
- `gmail_multi_user/gmail/parser.py` - MessageParser for MIME parsing (text/html/multipart, attachments)
- `gmail_multi_user/gmail/__init__.py` - Updated exports
- `gmail_multi_user/service.py` - GmailService orchestrating token management and API calls
- `tests/unit/test_gmail_api.py` - 16 tests for Gmail API client
- `tests/unit/test_parser.py` - 14 tests for MIME parser
- `tests/conftest.py` - Fixed env_config fixture to use temp directory
- `scripts/test_gmail_read.py` - End-to-end Gmail read test script

**Decisions:**
- Gmail API base URL: `https://gmail.googleapis.com/gmail/v1`
- Batch get uses individual requests (future optimization: batch endpoint)
- MessageParser handles nested multipart MIME recursively
- RateLimitError uses retry_after int parameter (not code kwarg)

**Test Results:** 126 tests passing (93 from Phase 2 + 33 new)

**Real Gmail Validation:**
- Profile: 851 messages, 842 threads
- Labels: 15 system labels listed
- Search: Found messages with pagination
- Full message: Subject, body, attachments parsed correctly

**Next:** Phase 4 - Gmail write operations (send, draft, modify labels)

---

### Iteration 5 - 2026-01-12
**Phase:** Phase 4: Gmail Write Operations
**Focus:** Email composition, send/draft operations, label modification, trash operations

**Changes:**
- `gmail_multi_user/gmail/composer.py` - MessageComposer for MIME message building (text, HTML, multipart/alternative, attachments, reply threading)
- `gmail_multi_user/gmail/client.py` - Added send_message, create/update/send/delete/list drafts, modify_message_labels, batch_modify_labels, trash/untrash
- `gmail_multi_user/gmail/__init__.py` - Export MessageComposer, guess_mime_type
- `gmail_multi_user/service.py` - Added send, reply, create/update/send/delete draft, modify_labels, batch_modify_labels, archive, mark_read/unread, trash/untrash
- `tests/unit/test_composer.py` - 18 tests for MIME composition
- `tests/unit/test_gmail_write.py` - 14 tests for API client write ops
- `tests/unit/test_service_write.py` - 17 tests for service write ops
- `scripts/test_gmail_write.py` - E2E test script for write operations

**Decisions:**
- Python email.mime module for MIME building (standard library)
- Base64url encoding for Gmail API (urlsafe_b64encode)
- SendResult has success, message_id, thread_id (no label_ids per types.py)
- DraftResult has draft_id, message_id (no thread_id per types.py)
- mark_read/unread use single modify_labels for 1 message, batch for multiple

**Test Results:** 175 tests passing (126 from Phase 3 + 49 new)

**Real Gmail Validation:**
- Created draft with HTML body
- Updated draft successfully
- Marked messages read/unread
- Deleted draft (cleanup)

**Next:** Phase 5 - Supabase storage backend

---

### Iteration 6 - 2026-01-12
**Phase:** Phase 5: Supabase Storage Backend
**Focus:** Production-ready storage backend for Supabase

**Changes:**
- `gmail_multi_user/storage/supabase.py` - SupabaseBackend implementing StorageBackend interface
- `gmail_multi_user/storage/factory.py` - Updated to support Supabase backend creation
- `migrations/supabase/001_initial.sql` - PostgreSQL schema with tables, indexes, triggers
- `tests/unit/test_storage_supabase.py` - 23 unit tests with mocked Supabase client

**Decisions:**
- Supabase client uses sync API (async wrapper not needed for simple CRUD)
- JSON stored as TEXT in scopes column (PostgreSQL JSONB could be used)
- updated_at trigger function handles automatic timestamp updates
- StorageFactory does lazy import to avoid dependency issues

**Test Results:** 198 tests passing (175 from Phase 4 + 23 new)

**Migration Features:**
- UUID extension for ID generation
- TIMESTAMPTZ for timezone-aware timestamps
- Foreign key constraints with CASCADE delete
- Indexes on commonly queried columns
- Trigger for automatic updated_at updates

**Next:** Phase 6 - MCP Server implementation

---

### Iteration 7 - 2026-01-12
**Phase:** Phase 6: MCP Server Implementation
**Focus:** FastMCP server, 18 MCP tools, 8 resources, 5 prompts, CLI with Typer

**Changes:**
- `gmail_mcp_server/server.py` - FastMCP server with ServerState lazy initialization, lifespan management
- `gmail_mcp_server/tools/setup.py` - 4 setup tools (gmail_check_setup, gmail_init_config, gmail_test_connection, gmail_run_migrations)
- `gmail_mcp_server/tools/auth.py` - 5 auth tools (gmail_get_auth_url, gmail_handle_oauth_callback, gmail_list_connections, gmail_check_connection, gmail_disconnect)
- `gmail_mcp_server/tools/read.py` - 4 read tools (gmail_search, gmail_get_message, gmail_get_thread, gmail_get_attachment)
- `gmail_mcp_server/tools/write.py` - 3 write tools (gmail_send, gmail_create_draft, gmail_send_draft)
- `gmail_mcp_server/tools/manage.py` - 3 management tools (gmail_modify_labels, gmail_archive, gmail_trash)
- `gmail_mcp_server/resources/config.py` - 2 resources (config://status, config://schema)
- `gmail_mcp_server/resources/users.py` - 2 resources (users://list, users://{user_id}/connections)
- `gmail_mcp_server/resources/gmail.py` - 2 resources (gmail://{connection_id}/labels, gmail://{connection_id}/profile)
- `gmail_mcp_server/resources/docs.py` - 3 resources (docs://setup, docs://google-oauth, docs://troubleshooting)
- `gmail_mcp_server/prompts/` - 5 prompts (setup_gmail, connect_test_account, diagnose_connection, generate_oauth_ui, build_email_agent)
- `gmail_mcp_server/cli.py` - Typer CLI with serve, health, init, migrate, connections subcommands
- `gmail_mcp_server/__init__.py` - Package exports mcp and state
- `gmail_mcp_server/__main__.py` - Entry point for `python -m gmail_mcp_server`

**Decisions:**
- FastMCP uses `instructions` param (not `description`) for server metadata
- Tool impl functions separated from MCP wrappers to allow CLI to call directly
- @mcp.tool decorator wraps functions in FunctionTool which isn't directly callable
- ServerState pattern: lazy initialization of config, storage, managers on first tool call
- Lifespan context manager handles initialize/close for proper resource cleanup
- register_all() function imports tools/resources/prompts to avoid circular imports

**Test Results:** 198 unit tests still passing

**CLI Verification:**
- `gmail-mcp health` shows config status
- `gmail-mcp connections list` shows Gmail connections
- `gmail-mcp init` creates config file
- `gmail-mcp serve` starts MCP server (stdio or http transport)

**Next:** Phase 7 - Integration testing, E2E tests, documentation

---

### Iteration 8 - 2026-01-12
**Phase:** Phase 7: Documentation & Polish
**Focus:** API documentation, user guides, error handling, config validation

**Changes:**
- `docs/api/library.md` - Complete library API reference (GmailService, types, exceptions)
- `docs/api/mcp-tools.md` - Reference for all 18 MCP tools with schemas and examples
- `docs/api/mcp-resources.md` - Reference for all 8 MCP resources
- `docs/api/mcp-prompts.md` - Reference for all 5 MCP prompts
- `docs/guides/quickstart.md` - 5-minute getting started guide
- `docs/guides/oauth-setup.md` - Step-by-step Google OAuth configuration
- `docs/guides/multi-user.md` - Multi-user architecture and patterns
- `docs/guides/deployment.md` - Deployment guide (local, Docker, Kubernetes, Supabase)
- `docs/guides/mcp-integration.md` - Claude Desktop and MCP client integration
- `CHANGELOG.md` - Keep a Changelog format with v0.1.0 release notes
- `gmail_multi_user/exceptions.py` - Enhanced with error codes, suggestions, is_retriable()
- `gmail_multi_user/config.py` - Added ConfigLoader.validate() with comprehensive validation
- `gmail_mcp_server/cli.py` - Added `validate` command for config validation

**Decisions:**
- Error codes use structured format: TYPE_NNN (e.g., AUTH_001, GMAIL_005)
- All exceptions have suggestion field with actionable fix
- is_retriable() method identifies transient errors
- Config validation checks encryption key, OAuth, storage, common warnings
- CLI validate command returns exit code 1 on errors

**Test Results:** 198 unit tests still passing

**Documentation:**
- 4 API reference docs
- 5 user guides
- CHANGELOG.md

**Next:** Structured logging, sandbox/mock mode (if needed)

---

### Iteration 9 - 2026-01-12
**Phase:** Phase 7: Documentation & Polish (continued)
**Focus:** Structured JSON logging, sandbox/mock mode for testing

**Changes:**
- `gmail_multi_user/logging.py` - Full structured logging module with JSON/human formatters, LogContext, StructuredLoggerAdapter
- `gmail_multi_user/service.py` - Added logging to search, send operations with context
- `gmail_multi_user/oauth/manager.py` - Added logging to auth flow operations
- `gmail_multi_user/tokens/manager.py` - Added logging to token refresh operations
- `gmail_multi_user/sandbox/` - New sandbox module with mock OAuth/Gmail clients
- `gmail_multi_user/sandbox/mode.py` - Sandbox state management, SandboxConfig
- `gmail_multi_user/sandbox/mock_oauth.py` - MockGoogleOAuthClient for testing
- `gmail_multi_user/sandbox/mock_gmail.py` - MockGmailAPIClient with sample data generation
- `gmail_mcp_server/cli.py` - Added --log-format option to serve command
- `tests/unit/test_logging.py` - 14 tests for logging module
- `tests/unit/test_sandbox.py` - 22 tests for sandbox mode

**Decisions:**
- LogContext uses contextvars for async-safe request tracing
- JSON format auto-detected: TTY uses human format, non-TTY uses JSON
- Environment variables GMAIL_MCP_LOG_LEVEL and GMAIL_MCP_LOG_FORMAT for config
- Sandbox mode via GMAIL_MCP_SANDBOX=true or enable_sandbox_mode()
- Mock clients generate realistic sample data (50 messages, 25 threads)

**Test Results:** 234 unit tests passing (198 + 14 logging + 22 sandbox)

**Phase 7 Complete:**
- Documentation: 4 API docs, 5 user guides, CHANGELOG
- Error handling: Structured codes, suggestions, is_retriable()
- Config validation: CLI validate command
- Structured logging: JSON/human formats with context
- Sandbox mode: Test without Google credentials

**Next:** Phase 8 - Release preparation (if needed)

---

### Iteration 10 - 2026-01-12
**Phase:** Phase 8: Testing, Docker & Release
**Focus:** Test coverage improvements, integration tests, security tests, Docker, CI/CD

**Changes:**
- `tests/unit/test_service.py` - GmailService tests (60+ new tests, 96% coverage)
- `tests/unit/test_oauth_manager.py` - OAuthManager tests (auth URL, callback, disconnect)
- `tests/unit/test_storage_factory.py` - StorageFactory tests
- `tests/unit/test_token_manager.py` - Additional TokenManager tests
- `tests/integration/test_storage_integration.py` - SQLite storage integration tests
- `tests/integration/test_security.py` - Security tests (encryption, SQL injection, XSS)
- `Dockerfile` - Multi-stage build with non-root user
- `docker-compose.yml` - Dev config with stdio and HTTP variants
- `docker-compose.prod.yml` - Production overrides for Supabase
- `.dockerignore` - Optimized Docker build context
- `.github/workflows/ci.yml` - CI workflow (test, lint, security scan)
- `.github/workflows/release.yml` - Release workflow (PyPI, Docker, GitHub)

**Decisions:**
- Test coverage at 83% (above 80% target)
- Integration tests use real SQLite, security tests verify encryption and injection prevention
- Docker image uses Python 3.12-slim, runs as non-root user
- CI runs on Python 3.10, 3.11, 3.12 matrix
- Release workflow publishes to PyPI and ghcr.io on tags

**Test Results:** 318 tests passing (294 unit + 24 integration)

**Phase 8 Complete:**
- Test coverage: 83% (exceeds 80% target)
- Integration tests: Storage backend with real SQLite
- Security tests: Encryption, SQL injection, XSS prevention
- Docker: Multi-stage Dockerfile, docker-compose for dev/prod
- CI/CD: GitHub Actions for test, lint, release

---
