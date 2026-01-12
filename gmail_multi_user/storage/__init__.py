"""Storage backends for gmail-multi-user-mcp.

This package provides storage backend implementations for persisting
users, connections, and OAuth states.
"""

from gmail_multi_user.storage.base import StorageBackend
from gmail_multi_user.storage.factory import StorageFactory

__all__ = ["StorageBackend", "StorageFactory"]
