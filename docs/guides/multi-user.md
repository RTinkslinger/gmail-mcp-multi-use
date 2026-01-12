# Multi-User Guide

This guide explains how gmail-multi-user-mcp handles multiple users and Gmail accounts.

## Data Model

### Users

A **User** represents a user in your application. Users are identified by an `external_user_id` - the ID from your system.

```python
User:
  id: str                # Internal UUID
  external_user_id: str  # Your application's user ID
  email: str | None      # User's email (optional)
  created_at: datetime
  updated_at: datetime
```

### Connections

A **Connection** represents a linked Gmail account. One user can have multiple connections (multiple Gmail accounts).

```python
Connection:
  id: str                        # Internal UUID (connection_id)
  user_id: str                   # Reference to User
  gmail_address: str             # Gmail email address
  access_token_encrypted: str    # Encrypted OAuth token
  refresh_token_encrypted: str   # Encrypted refresh token
  token_expires_at: datetime     # Token expiration
  scopes: list[str]              # Granted OAuth scopes
  is_active: bool                # Connection status
  created_at: datetime
  updated_at: datetime
  last_used_at: datetime | None  # Last API call
```

### Relationship

```
Your App User (external_user_id)
    ├── Connection 1 (personal@gmail.com)
    ├── Connection 2 (work@gmail.com)
    └── Connection 3 (shared@gmail.com)
```

## Connecting Multiple Accounts

### First Account

```python
# Generate auth URL for user
result = await oauth_manager.get_auth_url(user_id="user_123")
# User completes OAuth flow
# Connection 1 created
```

### Additional Accounts

Same user can connect more Gmail accounts:

```python
# Same user_id, different Gmail account
result = await oauth_manager.get_auth_url(user_id="user_123")
# User signs in with different Gmail
# Connection 2 created
```

### Listing User's Connections

```python
# Via MCP tool
result = await gmail_list_connections(user_id="user_123")

# Returns all connections for this user:
# [
#   {"id": "conn_1", "gmail_address": "personal@gmail.com", ...},
#   {"id": "conn_2", "gmail_address": "work@gmail.com", ...},
# ]
```

## Operating on Specific Connections

All Gmail operations use `connection_id`, not `user_id`:

```python
# Search emails in personal account
personal_emails = await gmail_search(
    connection_id="conn_1",  # personal@gmail.com
    query="is:unread"
)

# Search emails in work account
work_emails = await gmail_search(
    connection_id="conn_2",  # work@gmail.com
    query="is:unread"
)
```

This allows precise control over which Gmail account to use.

## User Management Patterns

### Pattern 1: Single Account Per User

Most common - each user connects one Gmail:

```python
async def get_user_connection(user_id: str) -> str:
    """Get the connection_id for a user (assumes single connection)."""
    result = await gmail_list_connections(user_id=user_id)
    if result["connections"]:
        return result["connections"][0]["id"]
    raise Exception("User has no Gmail connection")
```

### Pattern 2: Multiple Accounts Per User

User selects which account to use:

```python
async def get_connections_for_user(user_id: str) -> list:
    """Get all connections for a user to let them choose."""
    result = await gmail_list_connections(user_id=user_id)
    return result["connections"]

async def search_in_account(user_id: str, connection_id: str, query: str):
    """Search in a specific account."""
    # Verify connection belongs to user
    connections = await get_connections_for_user(user_id)
    if not any(c["id"] == connection_id for c in connections):
        raise Exception("Connection doesn't belong to user")

    return await gmail_search(connection_id=connection_id, query=query)
```

### Pattern 3: Aggregate Across Accounts

Search all of a user's accounts:

```python
async def search_all_accounts(user_id: str, query: str) -> list:
    """Search across all user's Gmail accounts."""
    connections = await get_connections_for_user(user_id)

    all_results = []
    for conn in connections:
        result = await gmail_search(
            connection_id=conn["id"],
            query=query
        )
        for msg in result["messages"]:
            msg["account"] = conn["gmail_address"]
            all_results.append(msg)

    return all_results
```

## Security Considerations

### Connection Isolation

- Each connection has its own encrypted tokens
- Tokens are never shared between connections
- Revoking one connection doesn't affect others

### Authorization Checks

Always verify the connection belongs to the requesting user:

```python
async def authorized_gmail_action(user_id: str, connection_id: str):
    """Verify user owns the connection before acting."""
    connections = await gmail_list_connections(user_id=user_id)

    if not any(c["id"] == connection_id for c in connections["connections"]):
        raise PermissionError("Not authorized to access this connection")

    # Proceed with action...
```

### Token Encryption

- Access tokens and refresh tokens are encrypted with Fernet (AES-128)
- Each encryption uses a unique key from your config
- Tokens are decrypted only when making API calls

## Best Practices

### 1. Store Connection Mapping

In your database, track which connection is "primary" for each user:

```sql
CREATE TABLE user_gmail_settings (
    user_id VARCHAR PRIMARY KEY,
    primary_connection_id VARCHAR,
    created_at TIMESTAMP
);
```

### 2. Handle Connection Expiration

Connections can become invalid when:
- User revokes access in Google settings
- Token refresh fails
- Scopes change

Check connection status before operations:

```python
async def ensure_valid_connection(connection_id: str):
    """Check and handle invalid connections."""
    status = await gmail_check_connection(connection_id=connection_id)

    if status["needs_reauth"]:
        # Notify user they need to reconnect
        raise ReauthorizationRequired(
            connection_id=connection_id,
            gmail_address=status["gmail_address"]
        )

    if not status["valid"]:
        raise ConnectionError(status["error"])
```

### 3. Graceful Disconnection

When a user wants to remove an account:

```python
async def disconnect_account(user_id: str, connection_id: str):
    """Safely disconnect a Gmail account."""
    # Verify ownership
    connections = await gmail_list_connections(user_id=user_id)
    if not any(c["id"] == connection_id for c in connections["connections"]):
        raise PermissionError("Not authorized")

    # Disconnect (revokes Google access too)
    await gmail_disconnect(
        connection_id=connection_id,
        revoke_google_access=True
    )

    # Clean up your app's references
    # ...
```

### 4. User ID Consistency

Use consistent user IDs from your application:

```python
# Good: Consistent user ID
await gmail_get_auth_url(user_id=str(db_user.id))

# Bad: Inconsistent IDs create duplicate users
await gmail_get_auth_url(user_id=user.email)  # Sometimes
await gmail_get_auth_url(user_id=str(user.id))  # Other times
```

## Multi-Tenancy

For SaaS applications with multiple organizations:

### Approach 1: Prefix User IDs

```python
user_id = f"org_{org_id}_user_{user_id}"
```

### Approach 2: Separate Storage

Use different databases per tenant (advanced):

```python
# Per-tenant config
config = ConfigLoader.load_for_tenant(tenant_id)
storage = StorageFactory.create(config)
```

## API Reference

### List All Users

```python
# Via resource
users = await read_resource("users://list")
```

### List User's Connections

```python
# Via tool
connections = await gmail_list_connections(user_id="user_123")

# Via resource
connections = await read_resource("users://user_123/connections")
```

### Check Connection Health

```python
status = await gmail_check_connection(connection_id="conn_abc")
```

### Disconnect

```python
await gmail_disconnect(
    connection_id="conn_abc",
    revoke_google_access=True
)
```
