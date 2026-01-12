"""gmail-multi-user-mcp: Multi-user Gmail integration library and MCP server.

This package provides a simple way to add Gmail integration to your
AI agents and consumer applications.

Example:
    from gmail_multi_user import GmailClient

    client = GmailClient()
    messages = client.search(connection_id="conn_123", query="is:unread")
"""

from gmail_multi_user.config import Config, ConfigLoader, ValidationIssue, ValidationResult
from gmail_multi_user.logging import (
    LogContext,
    configure_logging,
    get_logger,
)
from gmail_multi_user.exceptions import (
    # Exception classes
    AuthError,
    ConfigError,
    ConnectionInactiveError,
    ConnectionNotFoundError,
    GmailAPIError,
    GmailMCPError,
    RateLimitError,
    StorageError,
    TokenError,
    # Error code constants
    AUTH_INVALID_CODE,
    AUTH_INVALID_STATE,
    AUTH_OAUTH_FAILED,
    AUTH_STATE_EXPIRED,
    CONFIG_INVALID,
    CONFIG_INVALID_ENCRYPTION_KEY,
    CONFIG_MISSING_FIELD,
    CONFIG_NOT_FOUND,
    CONNECTION_INACTIVE,
    CONNECTION_NOT_FOUND,
    GMAIL_API_ERROR,
    GMAIL_INVALID_REQUEST,
    GMAIL_NOT_FOUND,
    GMAIL_PERMISSION_DENIED,
    GMAIL_RATE_LIMIT,
    STORAGE_CONNECTION_FAILED,
    STORAGE_NOT_FOUND,
    STORAGE_QUERY_FAILED,
    TOKEN_ENCRYPTION_ERROR,
    TOKEN_EXPIRED,
    TOKEN_NEEDS_REAUTH,
    TOKEN_REFRESH_FAILED,
    TOKEN_REVOKED,
    # Helper functions
    create_auth_error,
    create_config_error,
    create_gmail_api_error,
)
from gmail_multi_user.types import (
    Attachment,
    AttachmentData,
    AttachmentInput,
    AuthUrlResult,
    CallbackResult,
    Connection,
    ConnectionStatus,
    Contact,
    DraftResult,
    Label,
    Message,
    OAuthState,
    SearchResult,
    SendResult,
    SetupStatus,
    Thread,
    User,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Config
    "Config",
    "ConfigLoader",
    "ValidationIssue",
    "ValidationResult",
    # Logging
    "LogContext",
    "configure_logging",
    "get_logger",
    # Types
    "Attachment",
    "AttachmentData",
    "AttachmentInput",
    "AuthUrlResult",
    "CallbackResult",
    "Connection",
    "ConnectionStatus",
    "Contact",
    "DraftResult",
    "Label",
    "Message",
    "OAuthState",
    "SearchResult",
    "SendResult",
    "SetupStatus",
    "Thread",
    "User",
    # Exceptions
    "GmailMCPError",
    "ConfigError",
    "AuthError",
    "TokenError",
    "StorageError",
    "ConnectionNotFoundError",
    "ConnectionInactiveError",
    "GmailAPIError",
    "RateLimitError",
    # Error codes
    "AUTH_INVALID_CODE",
    "AUTH_INVALID_STATE",
    "AUTH_OAUTH_FAILED",
    "AUTH_STATE_EXPIRED",
    "CONFIG_INVALID",
    "CONFIG_INVALID_ENCRYPTION_KEY",
    "CONFIG_MISSING_FIELD",
    "CONFIG_NOT_FOUND",
    "CONNECTION_INACTIVE",
    "CONNECTION_NOT_FOUND",
    "GMAIL_API_ERROR",
    "GMAIL_INVALID_REQUEST",
    "GMAIL_NOT_FOUND",
    "GMAIL_PERMISSION_DENIED",
    "GMAIL_RATE_LIMIT",
    "STORAGE_CONNECTION_FAILED",
    "STORAGE_NOT_FOUND",
    "STORAGE_QUERY_FAILED",
    "TOKEN_ENCRYPTION_ERROR",
    "TOKEN_EXPIRED",
    "TOKEN_NEEDS_REAUTH",
    "TOKEN_REFRESH_FAILED",
    "TOKEN_REVOKED",
    # Error helpers
    "create_auth_error",
    "create_config_error",
    "create_gmail_api_error",
]
