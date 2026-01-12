# MCP Tools Reference

This document provides a complete reference for all 18 MCP tools provided by the Gmail Multi-User MCP Server.

## Overview

| Category | Tool | Description |
|----------|------|-------------|
| **Setup** | `gmail_check_setup` | Check configuration status |
| | `gmail_init_config` | Create configuration file |
| | `gmail_test_connection` | Test database and OAuth |
| | `gmail_run_migrations` | Run database migrations |
| **Auth** | `gmail_get_auth_url` | Generate OAuth URL |
| | `gmail_handle_oauth_callback` | Process OAuth callback |
| | `gmail_list_connections` | List Gmail connections |
| | `gmail_check_connection` | Check connection health |
| | `gmail_disconnect` | Disconnect Gmail account |
| **Read** | `gmail_search` | Search emails |
| | `gmail_get_message` | Get single message |
| | `gmail_get_thread` | Get conversation thread |
| | `gmail_get_attachment` | Download attachment |
| **Write** | `gmail_send` | Send email |
| | `gmail_create_draft` | Create draft |
| | `gmail_send_draft` | Send existing draft |
| **Manage** | `gmail_modify_labels` | Add/remove labels |
| | `gmail_archive` | Archive message |
| | `gmail_trash` | Move to trash |

---

## Setup Tools

### gmail_check_setup

Check if gmail-multi-user-mcp is properly configured.

**Parameters:** None

**Returns:**
```json
{
  "config_found": true,
  "config_path": "/path/to/gmail_config.yaml",
  "database_connected": true,
  "database_type": "sqlite",
  "google_oauth_configured": true,
  "encryption_key_set": true,
  "issues": [],
  "ready": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `config_found` | `boolean` | Configuration file was found |
| `config_path` | `string \| null` | Path to config file |
| `database_connected` | `boolean` | Database is accessible |
| `database_type` | `string` | "sqlite" or "supabase" |
| `google_oauth_configured` | `boolean` | OAuth credentials are set |
| `encryption_key_set` | `boolean` | Encryption key is configured |
| `issues` | `string[]` | List of configuration issues |
| `ready` | `boolean` | System is ready to use |

---

### gmail_init_config

Create a gmail_config.yaml configuration file.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `database_type` | `string` | `"sqlite"` | "sqlite" or "supabase" |
| `sqlite_path` | `string \| null` | `null` | Path for SQLite database |
| `supabase_url` | `string \| null` | `null` | Supabase project URL |
| `supabase_key` | `string \| null` | `null` | Supabase service role key |
| `google_client_id` | `string \| null` | `null` | Google OAuth client ID |
| `google_client_secret` | `string \| null` | `null` | Google OAuth client secret |
| `redirect_uri` | `string` | `"http://localhost:8000/oauth/callback"` | OAuth redirect URI |
| `generate_encryption_key` | `boolean` | `true` | Generate new encryption key |
| `output_path` | `string` | `"./gmail_config.yaml"` | Output file path |

**Returns:**
```json
{
  "config_path": "/absolute/path/to/gmail_config.yaml",
  "encryption_key": "base64_encoded_key...",
  "next_steps": [
    "Set up Google OAuth credentials at https://console.cloud.google.com/apis/credentials",
    "Update google.client_id and google.client_secret in the config",
    "Add gmail_config.yaml to .gitignore to protect secrets"
  ]
}
```

---

### gmail_test_connection

Test database and Google OAuth configuration.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `verbose` | `boolean` | `false` | Include detailed information |

**Returns:**
```json
{
  "database_ok": true,
  "google_oauth_ok": true,
  "database_type": "sqlite",
  "user_count": 5,
  "connection_count": 8,
  "google_redirect_uri": "http://localhost:8000/oauth/callback",
  "google_scopes": ["https://www.googleapis.com/auth/gmail.readonly", "..."]
}
```

---

### gmail_run_migrations

Run database migrations (idempotent).

**Parameters:** None

**Returns:**
```json
{
  "migrations_run": ["001_initial"],
  "already_applied": [],
  "current_version": "001_initial",
  "message": "SQLite tables created/verified automatically"
}
```

---

## Authentication Tools

### gmail_get_auth_url

Generate OAuth URL for user to connect Gmail.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | `string` | required | External user identifier from your application |
| `scopes` | `string[] \| null` | `null` | OAuth scopes to request (defaults to config scopes) |
| `redirect_uri` | `string \| null` | `null` | Override configured redirect URI |

**Returns:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "state": "random_state_string",
  "expires_in": 600
}
```

| Field | Type | Description |
|-------|------|-------------|
| `auth_url` | `string` | URL to redirect user to |
| `state` | `string` | State parameter for CSRF protection |
| `expires_in` | `integer` | Seconds until URL expires (~10 minutes) |

**Example:**
```
gmail_get_auth_url(user_id="user_123")
```

---

### gmail_handle_oauth_callback

Process OAuth callback and store tokens.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | `string` | Authorization code from Google |
| `state_param` | `string` | State parameter for CSRF validation |

**Returns:**
```json
{
  "success": true,
  "connection_id": "conn_abc123",
  "user_id": "user_123",
  "gmail_address": "user@gmail.com",
  "error": null
}
```

---

### gmail_list_connections

List Gmail connections.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | `string \| null` | `null` | Filter by external user ID |
| `include_inactive` | `boolean` | `false` | Include revoked/expired connections |

**Returns:**
```json
{
  "connections": [
    {
      "id": "conn_abc123",
      "user_id": "user_123",
      "gmail_address": "user@gmail.com",
      "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "last_used_at": "2024-01-20T14:22:00Z"
    }
  ]
}
```

---

### gmail_check_connection

Check if a connection is valid and working.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `string` | Connection ID to check |

**Returns:**
```json
{
  "valid": true,
  "gmail_address": "user@gmail.com",
  "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
  "token_expires_in": 3200,
  "needs_reauth": false,
  "error": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `valid` | `boolean` | Connection is working |
| `gmail_address` | `string` | Gmail address |
| `scopes` | `string[]` | Granted OAuth scopes |
| `token_expires_in` | `integer \| null` | Seconds until token expires |
| `needs_reauth` | `boolean` | User needs to re-authorize |
| `error` | `string \| null` | Error message if invalid |

---

### gmail_disconnect

Disconnect Gmail account and delete tokens.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `string` | required | Connection ID to disconnect |
| `revoke_google_access` | `boolean` | `true` | Also revoke access at Google |

**Returns:**
```json
{
  "success": true,
  "gmail_address": "user@gmail.com"
}
```

---

## Read Tools

### gmail_search

Search emails using Gmail query syntax.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `string` | required | Gmail connection to search |
| `query` | `string` | required | Gmail search query (e.g., "is:unread from:boss") |
| `max_results` | `integer` | `10` | Maximum results (1-100) |
| `include_body` | `boolean` | `false` | Include message body in results (slower) |

**Returns:**
```json
{
  "messages": [
    {
      "id": "18abc123def",
      "thread_id": "18abc123def",
      "subject": "Meeting Tomorrow",
      "from": {"name": "John Doe", "email": "john@example.com"},
      "to": [{"name": "", "email": "me@gmail.com"}],
      "cc": [],
      "bcc": [],
      "date": "2024-01-20T10:30:00Z",
      "snippet": "Hi, let's meet tomorrow at 2pm...",
      "body_plain": "...",
      "body_html": "...",
      "labels": ["INBOX", "UNREAD"],
      "has_attachments": false,
      "attachments": []
    }
  ],
  "total_estimate": 150,
  "next_page_token": "token_for_next_page"
}
```

**Example queries:**
- `is:unread` - Unread messages
- `from:boss@company.com` - From specific sender
- `has:attachment after:2024/01/01` - With attachments, after date
- `subject:urgent -from:newsletter` - Subject contains "urgent", not from newsletters

---

### gmail_get_message

Get single message with full content.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `string` | required | Gmail connection |
| `message_id` | `string` | required | ID of the message to retrieve |
| `format` | `string` | `"full"` | Detail level: "full", "metadata", or "minimal" |

**Returns:** Same structure as message in `gmail_search`.

---

### gmail_get_thread

Get all messages in a thread.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `string` | Gmail connection |
| `thread_id` | `string` | ID of the thread to retrieve |

**Returns:**
```json
{
  "id": "18abc123def",
  "subject": "Project Discussion",
  "message_count": 5,
  "messages": [
    { "id": "...", "subject": "...", ... },
    { "id": "...", "subject": "...", ... }
  ]
}
```

---

### gmail_get_attachment

Download attachment.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `string` | Gmail connection |
| `message_id` | `string` | ID of the message containing the attachment |
| `attachment_id` | `string` | ID of the attachment to download |

**Returns:**
```json
{
  "filename": "report.pdf",
  "mime_type": "application/pdf",
  "size": 125000,
  "content_base64": "JVBERi0xLjQK..."
}
```

Note: `content_base64` is base64-encoded binary data.

---

## Write Tools

### gmail_send

Send email.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `string` | required | Gmail connection to send from |
| `to` | `string[]` | required | List of recipient email addresses |
| `subject` | `string` | required | Email subject |
| `body` | `string` | required | Plain text body |
| `body_html` | `string \| null` | `null` | Optional HTML body |
| `cc` | `string[] \| null` | `null` | Optional CC recipients |
| `bcc` | `string[] \| null` | `null` | Optional BCC recipients |
| `reply_to_message_id` | `string \| null` | `null` | Message ID for threading (reply) |

**Returns:**
```json
{
  "success": true,
  "message_id": "18abc123def",
  "thread_id": "18abc123def"
}
```

**Example:**
```
gmail_send(
  connection_id="conn_123",
  to=["recipient@example.com"],
  subject="Hello!",
  body="This is a test email.",
  body_html="<h1>Hello!</h1><p>This is a test email.</p>"
)
```

---

### gmail_create_draft

Create draft email.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `string` | required | Gmail connection |
| `to` | `string[]` | required | List of recipient email addresses |
| `subject` | `string` | required | Email subject |
| `body` | `string` | required | Plain text body |
| `body_html` | `string \| null` | `null` | Optional HTML body |
| `cc` | `string[] \| null` | `null` | Optional CC recipients |
| `bcc` | `string[] \| null` | `null` | Optional BCC recipients |
| `reply_to_message_id` | `string \| null` | `null` | Message ID for threading (reply draft) |

**Returns:**
```json
{
  "draft_id": "draft_abc123",
  "message_id": "18abc123def"
}
```

---

### gmail_send_draft

Send existing draft.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `string` | Gmail connection |
| `draft_id` | `string` | ID of the draft to send |

**Returns:**
```json
{
  "success": true,
  "message_id": "18abc123def",
  "thread_id": "18abc123def"
}
```

---

## Management Tools

### gmail_modify_labels

Add/remove labels from message.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `string` | required | Gmail connection |
| `message_id` | `string` | required | ID of the message to modify |
| `add_labels` | `string[] \| null` | `null` | Label IDs to add |
| `remove_labels` | `string[] \| null` | `null` | Label IDs to remove |

**Returns:**
```json
{
  "success": true,
  "current_labels": ["INBOX", "STARRED", "Label_123"]
}
```

**Common label IDs:**
- `INBOX` - Inbox
- `UNREAD` - Unread marker
- `STARRED` - Starred
- `IMPORTANT` - Important
- `SENT` - Sent
- `DRAFT` - Drafts
- `SPAM` - Spam
- `TRASH` - Trash

---

### gmail_archive

Archive message (remove from inbox).

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `string` | Gmail connection |
| `message_id` | `string` | ID of the message to archive |

**Returns:**
```json
{
  "success": true
}
```

---

### gmail_trash

Move message to trash.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `string` | Gmail connection |
| `message_id` | `string` | ID of the message to trash |

**Returns:**
```json
{
  "success": true
}
```

---

## Error Handling

All tools may return errors in this format:

```json
{
  "error": "Connection not found: conn_invalid"
}
```

Common error scenarios:

| Error | Cause | Solution |
|-------|-------|----------|
| Connection not found | Invalid connection_id | Use `gmail_list_connections` to find valid IDs |
| Connection inactive | Connection was disconnected | Re-authorize with `gmail_get_auth_url` |
| Token expired | OAuth token needs refresh | Usually auto-refreshed; if persistent, re-authorize |
| Rate limit exceeded | Too many API calls | Wait and retry with backoff |
| Invalid query | Malformed Gmail search query | Check query syntax |
