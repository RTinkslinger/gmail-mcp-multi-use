"""Custom exceptions for gmail-multi-user-mcp.

This module defines the exception hierarchy used throughout the library.
All exceptions inherit from GmailMCPError for easy catching.

Features:
- Structured error codes for programmatic handling
- Suggestions for resolving errors
- Retry information for transient errors
- Serialization to dict for API responses
"""

from __future__ import annotations

from typing import Any

# =============================================================================
# Error Code Constants
# =============================================================================

# Config errors
CONFIG_NOT_FOUND = "CONFIG_001"
CONFIG_INVALID = "CONFIG_002"
CONFIG_MISSING_FIELD = "CONFIG_003"
CONFIG_INVALID_ENCRYPTION_KEY = "CONFIG_004"

# Auth errors
AUTH_INVALID_STATE = "AUTH_001"
AUTH_STATE_EXPIRED = "AUTH_002"
AUTH_OAUTH_FAILED = "AUTH_003"
AUTH_INVALID_CODE = "AUTH_004"

# Token errors
TOKEN_EXPIRED = "TOKEN_001"
TOKEN_REFRESH_FAILED = "TOKEN_002"
TOKEN_REVOKED = "TOKEN_003"
TOKEN_NEEDS_REAUTH = "TOKEN_004"
TOKEN_ENCRYPTION_ERROR = "TOKEN_005"

# Storage errors
STORAGE_CONNECTION_FAILED = "STORAGE_001"
STORAGE_QUERY_FAILED = "STORAGE_002"
STORAGE_NOT_FOUND = "STORAGE_003"

# Connection errors
CONNECTION_NOT_FOUND = "CONN_001"
CONNECTION_INACTIVE = "CONN_002"

# Gmail API errors
GMAIL_API_ERROR = "GMAIL_001"
GMAIL_PERMISSION_DENIED = "GMAIL_002"
GMAIL_NOT_FOUND = "GMAIL_003"
GMAIL_INVALID_REQUEST = "GMAIL_004"
GMAIL_RATE_LIMIT = "GMAIL_005"

# Retry configuration
RETRIABLE_CODES = {
    TOKEN_REFRESH_FAILED,
    STORAGE_CONNECTION_FAILED,
    GMAIL_RATE_LIMIT,
}


class GmailMCPError(Exception):
    """Base exception for gmail-multi-user-mcp.

    All library exceptions inherit from this class, making it easy to catch
    any library-related error.

    Attributes:
        code: A short string identifying the error type.
        message: Human-readable error description.
        details: Optional dictionary with additional context.
        suggestion: Suggested action to resolve the error.
    """

    code: str = "unknown_error"
    message: str = "An unknown error occurred"
    suggestion: str = "Check the logs for more details."

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Override the default message.
            code: Override the default code.
            details: Additional context about the error.
            suggestion: Suggested action to resolve the error.
        """
        self.message = message or self.__class__.message
        self.code = code or self.__class__.code
        self.details = details or {}
        self.suggestion = suggestion or self.__class__.suggestion
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details if self.details else None,
                "suggestion": self.suggestion,
            }
        }

    def is_retriable(self) -> bool:
        """Check if this error is retriable."""
        return self.code in RETRIABLE_CODES

    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return (
            f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"
        )


class ConfigError(GmailMCPError):
    """Configuration-related errors.

    Raised when configuration is missing, invalid, or cannot be loaded.

    Error codes:
        - CONFIG_001: No configuration file found
        - CONFIG_002: Configuration file has syntax errors
        - CONFIG_003: Required configuration field is missing
        - CONFIG_004: Invalid encryption key format
    """

    code = CONFIG_NOT_FOUND
    message = "Configuration error"
    suggestion = (
        "Run 'gmail-mcp init' to create a configuration file, or set "
        "GMAIL_MCP_CONFIG environment variable to point to an existing config."
    )


class AuthError(GmailMCPError):
    """Authentication-related errors.

    Raised during OAuth flows when authentication fails.

    Error codes:
        - AUTH_001: OAuth state parameter is invalid
        - AUTH_002: OAuth state has expired (>10 minutes)
        - AUTH_003: OAuth flow failed at Google
        - AUTH_004: Invalid authorization code
    """

    code = AUTH_OAUTH_FAILED
    message = "Authentication error"
    suggestion = (
        "The OAuth flow failed. Try generating a new authorization URL with "
        "gmail_get_auth_url() and completing the flow within 10 minutes."
    )


class TokenError(GmailMCPError):
    """Token-related errors.

    Raised when token operations fail.

    Error codes:
        - TOKEN_001: Access token has expired and refresh failed
        - TOKEN_002: Token refresh operation failed
        - TOKEN_003: User has revoked access
        - TOKEN_004: User must re-authenticate
        - TOKEN_005: Token encryption/decryption failed
    """

    code = TOKEN_EXPIRED
    message = "Token error"
    suggestion = (
        "The OAuth token is invalid or expired. Use gmail_get_auth_url() to "
        "generate a new authorization URL and reconnect the Gmail account."
    )


class StorageError(GmailMCPError):
    """Storage-related errors.

    Raised when database operations fail.

    Error codes:
        - STORAGE_001: Could not connect to storage
        - STORAGE_002: Database query failed
        - STORAGE_003: Record not found in storage
    """

    code = STORAGE_CONNECTION_FAILED
    message = "Storage error"
    suggestion = (
        "Check your database configuration. For SQLite, ensure the path is "
        "writable. For Supabase, verify the URL and service role key."
    )


class ConnectionNotFoundError(GmailMCPError):
    """Connection not found error.

    Raised when a requested Gmail connection does not exist.
    """

    code = CONNECTION_NOT_FOUND
    message = "Gmail connection not found"
    suggestion = (
        "The connection_id is invalid. Use gmail_list_connections() to see "
        "available connections, or connect a Gmail account with gmail_get_auth_url()."
    )


class ConnectionInactiveError(GmailMCPError):
    """Connection inactive error.

    Raised when attempting to use a deactivated connection.
    """

    code = CONNECTION_INACTIVE
    message = "Gmail connection is inactive"
    suggestion = (
        "This connection has been deactivated or disconnected. Reconnect the "
        "Gmail account using gmail_get_auth_url() to generate a new OAuth URL."
    )


class GmailAPIError(GmailMCPError):
    """Gmail API errors.

    Raised when Gmail API calls fail.

    Error codes:
        - GMAIL_001: General Gmail API error
        - GMAIL_002: Insufficient OAuth scopes (permission denied)
        - GMAIL_003: Requested resource not found
        - GMAIL_004: Malformed request to Gmail API
        - GMAIL_005: Rate limit exceeded
    """

    code = GMAIL_API_ERROR
    message = "Gmail API error"
    suggestion = (
        "The Gmail API request failed. Check the error details for more "
        "information. If this is a permission error, you may need to reconnect "
        "with additional OAuth scopes."
    )


class RateLimitError(GmailMCPError):
    """Rate limit errors.

    Raised when Gmail API rate limits are exceeded.

    Attributes:
        retry_after: Suggested seconds to wait before retrying.
    """

    code = GMAIL_RATE_LIMIT
    message = "Rate limit exceeded"
    suggestion = (
        "Gmail API rate limit exceeded. Wait before retrying. See retry_after "
        "in the error details for the recommended wait time."
    )

    def __init__(
        self,
        message: str | None = None,
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Initialize rate limit exception.

        Args:
            message: Override the default message.
            retry_after: Seconds to wait before retrying.
            details: Additional context about the error.
            suggestion: Suggested action to resolve the error.
        """
        super().__init__(message=message, details=details, suggestion=suggestion)
        self.retry_after = retry_after
        if retry_after is not None:
            self.details["retry_after"] = retry_after

    def is_retriable(self) -> bool:
        """Rate limit errors are always retriable."""
        return True


# =============================================================================
# Helper Functions
# =============================================================================


def create_config_error(
    code: str,
    message: str,
    field: str | None = None,
    suggestion: str | None = None,
) -> ConfigError:
    """Create a ConfigError with appropriate context.

    Args:
        code: Error code (e.g., CONFIG_NOT_FOUND).
        message: Error message.
        field: Configuration field that caused the error.
        suggestion: Override the default suggestion.

    Returns:
        ConfigError with populated details.
    """
    details: dict[str, Any] = {}
    if field:
        details["field"] = field

    return ConfigError(
        message=message,
        code=code,
        details=details if details else None,
        suggestion=suggestion,
    )


def create_auth_error(
    code: str,
    message: str,
    state: str | None = None,
    suggestion: str | None = None,
) -> AuthError:
    """Create an AuthError with appropriate context.

    Args:
        code: Error code (e.g., AUTH_STATE_EXPIRED).
        message: Error message.
        state: OAuth state that caused the error.
        suggestion: Override the default suggestion.

    Returns:
        AuthError with populated details.
    """
    details: dict[str, Any] = {}
    if state:
        details["state"] = state

    return AuthError(
        message=message,
        code=code,
        details=details if details else None,
        suggestion=suggestion,
    )


def create_gmail_api_error(
    code: str,
    message: str,
    status_code: int | None = None,
    gmail_error: str | None = None,
    suggestion: str | None = None,
) -> GmailAPIError:
    """Create a GmailAPIError with appropriate context.

    Args:
        code: Error code (e.g., GMAIL_PERMISSION_DENIED).
        message: Error message.
        status_code: HTTP status code from Gmail API.
        gmail_error: Error message from Gmail API.
        suggestion: Override the default suggestion.

    Returns:
        GmailAPIError with populated details.
    """
    details: dict[str, Any] = {}
    if status_code:
        details["status_code"] = status_code
    if gmail_error:
        details["gmail_error"] = gmail_error

    return GmailAPIError(
        message=message,
        code=code,
        details=details if details else None,
        suggestion=suggestion,
    )
