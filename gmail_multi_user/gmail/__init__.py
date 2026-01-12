"""Gmail API wrapper for gmail-multi-user-mcp.

This package provides Gmail API operations and MIME parsing.
"""

from gmail_multi_user.gmail.client import GmailAPIClient
from gmail_multi_user.gmail.composer import MessageComposer, guess_mime_type
from gmail_multi_user.gmail.parser import MessageParser, decode_attachment_data

__all__ = [
    "GmailAPIClient",
    "MessageComposer",
    "MessageParser",
    "decode_attachment_data",
    "guess_mime_type",
]
