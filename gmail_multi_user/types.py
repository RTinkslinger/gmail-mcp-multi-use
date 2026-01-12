"""Data types for gmail-multi-user-mcp.

This module defines all the dataclasses used throughout the library
for type-safe data handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


# =============================================================================
# Core Entity Types (stored in database)
# =============================================================================


@dataclass
class User:
    """Represents a user in the system.

    Users are identified by their external_user_id, which is the ID
    from the developer's application.
    """

    id: str
    external_user_id: str
    email: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class Connection:
    """Represents a Gmail account connection.

    A connection links a user to their Gmail account with encrypted OAuth tokens.
    """

    id: str
    user_id: str
    gmail_address: str
    access_token_encrypted: str
    refresh_token_encrypted: str
    token_expires_at: datetime
    scopes: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None


@dataclass
class OAuthState:
    """Represents an OAuth flow state for CSRF protection.

    OAuth states are temporary and expire after 10 minutes.
    """

    id: str
    state: str
    user_id: str
    scopes: list[str]
    redirect_uri: str
    code_verifier: str
    expires_at: datetime
    created_at: datetime

    @property
    def is_expired(self) -> bool:
        """Check if the state has expired."""
        return datetime.utcnow() > self.expires_at


# =============================================================================
# OAuth Result Types
# =============================================================================


@dataclass
class AuthUrlResult:
    """Result from generating an OAuth URL."""

    auth_url: str
    state: str
    expires_at: datetime


@dataclass
class CallbackResult:
    """Result from handling an OAuth callback."""

    success: bool
    connection_id: str | None = None
    user_id: str | None = None
    gmail_address: str | None = None
    error: str | None = None


@dataclass
class ConnectionStatus:
    """Status of a Gmail connection."""

    valid: bool
    gmail_address: str
    scopes: list[str]
    token_expires_in: int | None = None
    needs_reauth: bool = False
    error: str | None = None


# =============================================================================
# Gmail Domain Types
# =============================================================================


@dataclass
class Contact:
    """Represents an email contact (sender or recipient)."""

    name: str
    email: str

    @classmethod
    def from_header(cls, header: str) -> Contact:
        """Parse a contact from an email header string.

        Args:
            header: Email header like "John Doe <john@example.com>" or "john@example.com"

        Returns:
            Contact with parsed name and email.
        """
        import re

        # Try to match "Name <email>" format
        match = re.match(r'^"?([^"<]*)"?\s*<([^>]+)>$', header.strip())
        if match:
            return cls(name=match.group(1).strip(), email=match.group(2).strip())

        # Fall back to just email
        email = header.strip().strip("<>")
        return cls(name="", email=email)


@dataclass
class Attachment:
    """Metadata about an email attachment."""

    id: str
    filename: str
    mime_type: str
    size: int


@dataclass
class AttachmentData:
    """Full attachment data including content."""

    filename: str
    mime_type: str
    size: int
    data: bytes


@dataclass
class AttachmentInput:
    """Input for attaching a file to an email."""

    filename: str
    content: bytes
    mime_type: str


@dataclass
class Message:
    """Represents an email message."""

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
    """Represents an email thread (conversation)."""

    id: str
    subject: str
    message_count: int
    messages: list[Message]


@dataclass
class Label:
    """Represents a Gmail label."""

    id: str
    name: str
    type: Literal["system", "user"]
    message_count: int | None = None
    unread_count: int | None = None


# =============================================================================
# Operation Result Types
# =============================================================================


@dataclass
class SearchResult:
    """Result from searching emails."""

    messages: list[Message]
    next_page_token: str | None = None
    total_estimate: int = 0


@dataclass
class SendResult:
    """Result from sending an email."""

    success: bool
    message_id: str
    thread_id: str


@dataclass
class DraftResult:
    """Result from creating a draft."""

    draft_id: str
    message_id: str


# =============================================================================
# Configuration Types
# =============================================================================


@dataclass
class SetupStatus:
    """Status of the system setup."""

    config_found: bool
    config_path: str | None
    database_connected: bool
    database_type: str
    google_oauth_configured: bool
    encryption_key_set: bool
    issues: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        """Check if the system is ready to use."""
        return (
            self.config_found
            and self.database_connected
            and self.google_oauth_configured
            and self.encryption_key_set
            and len(self.issues) == 0
        )
