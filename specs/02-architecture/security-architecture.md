# Security Architecture

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [Security Overview](#1-security-overview)
2. [OAuth 2.0 Implementation](#2-oauth-20-implementation)
3. [Token Security](#3-token-security)
4. [Data Protection](#4-data-protection)
5. [Access Control](#5-access-control)
6. [Threat Model](#6-threat-model)
7. [Security Best Practices](#7-security-best-practices)

---

## 1. Security Overview

### 1.1 Security Principles

| Principle | Implementation |
|-----------|----------------|
| **Defense in Depth** | Multiple layers: OAuth + encryption + validation |
| **Least Privilege** | Request only needed Gmail scopes |
| **Zero Trust** | Validate tokens on every operation |
| **Secure by Default** | Encryption required, PKCE enforced |
| **Fail Secure** | Invalid state → deny access |

### 1.2 Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPER'S TRUST ZONE                                │
│                                                                                 │
│   ┌───────────────────────────────────────────────────────────────────────┐    │
│   │                    gmail-multi-user-mcp                               │    │
│   │                                                                        │    │
│   │   Trusts:                                                             │    │
│   │   • Developer's config (client_id, client_secret, encryption_key)    │    │
│   │   • Storage backend (SQLite/Supabase)                                │    │
│   │                                                                        │    │
│   │   Does NOT trust:                                                     │    │
│   │   • Incoming OAuth callbacks (validates state)                        │    │
│   │   • Stored tokens (encrypts at rest)                                 │    │
│   │   • User input (sanitizes queries)                                   │    │
│   └───────────────────────────────────────────────────────────────────────┘    │
│                                     │                                          │
│                                     │ TLS 1.2+                                 │
│                                     ▼                                          │
│   ┌───────────────────────────────────────────────────────────────────────┐    │
│   │                         Storage Backend                               │    │
│   │                                                                        │    │
│   │   SQLite: File-level access control (OS permissions)                 │    │
│   │   Supabase: Service role key authentication                          │    │
│   └───────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      │ TLS 1.3
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           GOOGLE'S TRUST ZONE                                   │
│                                                                                 │
│   OAuth 2.0: Validates client credentials, issues tokens                       │
│   Gmail API: Validates access tokens, enforces scopes                          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. OAuth 2.0 Implementation

### 2.1 OAuth Flow with PKCE

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                      OAuth 2.0 Authorization Code Flow with PKCE               │
└────────────────────────────────────────────────────────────────────────────────┘

End User          Developer App        gmail-multi-user-mcp         Google OAuth
    │                  │                        │                        │
    │ 1. Click        │                        │                        │
    │    "Connect"    │                        │                        │
    │ ─────────────────>                       │                        │
    │                  │                        │                        │
    │                  │ 2. get_auth_url()     │                        │
    │                  │ ──────────────────────>│                        │
    │                  │                        │                        │
    │                  │                        │ 3. Generate:           │
    │                  │                        │    • state (32 bytes)  │
    │                  │                        │    • code_verifier     │
    │                  │                        │    • code_challenge    │
    │                  │                        │                        │
    │                  │                        │ 4. Store in DB:        │
    │                  │                        │    oauth_states table  │
    │                  │                        │                        │
    │                  │ 5. auth_url + state   │                        │
    │                  │ <──────────────────────│                        │
    │                  │                        │                        │
    │ 6. Redirect to auth_url                  │                        │
    │ <────────────────────────────────────────────────────────────────────>
    │                  │                        │                        │
    │                  │                        │        7. User logs in │
    │                  │                        │           & consents   │
    │                  │                        │                        │
    │ 8. Redirect: callback?code=xxx&state=yyy │                        │
    │ <────────────────────────────────────────────────────────────────────
    │                  │                        │                        │
    │ 9. Forward callback                       │                        │
    │ ─────────────────────────────────────────>│                        │
    │                  │                        │                        │
    │                  │                        │ 10. Validate:          │
    │                  │                        │     • state exists     │
    │                  │                        │     • state not expired│
    │                  │                        │                        │
    │                  │                        │ 11. Exchange code ─────>
    │                  │                        │     + code_verifier    │
    │                  │                        │                        │
    │                  │                        │ <───────────────────────
    │                  │                        │     access_token       │
    │                  │                        │     refresh_token      │
    │                  │                        │                        │
    │                  │                        │ 12. Encrypt & store    │
    │                  │                        │     tokens in DB       │
    │                  │                        │                        │
    │                  │                        │ 13. Delete oauth_state │
    │                  │                        │                        │
    │                  │ 14. Success response  │                        │
    │                  │ <──────────────────────│                        │
    │                  │                        │                        │
    │ 15. Success!     │                        │                        │
    │ <─────────────────                        │                        │
```

### 2.2 PKCE Implementation

```python
import secrets
import hashlib
import base64

class PKCEGenerator:
    """PKCE code verifier and challenge generator."""

    @staticmethod
    def generate_code_verifier(length: int = 64) -> str:
        """
        Generate cryptographically random code verifier.

        Length: 43-128 characters (RFC 7636)
        Characters: [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"
        """
        return secrets.token_urlsafe(length)[:length]

    @staticmethod
    def generate_code_challenge(code_verifier: str) -> str:
        """
        Generate S256 code challenge from verifier.

        challenge = BASE64URL(SHA256(verifier))
        """
        digest = hashlib.sha256(code_verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")
```

### 2.3 State Parameter

```python
class OAuthStateManager:
    """Manage OAuth state for CSRF protection."""

    STATE_LENGTH = 32  # bytes
    STATE_TTL = 600    # 10 minutes

    def generate_state(self) -> str:
        """Generate cryptographically random state."""
        return secrets.token_urlsafe(self.STATE_LENGTH)

    async def create_state(
        self,
        state: str,
        user_id: str,
        scopes: list[str],
        code_verifier: str,
        redirect_uri: str,
    ) -> None:
        """Store state in database with expiration."""
        await self._storage.create_oauth_state(
            state=state,
            user_id=user_id,
            scopes=scopes,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
            expires_at=datetime.utcnow() + timedelta(seconds=self.STATE_TTL),
        )

    async def validate_state(self, state: str) -> OAuthState | None:
        """
        Validate state and return associated data.

        Returns None if:
        - State doesn't exist
        - State has expired
        - State already used (deleted after use)
        """
        oauth_state = await self._storage.get_oauth_state(state)

        if oauth_state is None:
            return None

        if oauth_state.is_expired:
            await self._storage.delete_oauth_state(state)
            return None

        return oauth_state

    async def consume_state(self, state: str) -> None:
        """Delete state after successful use (one-time use)."""
        await self._storage.delete_oauth_state(state)
```

---

## 3. Token Security

### 3.1 Token Encryption

```python
from cryptography.fernet import Fernet

class TokenEncryption:
    """
    Encrypt/decrypt tokens using Fernet (AES-128-CBC + HMAC-SHA256).

    Key requirements:
    - 32 bytes (256 bits) of random data
    - Base64 URL-safe encoded (44 characters)
    - Must be kept secret
    """

    def __init__(self, key: str):
        """
        Initialize with encryption key.

        Args:
            key: 64-character hex string or 44-character base64 key
        """
        # Convert hex key to Fernet-compatible format
        if len(key) == 64:
            key_bytes = bytes.fromhex(key)
            key = base64.urlsafe_b64encode(key_bytes).decode()

        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a token.

        Returns:
            Base64-encoded ciphertext (safe for database storage)
        """
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a token.

        Raises:
            InvalidToken: If ciphertext is invalid or tampered
        """
        return self._fernet.decrypt(ciphertext.encode()).decode()
```

### 3.2 Token Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TOKEN LIFECYCLE                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

                            ┌───────────────┐
                            │   ACQUIRED    │
                            │ (OAuth flow)  │
                            └───────┬───────┘
                                    │
                                    │ Encrypt & Store
                                    ▼
                            ┌───────────────┐
                            │    ACTIVE     │ ◄─────────────────┐
                            │ (token valid) │                   │
                            └───────┬───────┘                   │
                                    │                           │
                    ┌───────────────┼───────────────┐           │
                    │               │               │           │
                    ▼               ▼               ▼           │
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
            │   EXPIRING  │ │   EXPIRED   │ │   REVOKED   │     │
            │ (<5 min)    │ │             │ │ (by user)   │     │
            └──────┬──────┘ └──────┬──────┘ └──────┬──────┘     │
                   │               │               │            │
                   │               │               │            │
                   ▼               ▼               │            │
            ┌─────────────────────────────┐        │            │
            │        REFRESH              │        │      Refresh
            │  (use refresh_token)        │        │      Success
            └──────────────┬──────────────┘        │            │
                           │                       │            │
              ┌────────────┴────────────┐          │            │
              │                         │          │            │
              ▼                         ▼          ▼            │
     ┌─────────────────┐      ┌─────────────────────────┐       │
     │ Refresh SUCCESS │      │    Refresh FAILED       │       │
     │ (new tokens)    │──────│ or USER REVOKED         │       │
     └─────────────────┘      └───────────┬─────────────┘       │
              │                           │                     │
              │                           ▼                     │
              │               ┌─────────────────────────┐       │
              │               │     NEEDS_REAUTH        │       │
              │               │ (mark inactive, notify) │       │
              └───────────────│                         │───────┘
                              └─────────────────────────┘
```

### 3.3 Token Refresh Strategy

```python
class TokenManager:
    """Manage token refresh and validation."""

    REFRESH_BUFFER = timedelta(minutes=5)  # Refresh when < 5 min to expiry

    async def get_valid_token(self, connection: Connection) -> str:
        """
        Get a valid access token, refreshing if needed.

        Strategy:
        1. Check if token expires within REFRESH_BUFFER
        2. If yes, attempt refresh
        3. If refresh fails, mark needs_reauth
        4. Return valid token or raise TokenError
        """
        # Check expiry
        if connection.token_expires_at < datetime.utcnow() + self.REFRESH_BUFFER:
            try:
                return await self._refresh_token(connection)
            except RefreshError as e:
                # Mark connection as needing re-auth
                await self._storage.update_connection(
                    connection.id,
                    is_active=False,
                    needs_reauth=True,
                )
                raise TokenError(
                    code="needs_reauth",
                    message="Token refresh failed. User must re-authenticate.",
                    details={"connection_id": connection.id},
                )

        # Token still valid
        return self._encryption.decrypt(connection.access_token_encrypted)

    async def _refresh_token(self, connection: Connection) -> str:
        """Refresh tokens using refresh_token."""
        refresh_token = self._encryption.decrypt(connection.refresh_token_encrypted)

        # Call Google token endpoint
        new_tokens = await self._google_client.refresh(refresh_token)

        # Encrypt and store new access token
        encrypted_access = self._encryption.encrypt(new_tokens.access_token)
        await self._storage.update_connection_tokens(
            connection.id,
            access_token_encrypted=encrypted_access,
            token_expires_at=new_tokens.expires_at,
        )

        return new_tokens.access_token
```

---

## 4. Data Protection

### 4.1 Data at Rest

| Data Type | Protection | Location |
|-----------|------------|----------|
| Access Token | Fernet encryption (AES-128-CBC) | gmail_connections.access_token_encrypted |
| Refresh Token | Fernet encryption (AES-128-CBC) | gmail_connections.refresh_token_encrypted |
| User IDs | Plain text | users.external_user_id |
| Gmail Addresses | Plain text | gmail_connections.gmail_address |
| OAuth State | Plain text (temporary) | oauth_states.state |
| Code Verifier | Plain text (temporary) | oauth_states.code_verifier |

### 4.2 Data in Transit

| Connection | Protocol | Certificate |
|------------|----------|-------------|
| App → gmail-multi-user-mcp | N/A (library) or HTTPS (MCP HTTP) | Developer-provided |
| gmail-multi-user-mcp → Google | HTTPS (TLS 1.3) | Google CA |
| gmail-multi-user-mcp → Supabase | HTTPS (TLS 1.2+) | Supabase CA |

### 4.3 Sensitive Data Handling

```python
# NEVER log tokens
logger.info(f"Refreshing token for connection {connection_id}")  # OK
logger.debug(f"Token: {access_token}")  # NEVER DO THIS

# NEVER include tokens in errors
raise TokenError(
    message="Token expired",
    details={"connection_id": conn_id}  # OK
    # NEVER: details={"token": token}
)

# NEVER return tokens in API responses
return {
    "connection_id": conn_id,
    "gmail_address": "user@gmail.com",
    # NEVER: "access_token": token
}
```

---

## 5. Access Control

### 5.1 Connection Isolation

```python
class ConnectionValidator:
    """Ensure connection belongs to user."""

    async def validate_access(
        self,
        connection_id: str,
        user_id: str | None = None,
    ) -> Connection:
        """
        Validate that connection exists and optionally belongs to user.

        Raises:
            ConnectionError: If connection not found or doesn't belong to user
        """
        connection = await self._storage.get_connection(connection_id)

        if connection is None:
            raise ConnectionError(
                code="connection_not_found",
                message=f"Connection {connection_id} not found",
            )

        if user_id is not None and connection.user_id != user_id:
            # Don't reveal that connection exists for another user
            raise ConnectionError(
                code="connection_not_found",
                message=f"Connection {connection_id} not found",
            )

        if not connection.is_active:
            raise ConnectionError(
                code="connection_inactive",
                message="Connection is no longer active",
                details={"needs_reauth": True},
            )

        return connection
```

### 5.2 Scope Enforcement

```python
class ScopeValidator:
    """Validate Gmail scopes for operations."""

    SCOPE_REQUIREMENTS = {
        "search": ["gmail.readonly"],
        "get_message": ["gmail.readonly"],
        "send": ["gmail.send", "gmail.compose"],
        "create_draft": ["gmail.compose"],
        "modify_labels": ["gmail.modify"],
        "trash": ["gmail.modify"],
    }

    def validate_scope(
        self,
        operation: str,
        connection_scopes: list[str],
    ) -> None:
        """
        Validate connection has required scope for operation.

        Raises:
            GmailAPIError: If scope not granted
        """
        required = self.SCOPE_REQUIREMENTS.get(operation, [])

        # Check if any required scope is present
        if not any(scope in connection_scopes for scope in required):
            raise GmailAPIError(
                code="permission_denied",
                message=f"Operation '{operation}' requires scope: {required}",
                details={
                    "required_scopes": required,
                    "granted_scopes": connection_scopes,
                },
            )
```

---

## 6. Threat Model

### 6.1 Threat Matrix

| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| **Token theft from DB** | Medium | High | Fernet encryption at rest |
| **OAuth CSRF attack** | Medium | High | State parameter + one-time use |
| **Token interception (transit)** | Low | High | TLS for all connections |
| **Brute force state** | Very Low | Medium | 32-byte random state, 10min TTL |
| **Code injection (Gmail query)** | Low | Medium | API passes query directly, no shell |
| **Unauthorized access to other user's Gmail** | Low | Critical | Connection isolation in DB |
| **Encryption key compromise** | Low | Critical | Key in env var, never logged |
| **Refresh token abuse** | Low | High | Stored encrypted, revocable |

### 6.2 Attack Scenarios and Mitigations

#### Scenario 1: Attacker steals database

**Attack:** Attacker gains read access to SQLite file or Supabase.

**Mitigations:**
- Tokens encrypted with Fernet (AES-128-CBC + HMAC)
- Without encryption key, tokens are useless
- Encryption key never stored in database

#### Scenario 2: OAuth callback hijacking

**Attack:** Attacker intercepts OAuth callback or guesses state.

**Mitigations:**
- State is 32 bytes (256 bits) of cryptographic randomness
- State expires after 10 minutes
- State is one-time use (deleted after successful exchange)
- PKCE prevents code interception (code_verifier required)

#### Scenario 3: Token replay attack

**Attack:** Attacker captures valid access token from network.

**Mitigations:**
- TLS for all external communication
- Access tokens are short-lived (1 hour)
- Tokens tied to specific Gmail account

---

## 7. Security Best Practices

### 7.1 For Developers Using This Library

```markdown
## Security Checklist

### Configuration
- [ ] Store encryption_key in environment variable, not config file
- [ ] Use Supabase for production (not SQLite)
- [ ] Set up HTTPS for production redirect_uri
- [ ] Restrict Google OAuth consent screen to verified domains

### Deployment
- [ ] Never commit gmail_config.yaml with real credentials
- [ ] Use secrets manager for encryption key
- [ ] Rotate encryption key periodically (requires re-auth in v1)
- [ ] Monitor for unusual API usage patterns

### Application
- [ ] Validate user_id before calling library methods
- [ ] Handle needs_reauth errors gracefully
- [ ] Provide clear disconnect option to users
- [ ] Log connection events (without tokens)
```

### 7.2 Security Configuration Example

```yaml
# Production security configuration

database:
  type: supabase
  supabase_url: ${SUPABASE_URL}          # From secrets manager
  supabase_service_key: ${SUPABASE_KEY}  # From secrets manager

google:
  client_id: ${GOOGLE_CLIENT_ID}
  client_secret: ${GOOGLE_CLIENT_SECRET}  # From secrets manager
  redirect_uri: https://myapp.com/oauth/callback  # HTTPS only

encryption:
  key: ${GMAIL_ENCRYPTION_KEY}  # From secrets manager, never in config

server:
  auth_token: ${MCP_AUTH_TOKEN}  # For HTTP transport
```

### 7.3 Audit Logging

```python
class SecurityAuditLogger:
    """Log security-relevant events."""

    def log_oauth_initiated(self, user_id: str) -> None:
        logger.info(f"OAuth flow initiated for user {user_id}")

    def log_oauth_completed(self, user_id: str, gmail: str) -> None:
        logger.info(f"OAuth completed: user {user_id} connected {gmail}")

    def log_oauth_failed(self, user_id: str, reason: str) -> None:
        logger.warning(f"OAuth failed for user {user_id}: {reason}")

    def log_token_refresh(self, connection_id: str) -> None:
        logger.debug(f"Token refreshed for connection {connection_id}")

    def log_token_refresh_failed(self, connection_id: str, reason: str) -> None:
        logger.warning(f"Token refresh failed for {connection_id}: {reason}")

    def log_connection_revoked(self, connection_id: str, by_user: bool) -> None:
        actor = "user" if by_user else "system"
        logger.info(f"Connection {connection_id} revoked by {actor}")

    def log_access_denied(self, connection_id: str, reason: str) -> None:
        logger.warning(f"Access denied for {connection_id}: {reason}")
```
