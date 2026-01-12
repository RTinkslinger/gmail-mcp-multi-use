# Library API Reference

This document provides a complete reference for the `gmail_multi_user` Python library.

## Installation

```bash
pip install gmail-multi-user-mcp
```

## Quick Start

```python
from gmail_multi_user.service import GmailService
from gmail_multi_user.config import ConfigLoader
from gmail_multi_user.storage.factory import StorageFactory
from gmail_multi_user.tokens.manager import TokenManager
from gmail_multi_user.tokens.encryption import TokenEncryption

# Load configuration
config = ConfigLoader.load()

# Initialize components
storage = StorageFactory.create(config)
await storage.initialize()

encryption = TokenEncryption(config.encryption_key)
token_manager = TokenManager(config=config, storage=storage, encryption=encryption)

# Create service
service = GmailService(config=config, storage=storage, token_manager=token_manager)

# Search emails
result = await service.search(connection_id="conn_123", query="is:unread")
for message in result.messages:
    print(f"{message.subject} from {message.from_.email}")

# Clean up
await service.close()
await storage.close()
```

---

## GmailService

The main service class for all Gmail operations.

```python
from gmail_multi_user.service import GmailService
```

### Constructor

```python
GmailService(
    config: Config,
    storage: StorageBackend,
    token_manager: TokenManager,
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `Config` | Application configuration |
| `storage` | `StorageBackend` | Storage backend instance |
| `token_manager` | `TokenManager` | Token manager for OAuth tokens |

### Methods

#### `search`

Search emails using Gmail query syntax.

```python
async def search(
    connection_id: str,
    query: str,
    max_results: int = 10,
    include_body: bool = False,
    page_token: str | None = None,
) -> SearchResult
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `str` | required | Gmail connection to search |
| `query` | `str` | required | Gmail search query (e.g., "is:unread from:boss") |
| `max_results` | `int` | `10` | Maximum results (1-100) |
| `include_body` | `bool` | `False` | Include message body in results |
| `page_token` | `str \| None` | `None` | Token for pagination |

**Returns:** `SearchResult` with messages list and pagination info.

**Example:**
```python
result = await service.search(
    connection_id="conn_123",
    query="from:boss@company.com is:unread",
    max_results=20,
    include_body=True
)

for msg in result.messages:
    print(f"{msg.subject}: {msg.body_plain[:100]}...")

# Paginate
if result.next_page_token:
    next_page = await service.search(
        connection_id="conn_123",
        query="from:boss@company.com is:unread",
        page_token=result.next_page_token
    )
```

---

#### `get_message`

Get a single email message.

```python
async def get_message(
    connection_id: str,
    message_id: str,
    format: Literal["full", "metadata", "minimal"] = "full",
) -> Message
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `str` | required | Gmail connection |
| `message_id` | `str` | required | ID of the message |
| `format` | `str` | `"full"` | Detail level: "full", "metadata", or "minimal" |

**Returns:** `Message` object.

**Example:**
```python
message = await service.get_message(
    connection_id="conn_123",
    message_id="18abc123def",
    format="full"
)
print(f"Subject: {message.subject}")
print(f"From: {message.from_.name} <{message.from_.email}>")
print(f"Body: {message.body_plain}")
```

---

#### `get_thread`

Get all messages in an email thread.

```python
async def get_thread(
    connection_id: str,
    thread_id: str,
) -> Thread
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `str` | Gmail connection |
| `thread_id` | `str` | ID of the thread |

**Returns:** `Thread` object with all messages.

**Example:**
```python
thread = await service.get_thread(
    connection_id="conn_123",
    thread_id="18abc123def"
)
print(f"Thread: {thread.subject} ({thread.message_count} messages)")
for msg in thread.messages:
    print(f"  - {msg.from_.email}: {msg.snippet}")
```

---

#### `list_labels`

List all labels for a Gmail account.

```python
async def list_labels(connection_id: str) -> list[Label]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `str` | Gmail connection |

**Returns:** List of `Label` objects.

**Example:**
```python
labels = await service.list_labels(connection_id="conn_123")
for label in labels:
    print(f"{label.name}: {label.unread_count} unread")
```

---

#### `get_attachment`

Download an attachment.

```python
async def get_attachment(
    connection_id: str,
    message_id: str,
    attachment_id: str,
) -> AttachmentData
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `str` | Gmail connection |
| `message_id` | `str` | ID of the message |
| `attachment_id` | `str` | ID of the attachment |

**Returns:** `AttachmentData` with filename, mime_type, size, and data bytes.

**Example:**
```python
attachment = await service.get_attachment(
    connection_id="conn_123",
    message_id="18abc123def",
    attachment_id="att_456"
)

# Save to file
with open(attachment.filename, "wb") as f:
    f.write(attachment.data)
```

---

#### `get_profile`

Get Gmail profile information.

```python
async def get_profile(connection_id: str) -> dict
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_id` | `str` | Gmail connection |

**Returns:** Dictionary with email_address, messages_total, threads_total, history_id.

**Example:**
```python
profile = await service.get_profile(connection_id="conn_123")
print(f"Email: {profile['email_address']}")
print(f"Total messages: {profile['messages_total']}")
```

---

#### `send`

Send an email message.

```python
async def send(
    connection_id: str,
    to: list[str],
    subject: str,
    body: str,
    body_html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[AttachmentInput] | None = None,
    thread_id: str | None = None,
    in_reply_to: str | None = None,
    references: str | None = None,
) -> SendResult
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `str` | required | Gmail connection |
| `to` | `list[str]` | required | Recipient email addresses |
| `subject` | `str` | required | Email subject |
| `body` | `str` | required | Plain text body |
| `body_html` | `str \| None` | `None` | Optional HTML body |
| `cc` | `list[str] \| None` | `None` | CC recipients |
| `bcc` | `list[str] \| None` | `None` | BCC recipients |
| `attachments` | `list[AttachmentInput] \| None` | `None` | List of attachments |
| `thread_id` | `str \| None` | `None` | Thread ID for replies |
| `in_reply_to` | `str \| None` | `None` | Message-ID for reply threading |
| `references` | `str \| None` | `None` | References header for threading |

**Returns:** `SendResult` with success, message_id, and thread_id.

**Example:**
```python
from gmail_multi_user.types import AttachmentInput

# Simple email
result = await service.send(
    connection_id="conn_123",
    to=["recipient@example.com"],
    subject="Hello from Python!",
    body="This is a test email.",
)
print(f"Sent! Message ID: {result.message_id}")

# With HTML and attachment
attachment = AttachmentInput(
    filename="report.pdf",
    content=open("report.pdf", "rb").read(),
    mime_type="application/pdf"
)

result = await service.send(
    connection_id="conn_123",
    to=["recipient@example.com"],
    subject="Monthly Report",
    body="Please see the attached report.",
    body_html="<h1>Monthly Report</h1><p>Please see the attached report.</p>",
    attachments=[attachment]
)
```

---

#### `reply`

Reply to an existing message.

```python
async def reply(
    connection_id: str,
    message_id: str,
    body: str,
    body_html: str | None = None,
    reply_all: bool = False,
    attachments: list[AttachmentInput] | None = None,
) -> SendResult
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection_id` | `str` | required | Gmail connection |
| `message_id` | `str` | required | ID of message to reply to |
| `body` | `str` | required | Reply body text |
| `body_html` | `str \| None` | `None` | Optional HTML body |
| `reply_all` | `bool` | `False` | Include all original recipients |
| `attachments` | `list[AttachmentInput] \| None` | `None` | Optional attachments |

**Returns:** `SendResult` with sent message details.

**Example:**
```python
result = await service.reply(
    connection_id="conn_123",
    message_id="18abc123def",
    body="Thanks for your email! I'll look into this.",
    reply_all=True
)
```

---

#### `create_draft`

Create a draft email.

```python
async def create_draft(
    connection_id: str,
    to: list[str],
    subject: str,
    body: str,
    body_html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[AttachmentInput] | None = None,
    thread_id: str | None = None,
) -> DraftResult
```

**Returns:** `DraftResult` with draft_id and message_id.

**Example:**
```python
result = await service.create_draft(
    connection_id="conn_123",
    to=["recipient@example.com"],
    subject="Draft for review",
    body="Please review before sending.",
)
print(f"Draft created: {result.draft_id}")
```

---

#### `send_draft`

Send an existing draft.

```python
async def send_draft(
    connection_id: str,
    draft_id: str,
) -> SendResult
```

**Example:**
```python
result = await service.send_draft(
    connection_id="conn_123",
    draft_id="draft_456"
)
```

---

#### `modify_labels`

Modify labels on a message.

```python
async def modify_labels(
    connection_id: str,
    message_id: str,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
) -> Message
```

**Example:**
```python
# Add "Important" label, remove "INBOX" (archive)
message = await service.modify_labels(
    connection_id="conn_123",
    message_id="18abc123def",
    add_labels=["IMPORTANT"],
    remove_labels=["INBOX"]
)
```

---

#### `archive`

Archive a message (remove from INBOX).

```python
async def archive(connection_id: str, message_id: str) -> Message
```

---

#### `trash`

Move a message to trash.

```python
async def trash(connection_id: str, message_id: str) -> Message
```

---

#### `mark_read` / `mark_unread`

Mark messages as read or unread.

```python
async def mark_read(connection_id: str, message_ids: list[str]) -> None
async def mark_unread(connection_id: str, message_ids: list[str]) -> None
```

**Example:**
```python
await service.mark_read(
    connection_id="conn_123",
    message_ids=["msg_1", "msg_2", "msg_3"]
)
```

---

## Data Types

### Message

```python
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
```

### Contact

```python
@dataclass
class Contact:
    name: str
    email: str
```

### SearchResult

```python
@dataclass
class SearchResult:
    messages: list[Message]
    next_page_token: str | None = None
    total_estimate: int = 0
```

### SendResult

```python
@dataclass
class SendResult:
    success: bool
    message_id: str
    thread_id: str
```

### DraftResult

```python
@dataclass
class DraftResult:
    draft_id: str
    message_id: str
```

### Label

```python
@dataclass
class Label:
    id: str
    name: str
    type: Literal["system", "user"]
    message_count: int | None = None
    unread_count: int | None = None
```

### AttachmentInput

```python
@dataclass
class AttachmentInput:
    filename: str
    content: bytes
    mime_type: str
```

### AttachmentData

```python
@dataclass
class AttachmentData:
    filename: str
    mime_type: str
    size: int
    data: bytes
```

---

## Exceptions

All exceptions inherit from `GmailMCPError`.

| Exception | Description |
|-----------|-------------|
| `ConfigError` | Configuration is invalid or missing |
| `AuthError` | OAuth authentication failed |
| `TokenError` | Token refresh or validation failed |
| `StorageError` | Database operation failed |
| `ConnectionNotFoundError` | Connection ID doesn't exist |
| `ConnectionInactiveError` | Connection is disconnected |
| `GmailAPIError` | Gmail API returned an error |
| `RateLimitError` | Rate limit exceeded |

**Example:**
```python
from gmail_multi_user import (
    ConnectionNotFoundError,
    TokenError,
    GmailAPIError,
)

try:
    result = await service.search(connection_id="invalid", query="is:unread")
except ConnectionNotFoundError:
    print("Connection not found. Please reconnect.")
except TokenError:
    print("Token expired. Re-authorization required.")
except GmailAPIError as e:
    print(f"Gmail API error: {e}")
```

---

## Gmail Query Syntax

The `query` parameter uses Gmail's search syntax:

| Query | Description |
|-------|-------------|
| `is:unread` | Unread messages |
| `is:starred` | Starred messages |
| `from:email@example.com` | From specific sender |
| `to:email@example.com` | To specific recipient |
| `subject:keyword` | Subject contains keyword |
| `has:attachment` | Has attachments |
| `after:2024/01/01` | After date |
| `before:2024/12/31` | Before date |
| `label:work` | Has label "work" |
| `in:inbox` | In inbox |
| `in:sent` | In sent folder |

Combine with AND (space) or OR:
```
from:boss@company.com subject:urgent is:unread
from:alice OR from:bob
```
