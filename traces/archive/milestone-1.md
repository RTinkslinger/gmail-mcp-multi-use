# Milestone 1: Foundation & OAuth
**Iterations:** 1-3 | **Dates:** 2026-01-12 to 2026-01-12

## Summary
Established project foundation with config system, SQLite storage, Fernet encryption, and complete OAuth 2.0 implementation with PKCE. Validated end-to-end OAuth flow with real Google credentials.

## Key Decisions
- Pydantic-settings for config loading; file values take precedence when file explicitly specified
- UUID hex strings for IDs (32 chars) instead of standard UUID format
- JSON arrays stored as TEXT in SQLite for scopes field
- Encryption keys accept both base64 (44 chars) and hex (64 chars) formats
- PKCE verifier length: 64 chars (default), range 43-128 per RFC 7636
- State TTL: 600 seconds (10 minutes) default, configurable
- Token refresh buffer: 300 seconds (5 minutes) before expiry
- Local OAuth server: dynamic port finding in 8000-9000 range
- Single-use OAuth states (deleted after validation)
- `userinfo.email` scope required for fetching authenticated user's email

## Iteration Details

### Iteration 1 - 2026-01-12
**Phase:** Phase 1: Foundation
**Focus:** Project setup, config system, SQLite storage, encryption

**Changes:**
- `pyproject.toml` - Complete package config with all dependencies
- `gmail_multi_user/exceptions.py` - Exception hierarchy (GmailMCPError, ConfigError, TokenError, etc.)
- `gmail_multi_user/types.py` - All dataclasses (User, Connection, OAuthState, Message, etc.)
- `gmail_multi_user/config.py` - ConfigLoader with env/file/home discovery, pydantic validation
- `gmail_multi_user/storage/base.py` - StorageBackend ABC with full interface
- `gmail_multi_user/storage/sqlite.py` - Complete SQLiteBackend with all CRUD operations
- `gmail_multi_user/storage/factory.py` - StorageFactory for backend creation
- `gmail_multi_user/tokens/encryption.py` - TokenEncryption with Fernet (base64/hex keys)
- `migrations/sqlite/001_initial.sql` - Initial schema
- `tests/conftest.py` - Pytest fixtures for testing
- `tests/unit/test_*.py` - 57 unit tests for config, encryption, SQLite storage

**Test Results:** 57 tests passing

---

### Iteration 2 - 2026-01-12
**Phase:** Phase 2: OAuth & Token Management
**Focus:** Complete OAuth 2.0 implementation with PKCE, token management

**Changes:**
- `gmail_multi_user/oauth/pkce.py` - RFC 7636 PKCE implementation (verifier, challenge, verification)
- `gmail_multi_user/oauth/state.py` - OAuth state manager for CSRF protection with TTL
- `gmail_multi_user/oauth/google.py` - Google OAuth client (auth URL, token exchange, refresh, user info)
- `gmail_multi_user/oauth/manager.py` - OAuth flow orchestrator (get_auth_url, handle_callback, disconnect)
- `gmail_multi_user/oauth/local_server.py` - Local HTTP server for CLI OAuth flow with Starlette/uvicorn
- `gmail_multi_user/tokens/manager.py` - Token manager with auto-refresh, expiration buffer
- `templates/oauth_success.html` - Success page for OAuth callback
- `templates/oauth_error.html` - Error page for OAuth callback
- `tests/unit/test_oauth.py` - 18 tests for PKCE and state management
- `tests/unit/test_tokens.py` - 18 tests for Google OAuth client and token manager

**Test Results:** 93 tests passing (57 from Phase 1 + 36 new)

---

### Iteration 3 - 2026-01-12
**Phase:** Phase 2: OAuth & Token Management (Validation)
**Focus:** End-to-end OAuth validation with real Google credentials

**Changes:**
- `gmail_config.yaml` - Test configuration with real credentials (gitignored)
- `gmail_config.yaml.example` - Updated to include userinfo.email scope
- `scripts/test_oauth_flow.py` - End-to-end OAuth test script

**Validation Results:**
- OAuth flow with PKCE completed successfully
- Tokens encrypted and stored in SQLite
- Connection ID: 13d3546ee9a5451ba3a1a62a007a51de
- Gmail: hi@aacash.me
