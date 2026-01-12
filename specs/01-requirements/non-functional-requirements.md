# Non-Functional Requirements

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [Security Requirements](#1-security-requirements)
2. [Performance Requirements](#2-performance-requirements)
3. [Reliability Requirements](#3-reliability-requirements)
4. [Scalability Requirements](#4-scalability-requirements)
5. [Maintainability Requirements](#5-maintainability-requirements)
6. [Compatibility Requirements](#6-compatibility-requirements)
7. [Compliance Requirements](#7-compliance-requirements)
8. [Documentation Requirements](#8-documentation-requirements)

---

## 1. Security Requirements

### 1.1 Token Security

#### NFR-SEC-001: Token Encryption at Rest
- All OAuth tokens (access and refresh) SHALL be encrypted before storage
- Encryption algorithm: Fernet (AES-128-CBC with HMAC)
- Encryption key SHALL be user-provided (not hardcoded)
- Encryption key format: 64-character hexadecimal string

#### NFR-SEC-002: Token Encryption in Transit
- All communication with Google APIs SHALL use TLS 1.2+
- MCP HTTP transport SHALL use HTTPS in production
- Internal API calls SHALL support bearer token authentication

#### NFR-SEC-003: Token Lifecycle
- Access tokens SHALL be refreshed before expiration (within 5 minutes of expiry)
- Refresh tokens SHALL be immediately revoked when user disconnects
- Expired OAuth states SHALL be automatically cleaned up

### 1.2 OAuth Security

#### NFR-SEC-010: PKCE Support
- OAuth flow SHALL implement PKCE (Proof Key for Code Exchange)
- Code verifier: 43-128 character random string
- Code challenge method: S256 (SHA-256)

#### NFR-SEC-011: State Parameter
- OAuth flow SHALL use state parameter for CSRF protection
- State SHALL be cryptographically random (32+ bytes)
- State SHALL expire after 10 minutes

#### NFR-SEC-012: Redirect URI Validation
- Callback handler SHALL validate redirect URI matches configuration
- Only exact matches SHALL be accepted (no wildcards)

### 1.3 Input Validation

#### NFR-SEC-020: Query Parameter Sanitization
- All user-provided Gmail queries SHALL be passed to API without shell interpretation
- No SQL injection possible (parameterized queries only)
- Email addresses SHALL be validated before use

#### NFR-SEC-021: Attachment Handling
- Attachment content SHALL be base64 decoded safely
- Maximum attachment size: 25MB (Gmail limit)
- MIME types SHALL be validated

### 1.4 Access Control

#### NFR-SEC-030: Connection Isolation
- Each connection_id SHALL only be usable by its associated user_id
- Cross-user access SHALL be prevented at storage layer
- Connection IDs SHALL be UUIDs (not sequential)

#### NFR-SEC-031: Scope Enforcement
- Operations SHALL verify connection has required Gmail scopes
- Missing scope SHALL result in clear error message
- No scope escalation without re-authentication

### 1.5 Secrets Management

#### NFR-SEC-040: No Hardcoded Secrets
- No secrets SHALL be committed to repository
- Example config SHALL use placeholder values
- Environment variables SHALL be preferred for production secrets

#### NFR-SEC-041: Encryption Key Security
- Encryption key SHALL never be logged
- Encryption key SHALL not be included in error messages
- Key rotation SHALL require re-authentication (v2)

---

## 2. Performance Requirements

### 2.1 Response Time

#### NFR-PERF-001: Library Operations
| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Config loading | < 10ms | < 50ms | < 100ms |
| Token decryption | < 5ms | < 10ms | < 20ms |
| Database query | < 20ms | < 50ms | < 100ms |

#### NFR-PERF-002: Gmail API Operations
| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Search (10 results) | < 500ms | < 1s | < 2s |
| Get message | < 300ms | < 500ms | < 1s |
| Send email | < 500ms | < 1s | < 2s |

*Note: Gmail API latency is largely controlled by Google*

#### NFR-PERF-003: MCP Server Overhead
- MCP tool wrapper SHALL add < 10ms overhead vs direct library call
- Resource reads SHALL complete in < 100ms
- Stdio transport SHALL have < 5ms message overhead

### 2.2 Throughput

#### NFR-PERF-010: Concurrent Operations
- Library SHALL support 100+ concurrent operations per process
- MCP server SHALL handle 50+ concurrent tool calls
- Connection pooling SHALL be used for Supabase

#### NFR-PERF-011: Batch Operations
- Batch get (100 messages) SHALL complete in < 5s
- Batch modify (100 messages) SHALL complete in < 3s

### 2.3 Resource Usage

#### NFR-PERF-020: Memory
- Base library memory: < 50MB
- MCP server memory: < 100MB
- Per-connection overhead: < 1MB

#### NFR-PERF-021: CPU
- Idle CPU usage: < 1%
- Token encryption/decryption: < 10ms CPU time

---

## 3. Reliability Requirements

### 3.1 Availability

#### NFR-REL-001: Library Availability
- Library SHALL not crash on invalid input
- All errors SHALL be caught and returned as typed exceptions
- No uncaught exceptions in production code

#### NFR-REL-002: MCP Server Availability
- Server SHALL recover from temporary network failures
- Server SHALL log errors and continue operation
- Graceful shutdown on SIGTERM/SIGINT

### 3.2 Token Refresh Reliability

#### NFR-REL-010: Proactive Refresh
- Tokens SHALL be refreshed when expiring within 5 minutes
- Background refresh job SHALL run every 60 seconds (when enabled)
- Failed refresh SHALL trigger on-demand retry

#### NFR-REL-011: On-Demand Refresh
- If token expired, refresh SHALL be attempted before API call
- Maximum 3 retry attempts with exponential backoff
- Clear error if refresh permanently fails

### 3.3 Error Recovery

#### NFR-REL-020: Transient Error Handling
- Google API 5xx errors: retry with backoff (3 attempts)
- Network timeouts: retry once after 5s
- Rate limit (429): respect Retry-After header

#### NFR-REL-021: Permanent Error Handling
- Invalid credentials: mark connection as needs_reauth
- Token revoked: mark connection as inactive
- Clear error messages with resolution guidance

---

## 4. Scalability Requirements

### 4.1 Data Scalability

#### NFR-SCALE-001: User Scale
| Metric | SQLite | Supabase Free | Supabase Pro |
|--------|--------|---------------|--------------|
| Users | 1,000 | 10,000 | 100,000+ |
| Connections | 5,000 | 50,000 | 500,000+ |
| Queries/second | 100 | 500 | 5,000+ |

#### NFR-SCALE-002: Connection Limits
- Per user: unlimited connections (practical limit ~10)
- Per deployment: limited by storage backend

### 4.2 Operation Scalability

#### NFR-SCALE-010: Gmail API Limits
| Quota | Limit | Per |
|-------|-------|-----|
| API calls | 1B | Project/day |
| Per-user calls | 250 | User/second |
| Messages sent | 100-2000 | User/day |

*Library SHALL respect these limits and return helpful errors*

---

## 5. Maintainability Requirements

### 5.1 Code Quality

#### NFR-MAINT-001: Type Safety
- 100% type hints on public API
- Strict mypy configuration
- No `Any` types in public interfaces

#### NFR-MAINT-002: Code Style
- Black formatting (line length 88)
- isort for imports
- ruff for linting

#### NFR-MAINT-003: Test Coverage
- Minimum 80% line coverage
- 100% coverage on public API
- Integration tests for all MCP tools

### 5.2 Logging

#### NFR-MAINT-010: Structured Logging
- JSON logging format option
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request correlation IDs

#### NFR-MAINT-011: Sensitive Data Redaction
- Tokens SHALL never be logged
- Email addresses MAY be partially redacted
- Encryption keys SHALL never be logged

### 5.3 Error Messages

#### NFR-MAINT-020: Error Clarity
- All errors SHALL include error code
- All errors SHALL include human-readable message
- All errors SHALL include resolution hints where applicable

---

## 6. Compatibility Requirements

### 6.1 Python Compatibility

#### NFR-COMPAT-001: Python Versions
- Minimum: Python 3.10
- Tested: Python 3.10, 3.11, 3.12
- No deprecated features from Python 3.9

### 6.2 Platform Compatibility

#### NFR-COMPAT-010: Operating Systems
- Linux: Ubuntu 20.04+, Debian 10+
- macOS: 11.0+ (Big Sur)
- Windows: 10+

#### NFR-COMPAT-011: Architecture
- x86_64: full support
- arm64: full support (Apple Silicon, AWS Graviton)

### 6.3 MCP Compatibility

#### NFR-COMPAT-020: MCP Protocol
- MCP specification version: 2024-11-05 or later
- FastMCP SDK version: 0.1.0+
- Transports: stdio, HTTP (Streamable HTTP)

### 6.4 Gmail API Compatibility

#### NFR-COMPAT-030: Gmail API Version
- Gmail API version: v1
- OAuth 2.0 with PKCE
- Scopes: gmail.readonly, gmail.send, gmail.compose, gmail.modify, gmail.labels

---

## 7. Compliance Requirements

### 7.1 Google API Terms

#### NFR-COMP-001: OAuth Verification
- Application MUST be verified by Google for production use
- Limited use compliance (not sending spam, respecting user data)
- Data use disclosure in OAuth consent screen

#### NFR-COMP-002: API Usage Policy
- No bulk data collection
- No selling user data
- Respect user revocation immediately

### 7.2 Privacy

#### NFR-COMP-010: GDPR Considerations
- Users SHALL be able to export their data
- Users SHALL be able to delete their data (disconnect)
- No data retention after disconnection

#### NFR-COMP-011: Data Minimization
- Only store tokens and email addresses
- Do not cache email content
- Do not log email bodies

### 7.3 Open Source

#### NFR-COMP-020: License
- MIT License
- All dependencies SHALL have compatible licenses
- License file in repository root

---

## 8. Documentation Requirements

### 8.1 Code Documentation

#### NFR-DOC-001: Docstrings
- All public functions SHALL have docstrings
- Google-style docstring format
- Include Args, Returns, Raises sections

#### NFR-DOC-002: Type Stubs
- py.typed marker file included
- All public types exported in __init__.py

### 8.2 User Documentation

#### NFR-DOC-010: README
- Quick start (< 5 minutes to first API call)
- Installation instructions
- Basic usage examples

#### NFR-DOC-011: Guides
- Google Cloud OAuth setup (with screenshots)
- Supabase setup
- Production deployment
- Troubleshooting

#### NFR-DOC-012: API Reference
- All library methods documented
- All MCP tools documented
- All CLI commands documented

### 8.3 Examples

#### NFR-DOC-020: Code Examples
- Basic usage (connect, search, send)
- Multi-account handling
- Error handling
- Claude Desktop integration
