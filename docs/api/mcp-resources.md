# MCP Resources Reference

This document provides a complete reference for all 8 MCP resources provided by the Gmail Multi-User MCP Server.

Resources provide read-only access to data and documentation. They are accessed via URI patterns.

## Overview

| Category | Resource URI | Description |
|----------|-------------|-------------|
| **Config** | `config://status` | Current configuration status |
| | `config://schema` | Full configuration schema |
| **Users** | `users://list` | List all users |
| | `users://{user_id}/connections` | User's Gmail connections |
| **Gmail** | `gmail://{connection_id}/labels` | Gmail labels |
| | `gmail://{connection_id}/profile` | Gmail profile info |
| **Docs** | `docs://setup` | Setup guide |
| | `docs://google-oauth` | Google OAuth setup guide |
| | `docs://troubleshooting` | Troubleshooting guide |

---

## Configuration Resources

### config://status

Get current configuration status and health.

**URI:** `config://status`

**Response:**
```json
{
  "configured": true,
  "config_path": "/path/to/gmail_config.yaml",
  "database": {
    "type": "sqlite",
    "connected": true
  },
  "google_oauth": {
    "configured": true
  },
  "encryption": {
    "key_set": true
  },
  "server": {
    "running": true,
    "transport": "stdio"
  },
  "issues": []
}
```

| Field | Type | Description |
|-------|------|-------------|
| `configured` | `boolean` | System is fully configured and ready |
| `config_path` | `string \| null` | Path to configuration file |
| `database.type` | `string` | "sqlite" or "supabase" |
| `database.connected` | `boolean` | Database is accessible |
| `google_oauth.configured` | `boolean` | OAuth credentials are set |
| `encryption.key_set` | `boolean` | Encryption key is configured |
| `server.running` | `boolean` | MCP server is running |
| `server.transport` | `string` | Transport mode |
| `issues` | `string[]` | List of configuration issues |

---

### config://schema

Get full configuration schema with documentation.

**URI:** `config://schema`

**Response:** YAML-formatted configuration schema showing all options:

```yaml
# Gmail Multi-User MCP Configuration Schema
# All fields support environment variable overrides with GMAIL_MCP_ prefix

# Security
encryption_key: str
  # Required: Fernet encryption key for token storage
  # Format: 44-character base64 string or 64-character hex string
  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  # Env: GMAIL_MCP_ENCRYPTION_KEY

# Google OAuth Configuration
google:
  client_id: str
    # Required: Google OAuth 2.0 client ID
    # Get from: https://console.cloud.google.com/apis/credentials
    # Env: GMAIL_MCP_GOOGLE__CLIENT_ID

  client_secret: str
    # Required: Google OAuth 2.0 client secret
    # Env: GMAIL_MCP_GOOGLE__CLIENT_SECRET

  redirect_uri: str = "http://localhost:8000/oauth/callback"
    # OAuth redirect URI - must match Google Console configuration
    # Env: GMAIL_MCP_GOOGLE__REDIRECT_URI

  scopes: list[str]
    # Default scopes to request during OAuth

# Storage Backend Configuration
storage:
  type: "sqlite" | "supabase"
    # Storage backend type

  sqlite:
    path: str = "gmail_mcp.db"
      # Path to SQLite database file

  supabase:
    url: str
      # Supabase project URL
    key: str
      # Supabase service role key

# OAuth Settings
oauth_state_ttl_seconds: int = 600
  # OAuth state expiration time (default: 10 minutes)

token_refresh_buffer_seconds: int = 300
  # Refresh tokens this many seconds before expiry (default: 5 minutes)
```

---

## User Resources

### users://list

Get all users with Gmail connections.

**URI:** `users://list`

**Response:**
```json
[
  {
    "id": "internal_uuid_123",
    "external_user_id": "user_123",
    "email": "user@example.com",
    "connection_count": 2,
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "internal_uuid_456",
    "external_user_id": "user_456",
    "email": null,
    "connection_count": 1,
    "created_at": "2024-01-18T14:22:00Z"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Internal user ID |
| `external_user_id` | `string` | Your application's user ID |
| `email` | `string \| null` | User's email (if known) |
| `connection_count` | `integer` | Number of Gmail connections |
| `created_at` | `string` | ISO timestamp |

---

### users://{user_id}/connections

Get all Gmail connections for a specific user.

**URI:** `users://{user_id}/connections`

**Parameters:**
- `{user_id}` - The external user ID (your application's user ID)

**Response:**
```json
[
  {
    "id": "conn_abc123",
    "gmail_address": "personal@gmail.com",
    "scopes": [
      "https://www.googleapis.com/auth/gmail.readonly",
      "https://www.googleapis.com/auth/gmail.send"
    ],
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T14:22:00Z",
    "last_used_at": "2024-01-20T16:45:00Z",
    "token_expires_at": "2024-01-20T17:30:00Z"
  },
  {
    "id": "conn_def456",
    "gmail_address": "work@company.com",
    "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
    "is_active": true,
    "created_at": "2024-01-18T09:15:00Z",
    "updated_at": "2024-01-18T09:15:00Z",
    "last_used_at": null,
    "token_expires_at": "2024-01-18T10:15:00Z"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Connection ID |
| `gmail_address` | `string` | Gmail email address |
| `scopes` | `string[]` | Granted OAuth scopes |
| `is_active` | `boolean` | Connection is active |
| `created_at` | `string` | ISO timestamp |
| `updated_at` | `string` | ISO timestamp |
| `last_used_at` | `string \| null` | Last API call timestamp |
| `token_expires_at` | `string` | Token expiration timestamp |

**Error Response:**
```json
{
  "error": "User not found: user_invalid"
}
```

---

## Gmail Resources

### gmail://{connection_id}/labels

Get all labels for a Gmail connection.

**URI:** `gmail://{connection_id}/labels`

**Parameters:**
- `{connection_id}` - The connection ID

**Response:**
```json
[
  {
    "id": "INBOX",
    "name": "INBOX",
    "type": "system",
    "message_count": 1250,
    "unread_count": 42
  },
  {
    "id": "SENT",
    "name": "SENT",
    "type": "system",
    "message_count": 890,
    "unread_count": 0
  },
  {
    "id": "Label_123",
    "name": "Work/Projects",
    "type": "user",
    "message_count": 156,
    "unread_count": 3
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Label ID (use in `gmail_modify_labels`) |
| `name` | `string` | Display name |
| `type` | `string` | "system" or "user" |
| `message_count` | `integer \| null` | Total messages with label |
| `unread_count` | `integer \| null` | Unread messages with label |

**Common System Labels:**

| ID | Name |
|----|------|
| `INBOX` | Inbox |
| `SENT` | Sent Mail |
| `DRAFT` | Drafts |
| `TRASH` | Trash |
| `SPAM` | Spam |
| `STARRED` | Starred |
| `IMPORTANT` | Important |
| `UNREAD` | Unread (marker) |
| `CATEGORY_PERSONAL` | Personal |
| `CATEGORY_SOCIAL` | Social |
| `CATEGORY_PROMOTIONS` | Promotions |
| `CATEGORY_UPDATES` | Updates |
| `CATEGORY_FORUMS` | Forums |

---

### gmail://{connection_id}/profile

Get Gmail profile info for a connection.

**URI:** `gmail://{connection_id}/profile`

**Parameters:**
- `{connection_id}` - The connection ID

**Response:**
```json
{
  "email_address": "user@gmail.com",
  "messages_total": 15420,
  "threads_total": 8930,
  "history_id": "12345678"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `email_address` | `string` | Gmail email address |
| `messages_total` | `integer` | Total messages in mailbox |
| `threads_total` | `integer` | Total conversation threads |
| `history_id` | `string` | Current history ID (for sync) |

---

## Documentation Resources

### docs://setup

Complete setup guide for gmail-multi-user-mcp.

**URI:** `docs://setup`

**Response:** Markdown-formatted setup guide including:
- Prerequisites
- Installation steps
- Configuration
- First connection
- Testing

---

### docs://google-oauth

Step-by-step Google OAuth configuration guide.

**URI:** `docs://google-oauth`

**Response:** Markdown-formatted guide including:
- Creating a Google Cloud project
- Enabling Gmail API
- Configuring OAuth consent screen
- Creating OAuth 2.0 credentials
- Setting up redirect URIs
- Common pitfalls

---

### docs://troubleshooting

Troubleshooting guide for common issues.

**URI:** `docs://troubleshooting`

**Response:** Markdown-formatted troubleshooting guide including:

**Connection Issues:**
- Token expired
- Invalid credentials
- Revoked access

**Configuration Issues:**
- Missing config file
- Invalid encryption key
- Database connection failed

**API Errors:**
- Rate limiting
- Quota exceeded
- Invalid requests

---

## Usage in MCP Clients

Resources are accessed using the MCP resource protocol. Example with Claude Desktop:

```
// In Claude Desktop, resources are accessed automatically when relevant
// The AI can read resources to understand system state

// Example: AI reads config status to check if setup is complete
// Resource: config://status

// Example: AI reads user's connections to list their Gmail accounts
// Resource: users://user_123/connections

// Example: AI reads labels to help organize emails
// Resource: gmail://conn_abc123/labels
```

Resources are read-only and provide context for the AI to make better decisions about which tools to use.
