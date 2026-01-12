# Test Cases Catalog

This document provides an exhaustive catalog of test cases for the `gmail-multi-user-mcp` project, organized by module and functionality.

---

## 1. Configuration Module

### 1.1 Config Loader (`test_config_loader.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| CFG-001 | Load from YAML file | Valid YAML file path | Config object with all fields |
| CFG-002 | Load from environment variables | Env vars set | Config populated from env |
| CFG-003 | Environment overrides file | Both present | Env vars take precedence |
| CFG-004 | Missing required field | YAML without google_oauth | ConfigError raised |
| CFG-005 | Invalid YAML syntax | Malformed YAML | ConfigError with clear message |
| CFG-006 | Default values applied | Minimal config | Defaults for optional fields |
| CFG-007 | Config file not found | Non-existent path | ConfigError raised |
| CFG-008 | Auto-discover config | No explicit path | Finds ~/.gmail_mcp/config.yaml |
| CFG-009 | Storage backend validation | Invalid backend name | ConfigError raised |
| CFG-010 | Supabase config requires URL | Backend=supabase, no URL | ConfigError raised |

### 1.2 Encryption (`test_encryption.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| ENC-001 | Generate valid key | None | 32-byte Fernet key (base64) |
| ENC-002 | Encrypt/decrypt roundtrip | "secret_token" | Original value returned |
| ENC-003 | Invalid key format | "not-a-valid-key" | EncryptionError raised |
| ENC-004 | Tampered ciphertext | Modified encrypted value | EncryptionError raised |
| ENC-005 | Empty string encryption | "" | Empty string decrypted |
| ENC-006 | Unicode encryption | "日本語テスト" | Correct unicode decrypted |
| ENC-007 | Large payload | 1MB string | Encrypts successfully |
| ENC-008 | Wrong key decryption | Encrypted with different key | EncryptionError raised |

---

## 2. Storage Module

### 2.1 SQLite Backend (`test_storage_sqlite.py`)

#### User Operations

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| SQL-U01 | Create new user | external_id, email | User created with UUID |
| SQL-U02 | Get existing user | Known external_id | Same user returned |
| SQL-U03 | User upsert idempotent | Same external_id twice | Single user exists |
| SQL-U04 | Update user email | New email for user | Email updated |
| SQL-U05 | List all users | Multiple users exist | All users returned |
| SQL-U06 | Get user by external ID | Known external_id | User returned |
| SQL-U07 | Get non-existent user | Unknown external_id | None returned |

#### Connection Operations

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| SQL-C01 | Create connection | Valid user_id, tokens | Connection created |
| SQL-C02 | Get connection by ID | Known connection_id | Connection returned |
| SQL-C03 | Get non-existent connection | Unknown ID | None returned |
| SQL-C04 | List user connections | user_id | All user's connections |
| SQL-C05 | List active only | include_inactive=False | Only active connections |
| SQL-C06 | Update tokens | New access_token, expires_at | Fields updated |
| SQL-C07 | Deactivate connection | connection_id | is_active=False |
| SQL-C08 | Delete connection | connection_id | Connection removed |
| SQL-C09 | Unique constraint | Same user+gmail twice | IntegrityError raised |
| SQL-C10 | Cascade delete | Delete user | Connections deleted |

#### OAuth State Operations

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| SQL-O01 | Create OAuth state | state, user_id, code_verifier | State created |
| SQL-O02 | Get valid state | Known state | State returned |
| SQL-O03 | Get expired state | State past expires_at | None returned |
| SQL-O04 | Delete state | state | State removed |
| SQL-O05 | Cleanup expired | Multiple expired states | All expired removed |
| SQL-O06 | Cleanup returns count | 3 expired | Returns 3 |

### 2.2 Supabase Backend (`test_storage_supabase.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| SUP-001 | Connection established | Valid URL and key | Client connected |
| SUP-002 | Invalid credentials | Wrong key | SupabaseError raised |
| SUP-003 | User CRUD | Full lifecycle | All operations work |
| SUP-004 | Connection CRUD | Full lifecycle | All operations work |
| SUP-005 | RLS enforcement | Query without auth | Proper filtering |
| SUP-006 | Concurrent writes | Parallel inserts | No data corruption |
| SUP-007 | Connection pooling | 50 concurrent requests | All succeed |
| SUP-008 | Retry on transient error | Simulated 503 | Retries and succeeds |

---

## 3. OAuth Module

### 3.1 PKCE (`test_pkce.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| PKC-001 | Generate verifier | None | 64-char random string |
| PKC-002 | Verifier character set | Generated verifier | Only a-zA-Z0-9-._~ |
| PKC-003 | Generate challenge | verifier | SHA256 base64url encoded |
| PKC-004 | Challenge is deterministic | Same verifier twice | Same challenge |
| PKC-005 | Min verifier length | 43 chars | Valid |
| PKC-006 | Max verifier length | 128 chars | Valid |
| PKC-007 | Verifier too short | 42 chars | ValidationError |
| PKC-008 | Verifier too long | 129 chars | ValidationError |

### 3.2 OAuth State (`test_oauth_state.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| STA-001 | Generate state | None | 32-byte random hex |
| STA-002 | State is unique | Generate 1000 states | All unique |
| STA-003 | Create with TTL | 10-minute TTL | expires_at set correctly |
| STA-004 | Validate fresh state | Just created | Returns state object |
| STA-005 | Validate expired state | Past expires_at | Returns None |
| STA-006 | Consume state | Valid state | State deleted after use |
| STA-007 | Consume already consumed | Same state twice | Second returns None |
| STA-008 | Cleanup old states | States older than 1 hour | All cleaned up |

### 3.3 OAuth Manager (`test_oauth_manager.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| OAU-001 | Generate auth URL | user_id, scopes | Valid Google OAuth URL |
| OAU-002 | Auth URL has state | Generated URL | State param present |
| OAU-003 | Auth URL has PKCE | Generated URL | code_challenge present |
| OAU-004 | Auth URL has scopes | ["gmail.readonly"] | scope param present |
| OAU-005 | Auth URL has redirect | redirect_uri specified | redirect_uri param |
| OAU-006 | Handle valid callback | code, valid state | Connection created |
| OAU-007 | Handle invalid state | code, unknown state | OAuthError raised |
| OAU-008 | Handle expired state | code, expired state | OAuthError raised |
| OAU-009 | Handle Google error | error=access_denied | OAuthError raised |
| OAU-010 | State consumed on success | Valid callback | State no longer valid |
| OAU-011 | User created if new | New external_user_id | User auto-created |
| OAU-012 | Existing user linked | Known external_user_id | Connection added |

### 3.4 Google OAuth Client (`test_google_oauth.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| GOO-001 | Exchange code for tokens | Valid code | Access + refresh tokens |
| GOO-002 | Exchange with PKCE | code + verifier | Tokens returned |
| GOO-003 | Invalid code | Bad code | GoogleOAuthError |
| GOO-004 | Refresh access token | Valid refresh token | New access token |
| GOO-005 | Refresh with expired | Revoked refresh token | GoogleOAuthError |
| GOO-006 | Get user info | Valid access token | Email address returned |
| GOO-007 | Revoke token | Any token | Revocation succeeds |
| GOO-008 | Network timeout | Simulated timeout | Timeout exception |
| GOO-009 | Rate limited | 429 response | RateLimitError |

---

## 4. Token Module

### 4.1 Token Manager (`test_token_manager.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| TOK-001 | Get valid token | Token expires in 1 hour | Returns decrypted token |
| TOK-002 | Get expiring token | Token expires in 4 min | Triggers refresh |
| TOK-003 | Get expired token | Token expired | Triggers refresh |
| TOK-004 | Refresh updates storage | After refresh | New token in storage |
| TOK-005 | Refresh failure | Google rejects refresh | marks needs_reauth |
| TOK-006 | Concurrent refresh | 2 threads same connection | Single refresh call |
| TOK-007 | Token decryption | Encrypted token | Correct plaintext |
| TOK-008 | Invalid encrypted token | Corrupted ciphertext | Re-auth required |

---

## 5. Gmail Module

### 5.1 Gmail API Client (`test_gmail_client.py`)

#### Search Operations

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| GML-S01 | Search with query | "from:test@example.com" | Message IDs returned |
| GML-S02 | Search empty results | Query matching nothing | Empty list, estimate=0 |
| GML-S03 | Search with max_results | max_results=10 | At most 10 results |
| GML-S04 | Search pagination | page_token | Next page returned |
| GML-S05 | Search rate limited | 429 response | RateLimitError raised |
| GML-S06 | Search auth error | 401 response | AuthError raised |

#### Message Operations

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| GML-M01 | Get message full | message_id, format=full | Complete message |
| GML-M02 | Get message metadata | format=metadata | Headers only |
| GML-M03 | Get message minimal | format=minimal | IDs and labels only |
| GML-M04 | Get non-existent | Unknown ID | NotFoundError |
| GML-M05 | Batch get messages | 10 message IDs | 10 messages returned |
| GML-M06 | Batch partial failure | 1 invalid in batch | Partial results + errors |

#### Thread Operations

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| GML-T01 | Get thread | thread_id | Thread with messages |
| GML-T02 | Get non-existent thread | Unknown ID | NotFoundError |

#### Label Operations

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| GML-L01 | List labels | token | System + user labels |
| GML-L02 | Modify labels add | message_id, add=["STARRED"] | Label added |
| GML-L03 | Modify labels remove | message_id, remove=["UNREAD"] | Label removed |
| GML-L04 | Invalid label | add=["INVALID_LABEL"] | GmailAPIError |

#### Write Operations

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| GML-W01 | Send message | Composed message | message_id returned |
| GML-W02 | Create draft | Message content | draft_id returned |
| GML-W03 | Update draft | draft_id, new content | Draft updated |
| GML-W04 | Send draft | draft_id | message_id returned |
| GML-W05 | Delete draft | draft_id | Draft removed |
| GML-W06 | Archive message | message_id | INBOX label removed |
| GML-W07 | Trash message | message_id | Moved to trash |
| GML-W08 | Untrash message | trashed message_id | Restored from trash |

### 5.2 MIME Parser (`test_mime_parser.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| MIM-001 | Parse plain text | Simple text email | body_text extracted |
| MIM-002 | Parse HTML only | HTML-only email | body_html extracted |
| MIM-003 | Parse multipart alt | text + HTML | Both extracted |
| MIM-004 | Parse with attachment | Email with PDF | Attachment listed |
| MIM-005 | Parse nested MIME | Complex multipart | All parts parsed |
| MIM-006 | Extract headers | Any email | From, To, Subject, Date |
| MIM-007 | Parse address | "Name <email@test.com>" | name="Name", email="email@test.com" |
| MIM-008 | Handle encoding | Base64 body | Correctly decoded |
| MIM-009 | Handle charset | UTF-8 encoded body | Unicode preserved |
| MIM-010 | Handle quoted-printable | QP encoded | Correctly decoded |
| MIM-011 | Missing body | Headers only | Empty body fields |

### 5.3 Message Composer (`test_message_composer.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| CMP-001 | Compose plain text | to, subject, body | Valid MIME message |
| CMP-002 | Compose HTML | body_html provided | multipart/alternative |
| CMP-003 | Compose with attachment | file attachment | multipart/mixed |
| CMP-004 | Compose reply | original_message | In-Reply-To header set |
| CMP-005 | Reply References | Chain of replies | References header updated |
| CMP-006 | CC and BCC | cc, bcc lists | Headers set correctly |
| CMP-007 | Unicode subject | "日本語件名" | Encoded in header |
| CMP-008 | Long subject | 200+ char subject | Properly wrapped |
| CMP-009 | Multiple attachments | 3 files | All attached |
| CMP-010 | Large attachment | 10MB file | Attached successfully |

---

## 6. Service Layer

### 6.1 Gmail Service (`test_service.py`)

| ID | Test Case | Input | Expected Result |
|----|-----------|-------|-----------------|
| SVC-001 | Search with valid connection | connection_id, query | Results returned |
| SVC-002 | Search with invalid connection | Unknown connection_id | ConnectionNotFoundError |
| SVC-003 | Search with inactive connection | Deactivated connection | ConnectionInactiveError |
| SVC-004 | Auto token refresh | Connection with expiring token | Token refreshed silently |
| SVC-005 | Connection last_used updated | After any operation | last_used_at updated |
| SVC-006 | Scope validation | Send without gmail.send | InsufficientScopeError |
| SVC-007 | Send email | connection_id, compose params | message_id returned |
| SVC-008 | Get auth URL | user_id, scopes | AuthUrlResult returned |
| SVC-009 | Handle callback | code, state | CallbackResult returned |
| SVC-010 | Disconnect | connection_id | Connection deactivated |
| SVC-011 | List connections | user_id | User's connections |

---

## 7. MCP Server

### 7.1 MCP Tools (`test_mcp_tools.py`)

| ID | Test Case | Tool | Input | Expected |
|----|-----------|------|-------|----------|
| MCP-T01 | gmail_check_setup | Setup check | None | Status object |
| MCP-T02 | gmail_init_config | Initialize | None | Config path |
| MCP-T03 | gmail_test_connection | Test DB | None | Test results |
| MCP-T04 | gmail_run_migrations | Migrate | None | Migration result |
| MCP-T05 | gmail_get_auth_url | Auth URL | user_id, scopes | URL + state |
| MCP-T06 | gmail_handle_oauth_callback | Callback | code, state | Result |
| MCP-T07 | gmail_list_connections | List | user_id | Connections array |
| MCP-T08 | gmail_check_connection | Health | connection_id | Health status |
| MCP-T09 | gmail_disconnect | Disconnect | connection_id | Success |
| MCP-T10 | gmail_search | Search | connection_id, query | Messages |
| MCP-T11 | gmail_get_message | Get msg | connection_id, message_id | Message |
| MCP-T12 | gmail_get_thread | Get thread | connection_id, thread_id | Thread |
| MCP-T13 | gmail_get_attachment | Attachment | connection_id, message_id, attachment_id | Data |
| MCP-T14 | gmail_send | Send | connection_id, to, subject, body | message_id |
| MCP-T15 | gmail_create_draft | Draft | connection_id, ... | draft_id |
| MCP-T16 | gmail_send_draft | Send draft | connection_id, draft_id | message_id |
| MCP-T17 | gmail_modify_labels | Labels | connection_id, message_id, labels | Updated |
| MCP-T18 | gmail_archive | Archive | connection_id, message_id | Success |

### 7.2 MCP Resources (`test_mcp_resources.py`)

| ID | Test Case | Resource URI | Expected |
|----|-----------|--------------|----------|
| MCP-R01 | config://status | Config status | Status JSON |
| MCP-R02 | config://schema | Config schema | JSON Schema |
| MCP-R03 | users://list | User list | Users array |
| MCP-R04 | users://{id}/connections | User connections | Connections array |
| MCP-R05 | gmail://{id}/labels | Gmail labels | Labels array |
| MCP-R06 | gmail://{id}/profile | Gmail profile | Profile JSON |
| MCP-R07 | docs://setup | Setup docs | Markdown content |
| MCP-R08 | docs://troubleshooting | Troubleshooting | Markdown content |

### 7.3 CLI Commands (`test_cli.py`)

| ID | Test Case | Command | Expected |
|----|-----------|---------|----------|
| CLI-001 | serve stdio | `gmail-mcp serve` | Server starts |
| CLI-002 | serve http | `gmail-mcp serve --transport http` | HTTP server |
| CLI-003 | health check | `gmail-mcp health` | Status output |
| CLI-004 | list connections | `gmail-mcp connections list` | Table output |
| CLI-005 | init config | `gmail-mcp init` | Config created |
| CLI-006 | run migrations | `gmail-mcp migrate` | Migrations run |
| CLI-007 | config validate | `gmail-mcp config validate` | Validation result |
| CLI-008 | help | `gmail-mcp --help` | Help text |
| CLI-009 | version | `gmail-mcp --version` | Version number |

---

## 8. Security Tests

### 8.1 Encryption Security (`test_encryption_security.py`)

| ID | Test Case | Input | Expected |
|----|-----------|-------|----------|
| SEC-E01 | Key entropy | Generated key | High entropy (>7.5 bits/byte) |
| SEC-E02 | No key in logs | Enable debug logging | Key not logged |
| SEC-E03 | No token in logs | API call with token | Token not logged |
| SEC-E04 | Timing attack resistance | Compare ciphertexts | Constant time |

### 8.2 OAuth Security (`test_oauth_security.py`)

| ID | Test Case | Input | Expected |
|----|-----------|-------|----------|
| SEC-O01 | State entropy | Generated state | ≥128 bits entropy |
| SEC-O02 | PKCE verifier entropy | Generated verifier | ≥256 bits entropy |
| SEC-O03 | State reuse prevented | Use state twice | Second fails |
| SEC-O04 | State expiration | 11-minute-old state | Rejected |
| SEC-O05 | CSRF protection | Missing state param | Rejected |

### 8.3 Injection Prevention (`test_injection.py`)

| ID | Test Case | Input | Expected |
|----|-----------|-------|----------|
| SEC-I01 | SQL injection in user_id | `"'; DROP TABLE users;--"` | Safely escaped |
| SEC-I02 | SQL injection in query | Malicious search query | Safely escaped |
| SEC-I03 | Gmail query injection | `"from:a OR 1=1"` | Passed as literal |
| SEC-I04 | Path traversal | `"../../../etc/passwd"` | Rejected |

---

## 9. Performance Tests

### 9.1 Latency (`test_latency.py`)

| ID | Test Case | Operation | Target |
|----|-----------|-----------|--------|
| PRF-L01 | Token validation | Check non-expired token | <10ms P95 |
| PRF-L02 | Token refresh | Full refresh cycle | <500ms P95 |
| PRF-L03 | DB user lookup | Get user by external_id | <5ms P95 |
| PRF-L04 | DB connection lookup | Get connection by id | <5ms P95 |
| PRF-L05 | Search (excluding Gmail) | Internal processing | <50ms P95 |

### 9.2 Concurrency (`test_concurrency.py`)

| ID | Test Case | Scenario | Target |
|----|-----------|----------|--------|
| PRF-C01 | Concurrent searches | 10 parallel searches | All complete |
| PRF-C02 | Concurrent token refresh | Same connection | Single refresh |
| PRF-C03 | Connection pool | 50 parallel DB operations | No pool exhaustion |
| PRF-C04 | Memory under load | 100 operations | No memory leak |

---

## 10. End-to-End Tests

### 10.1 Full Flow (`test_e2e_full_flow.py`)

| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| E2E-001 | Complete OAuth | 1. Get auth URL 2. Simulate callback 3. Verify connection | Connection active |
| E2E-002 | Search and read | 1. Connect 2. Search 3. Get message | Message content |
| E2E-003 | Send email | 1. Connect 2. Compose 3. Send 4. Verify in sent | Email delivered |
| E2E-004 | Draft workflow | 1. Create draft 2. Update 3. Send | Draft sent |
| E2E-005 | Label management | 1. Get message 2. Add label 3. Verify | Label applied |
| E2E-006 | Token refresh | 1. Connect 2. Wait for expiry 3. Make request | Auto-refreshed |
| E2E-007 | Multi-user | 1. User A connects 2. User B connects 3. Both operate | Isolated correctly |
| E2E-008 | Disconnect flow | 1. Connect 2. Disconnect 3. Try operation | Operation fails |
