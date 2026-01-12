# API Design

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [Library API](#1-library-api)
2. [MCP Tool Schemas](#2-mcp-tool-schemas)
3. [MCP Resource Schemas](#3-mcp-resource-schemas)
4. [Data Types](#4-data-types)
5. [Error Handling](#5-error-handling)

---

## 1. Library API

### 1.1 Client Classes

```python
# gmail_multi_user/__init__.py

from gmail_multi_user.client import GmailClient, AsyncGmailClient
from gmail_multi_user.config import Config, ConfigLoader
from gmail_multi_user.types import (
    AuthUrlResult,
    CallbackResult,
    Connection,
    ConnectionStatus,
    Message,
    Thread,
    SearchResult,
    SendResult,
    DraftResult,
    Label,
    Attachment,
    AttachmentData,
    AttachmentInput,
)
from gmail_multi_user.exceptions import (
    GmailMCPError,
    ConfigError,
    AuthError,
    TokenError,
    ConnectionError,
    GmailAPIError,
    RateLimitError,
)

__all__ = [
    "GmailClient",
    "AsyncGmailClient",
    "Config",
    "ConfigLoader",
    # Types
    "AuthUrlResult",
    "CallbackResult",
    "Connection",
    "ConnectionStatus",
    "Message",
    "Thread",
    "SearchResult",
    "SendResult",
    "DraftResult",
    "Label",
    "Attachment",
    "AttachmentData",
    "AttachmentInput",
    # Exceptions
    "GmailMCPError",
    "ConfigError",
    "AuthError",
    "TokenError",
    "ConnectionError",
    "GmailAPIError",
    "RateLimitError",
]
```

### 1.2 GmailClient (Sync)

```python
class GmailClient:
    """
    Synchronous Gmail client.

    Wraps AsyncGmailClient for use in synchronous code.
    All methods block until completion.

    Example:
        client = GmailClient()
        messages = client.search(connection_id="conn_123", query="is:unread")
    """

    def __init__(self, config: Config | None = None) -> None:
        """
        Initialize the Gmail client.

        Args:
            config: Optional configuration. If not provided, loads from
                   environment/file automatically.

        Raises:
            ConfigError: If configuration is invalid or missing.
        """

    # === OAuth Methods ===

    def get_auth_url(
        self,
        user_id: str,
        scopes: list[str] | None = None,
        redirect_uri: str | None = None,
    ) -> AuthUrlResult:
        """
        Generate OAuth URL for user authentication.

        Args:
            user_id: Your application's user identifier.
            scopes: Gmail scopes to request. Defaults to ["gmail.readonly", "gmail.send"].
            redirect_uri: Override the configured redirect URI.

        Returns:
            AuthUrlResult with auth_url, state, and expires_at.

        Example:
            result = client.get_auth_url(user_id="user_123")
            redirect_user_to(result.auth_url)
        """

    def handle_oauth_callback(self, code: str, state: str) -> CallbackResult:
        """
        Process OAuth callback after user authorization.

        Args:
            code: Authorization code from Google callback.
            state: State parameter for CSRF validation.

        Returns:
            CallbackResult with success status and connection details.

        Raises:
            AuthError: If state is invalid or expired.
        """

    def list_connections(
        self,
        user_id: str | None = None,
        include_inactive: bool = False,
    ) -> list[Connection]:
        """
        List Gmail connections.

        Args:
            user_id: Filter by user ID. If None, returns all connections.
            include_inactive: Include revoked/expired connections.

        Returns:
            List of Connection objects.
        """

    def check_connection(self, connection_id: str) -> ConnectionStatus:
        """
        Check if a connection is valid and working.

        Args:
            connection_id: The connection to check.

        Returns:
            ConnectionStatus with validity and details.
        """

    def disconnect(
        self,
        connection_id: str,
        revoke_google_access: bool = True,
    ) -> bool:
        """
        Disconnect a Gmail account.

        Args:
            connection_id: The connection to disconnect.
            revoke_google_access: Also revoke access at Google.

        Returns:
            True if disconnected successfully.
        """

    # === Read Methods ===

    def search(
        self,
        connection_id: str,
        query: str,
        max_results: int = 10,
        include_body: bool = False,
        page_token: str | None = None,
    ) -> SearchResult:
        """
        Search emails using Gmail query syntax.

        Args:
            connection_id: Gmail connection to search.
            query: Gmail search query (e.g., "is:unread from:boss@company.com").
            max_results: Maximum results (1-100).
            include_body: Include message body in results.
            page_token: Token for pagination.

        Returns:
            SearchResult with messages and pagination info.

        Example:
            result = client.search(
                connection_id="conn_123",
                query="is:unread newer_than:7d"
            )
            for msg in result.messages:
                print(f"{msg.subject} from {msg.from_.email}")
        """

    def get_message(
        self,
        connection_id: str,
        message_id: str,
        format: Literal["full", "metadata", "minimal"] = "full",
    ) -> Message:
        """
        Get a single email message.

        Args:
            connection_id: Gmail connection.
            message_id: ID of the message.
            format: Detail level ("full", "metadata", "minimal").

        Returns:
            Message object with full details.
        """

    def get_thread(self, connection_id: str, thread_id: str) -> Thread:
        """
        Get all messages in an email thread.

        Args:
            connection_id: Gmail connection.
            thread_id: ID of the thread.

        Returns:
            Thread object with all messages.
        """

    def list_labels(self, connection_id: str) -> list[Label]:
        """
        List all labels for a Gmail account.

        Args:
            connection_id: Gmail connection.

        Returns:
            List of Label objects.
        """

    def get_attachment(
        self,
        connection_id: str,
        message_id: str,
        attachment_id: str,
    ) -> AttachmentData:
        """
        Download an attachment.

        Args:
            connection_id: Gmail connection.
            message_id: ID of the message.
            attachment_id: ID of the attachment.

        Returns:
            AttachmentData with filename, mime_type, and data bytes.
        """

    # === Write Methods ===

    def send(
        self,
        connection_id: str,
        to: list[str],
        subject: str,
        body: str,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to_message_id: str | None = None,
        attachments: list[AttachmentInput] | None = None,
    ) -> SendResult:
        """
        Send an email.

        Args:
            connection_id: Gmail connection to send from.
            to: Recipient email addresses.
            subject: Email subject.
            body: Plain text body.
            body_html: Optional HTML body.
            cc: CC recipients.
            bcc: BCC recipients.
            reply_to_message_id: Message ID if this is a reply.
            attachments: List of attachments.

        Returns:
            SendResult with message_id and thread_id.

        Example:
            result = client.send(
                connection_id="conn_123",
                to=["bob@example.com"],
                subject="Hello",
                body="Hi Bob!"
            )
        """

    def create_draft(
        self,
        connection_id: str,
        to: list[str],
        subject: str,
        body: str,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to_message_id: str | None = None,
    ) -> DraftResult:
        """
        Create a draft email.

        Args:
            Same as send() except no attachments.

        Returns:
            DraftResult with draft_id and message_id.
        """

    def send_draft(self, connection_id: str, draft_id: str) -> SendResult:
        """Send an existing draft."""

    def delete_draft(self, connection_id: str, draft_id: str) -> bool:
        """Delete a draft."""

    # === Management Methods ===

    def modify_labels(
        self,
        connection_id: str,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> list[str]:
        """
        Add or remove labels from a message.

        Returns:
            Current labels after modification.
        """

    def archive(self, connection_id: str, message_id: str) -> bool:
        """Archive a message (remove from inbox)."""

    def trash(self, connection_id: str, message_id: str) -> bool:
        """Move message to trash."""

    def untrash(self, connection_id: str, message_id: str) -> bool:
        """Remove message from trash."""

    def mark_read(self, connection_id: str, message_ids: list[str]) -> bool:
        """Mark messages as read."""

    def mark_unread(self, connection_id: str, message_ids: list[str]) -> bool:
        """Mark messages as unread."""

    # === Batch Methods ===

    def batch_get_messages(
        self,
        connection_id: str,
        message_ids: list[str],
        format: Literal["full", "metadata", "minimal"] = "metadata",
    ) -> list[Message]:
        """Get multiple messages efficiently."""

    def batch_modify_labels(
        self,
        connection_id: str,
        message_ids: list[str],
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> bool:
        """Modify labels on multiple messages."""
```

### 1.3 AsyncGmailClient

Same interface as GmailClient but all methods are `async`:

```python
class AsyncGmailClient:
    """
    Asynchronous Gmail client.

    Native async implementation for use with asyncio.

    Example:
        async def main():
            client = AsyncGmailClient()
            messages = await client.search(connection_id="conn_123", query="is:unread")
    """

    async def get_auth_url(...) -> AuthUrlResult: ...
    async def handle_oauth_callback(...) -> CallbackResult: ...
    async def search(...) -> SearchResult: ...
    # ... all methods are async
```

---

## 2. MCP Tool Schemas

### 2.1 Setup Tools

#### gmail_check_setup

```json
{
  "name": "gmail_check_setup",
  "description": "Check if gmail-multi-user-mcp is properly configured. Returns status of config file, database, Google OAuth, and encryption key.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "config_found": {"type": "boolean"},
      "config_path": {"type": ["string", "null"]},
      "database_connected": {"type": "boolean"},
      "database_type": {"type": "string", "enum": ["sqlite", "supabase"]},
      "google_oauth_configured": {"type": "boolean"},
      "encryption_key_set": {"type": "boolean"},
      "issues": {"type": "array", "items": {"type": "string"}},
      "ready": {"type": "boolean"}
    }
  }
}
```

#### gmail_init_config

```json
{
  "name": "gmail_init_config",
  "description": "Create a gmail_config.yaml file with the provided settings.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "database_type": {
        "type": "string",
        "enum": ["sqlite", "supabase"],
        "description": "Storage backend type"
      },
      "sqlite_path": {
        "type": "string",
        "description": "Path to SQLite database file (required if database_type is sqlite)"
      },
      "supabase_url": {
        "type": "string",
        "description": "Supabase project URL (required if database_type is supabase)"
      },
      "supabase_key": {
        "type": "string",
        "description": "Supabase service role key (required if database_type is supabase)"
      },
      "google_client_id": {
        "type": "string",
        "description": "Google OAuth client ID"
      },
      "google_client_secret": {
        "type": "string",
        "description": "Google OAuth client secret"
      },
      "redirect_uri": {
        "type": "string",
        "default": "http://localhost:8000/oauth/callback",
        "description": "OAuth redirect URI"
      },
      "generate_encryption_key": {
        "type": "boolean",
        "default": true,
        "description": "Generate a new encryption key"
      }
    },
    "required": ["database_type"]
  }
}
```

### 2.2 OAuth Tools

#### gmail_get_auth_url

```json
{
  "name": "gmail_get_auth_url",
  "description": "Generate an OAuth URL for a user to connect their Gmail account.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "Your application's identifier for this user"
      },
      "scopes": {
        "type": "array",
        "items": {"type": "string"},
        "default": ["gmail.readonly", "gmail.send"],
        "description": "Gmail scopes to request"
      },
      "redirect_uri": {
        "type": "string",
        "description": "Override the default redirect URI"
      }
    },
    "required": ["user_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "auth_url": {"type": "string", "description": "URL to redirect user to"},
      "state": {"type": "string", "description": "State parameter for CSRF protection"},
      "expires_in": {"type": "integer", "description": "Seconds until URL expires"}
    }
  }
}
```

#### gmail_list_connections

```json
{
  "name": "gmail_list_connections",
  "description": "List Gmail connections for a user or all users.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "Filter by user ID (optional, omit for all)"
      },
      "include_inactive": {
        "type": "boolean",
        "default": false,
        "description": "Include disconnected/expired connections"
      }
    }
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "connections": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {"type": "string"},
            "user_id": {"type": "string"},
            "gmail_address": {"type": "string"},
            "scopes": {"type": "array", "items": {"type": "string"}},
            "is_active": {"type": "boolean"},
            "created_at": {"type": "string", "format": "date-time"},
            "last_used_at": {"type": ["string", "null"], "format": "date-time"}
          }
        }
      }
    }
  }
}
```

### 2.3 Gmail Operation Tools

#### gmail_search

```json
{
  "name": "gmail_search",
  "description": "Search emails using Gmail query syntax. Common queries: 'is:unread', 'from:alice@example.com', 'subject:invoice', 'has:attachment', 'newer_than:7d'.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "connection_id": {
        "type": "string",
        "description": "Gmail connection to search"
      },
      "query": {
        "type": "string",
        "description": "Gmail search query"
      },
      "max_results": {
        "type": "integer",
        "default": 10,
        "minimum": 1,
        "maximum": 100,
        "description": "Maximum number of results"
      },
      "include_body": {
        "type": "boolean",
        "default": false,
        "description": "Include message body in results (slower)"
      }
    },
    "required": ["connection_id", "query"]
  }
}
```

#### gmail_send

```json
{
  "name": "gmail_send",
  "description": "Send an email from the connected Gmail account.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "connection_id": {
        "type": "string",
        "description": "Gmail connection to send from"
      },
      "to": {
        "type": "array",
        "items": {"type": "string", "format": "email"},
        "description": "Recipient email addresses"
      },
      "subject": {
        "type": "string",
        "description": "Email subject"
      },
      "body": {
        "type": "string",
        "description": "Plain text email body"
      },
      "body_html": {
        "type": "string",
        "description": "Optional HTML email body"
      },
      "cc": {
        "type": "array",
        "items": {"type": "string", "format": "email"},
        "description": "CC recipients"
      },
      "bcc": {
        "type": "array",
        "items": {"type": "string", "format": "email"},
        "description": "BCC recipients"
      },
      "reply_to_message_id": {
        "type": "string",
        "description": "Message ID if this is a reply"
      }
    },
    "required": ["connection_id", "to", "subject", "body"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": {"type": "boolean"},
      "message_id": {"type": "string"},
      "thread_id": {"type": "string"}
    }
  }
}
```

---

## 3. MCP Resource Schemas

### 3.1 Configuration Resources

#### config://status

```json
{
  "uri": "config://status",
  "name": "Configuration Status",
  "description": "Current configuration status and health",
  "mimeType": "application/json",
  "schema": {
    "type": "object",
    "properties": {
      "configured": {"type": "boolean"},
      "config_path": {"type": ["string", "null"]},
      "database": {
        "type": "object",
        "properties": {
          "type": {"type": "string"},
          "connected": {"type": "boolean"},
          "path_or_url": {"type": "string"}
        }
      },
      "google_oauth": {
        "type": "object",
        "properties": {
          "configured": {"type": "boolean"},
          "client_id_set": {"type": "boolean"},
          "redirect_uri": {"type": "string"}
        }
      },
      "encryption": {
        "type": "object",
        "properties": {
          "key_set": {"type": "boolean"}
        }
      }
    }
  }
}
```

### 3.2 User Resources

#### users://list

```json
{
  "uri": "users://list",
  "name": "User List",
  "description": "All users with Gmail connections",
  "mimeType": "application/json"
}
```

#### users://{user_id}/connections

```json
{
  "uriTemplate": "users://{user_id}/connections",
  "name": "User Connections",
  "description": "Gmail connections for a specific user",
  "mimeType": "application/json"
}
```

### 3.3 Gmail Resources

#### gmail://{connection_id}/profile

```json
{
  "uriTemplate": "gmail://{connection_id}/profile",
  "name": "Gmail Profile",
  "description": "Profile info and quota for a Gmail connection",
  "mimeType": "application/json",
  "schema": {
    "type": "object",
    "properties": {
      "email_address": {"type": "string"},
      "messages_total": {"type": "integer"},
      "threads_total": {"type": "integer"},
      "history_id": {"type": "string"}
    }
  }
}
```

---

## 4. Data Types

### 4.1 Result Types

```python
@dataclass
class AuthUrlResult:
    auth_url: str
    state: str
    expires_at: datetime

@dataclass
class CallbackResult:
    success: bool
    connection_id: str | None = None
    user_id: str | None = None
    gmail_address: str | None = None
    error: str | None = None

@dataclass
class ConnectionStatus:
    valid: bool
    gmail_address: str
    scopes: list[str]
    token_expires_in: int | None = None
    needs_reauth: bool = False
    error: str | None = None

@dataclass
class SearchResult:
    messages: list[Message]
    next_page_token: str | None = None
    total_estimate: int = 0

@dataclass
class SendResult:
    success: bool
    message_id: str
    thread_id: str

@dataclass
class DraftResult:
    draft_id: str
    message_id: str
```

### 4.2 Domain Types

```python
@dataclass
class Contact:
    name: str
    email: str

@dataclass
class Message:
    id: str
    thread_id: str
    subject: str
    from_: Contact
    to: list[Contact]
    cc: list[Contact]
    bcc: list[Contact]
    date: datetime
    snippet: str
    body_plain: str
    body_html: str | None
    labels: list[str]
    attachments: list[Attachment]
    has_attachments: bool

@dataclass
class Thread:
    id: str
    subject: str
    message_count: int
    messages: list[Message]

@dataclass
class Label:
    id: str
    name: str
    type: Literal["system", "user"]
    message_count: int | None = None
    unread_count: int | None = None

@dataclass
class Attachment:
    id: str
    filename: str
    mime_type: str
    size: int

@dataclass
class AttachmentData:
    filename: str
    mime_type: str
    size: int
    data: bytes

@dataclass
class AttachmentInput:
    filename: str
    content: bytes
    mime_type: str
```

---

## 5. Error Handling

### 5.1 Exception Hierarchy

```python
class GmailMCPError(Exception):
    """Base exception for gmail-multi-user-mcp."""
    code: str
    message: str
    details: dict | None = None

class ConfigError(GmailMCPError):
    """Configuration-related errors."""
    # Codes: config_not_found, config_invalid, missing_field

class AuthError(GmailMCPError):
    """Authentication-related errors."""
    # Codes: invalid_state, state_expired, oauth_failed

class TokenError(GmailMCPError):
    """Token-related errors."""
    # Codes: token_expired, refresh_failed, token_revoked, needs_reauth

class ConnectionError(GmailMCPError):
    """Connection-related errors."""
    # Codes: connection_not_found, connection_inactive

class GmailAPIError(GmailMCPError):
    """Gmail API errors."""
    # Codes: api_error, permission_denied, not_found

class RateLimitError(GmailMCPError):
    """Rate limit errors."""
    retry_after: int | None = None
    # Codes: rate_limit_exceeded
```

### 5.2 Error Response Format (MCP)

```json
{
  "error": {
    "code": "token_expired",
    "message": "Access token has expired and refresh failed",
    "details": {
      "connection_id": "conn_123",
      "needs_reauth": true
    }
  }
}
```

### 5.3 Error Codes Reference

| Code | Exception | Description | Resolution |
|------|-----------|-------------|------------|
| `config_not_found` | ConfigError | No config file found | Create gmail_config.yaml |
| `config_invalid` | ConfigError | Config file has errors | Fix syntax/values |
| `missing_field` | ConfigError | Required field missing | Add missing field |
| `invalid_state` | AuthError | OAuth state invalid | Restart OAuth flow |
| `state_expired` | AuthError | OAuth state expired | Restart OAuth flow |
| `token_expired` | TokenError | Token refresh failed | User must re-auth |
| `token_revoked` | TokenError | User revoked access | User must re-auth |
| `connection_not_found` | ConnectionError | Connection ID invalid | Check connection_id |
| `rate_limit_exceeded` | RateLimitError | Too many requests | Wait and retry |
| `permission_denied` | GmailAPIError | Scope not granted | Request more scopes |
