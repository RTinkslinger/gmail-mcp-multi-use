"""Storage backend factory.

This module provides a factory for creating storage backend instances
based on configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gmail_multi_user.exceptions import ConfigError
from gmail_multi_user.storage.base import StorageBackend

if TYPE_CHECKING:
    from gmail_multi_user.config import Config


class StorageFactory:
    """Factory for creating storage backend instances."""

    @staticmethod
    def create(config: Config) -> StorageBackend:
        """Create a storage backend based on configuration.

        Args:
            config: The application configuration.

        Returns:
            A StorageBackend instance.

        Raises:
            ConfigError: If the storage type is unknown or misconfigured.
        """
        storage_type = config.storage.type

        if storage_type == "sqlite":
            from gmail_multi_user.storage.sqlite import SQLiteBackend

            if config.storage.sqlite is None:
                raise ConfigError(
                    message="SQLite configuration is required when storage type is 'sqlite'",
                    code="missing_field",
                    details={"field": "storage.sqlite"},
                )
            return SQLiteBackend(config.storage.sqlite.path)

        elif storage_type == "supabase":
            from gmail_multi_user.storage.supabase import SupabaseBackend

            if config.storage.supabase is None:
                raise ConfigError(
                    message="Supabase configuration is required when storage type is 'supabase'",
                    code="missing_field",
                    details={"field": "storage.supabase"},
                )
            return SupabaseBackend(
                supabase_url=config.storage.supabase.url,
                supabase_key=config.storage.supabase.key,
            )

        else:
            raise ConfigError(
                message=f"Unknown storage type: {storage_type}",
                code="config_invalid",
                details={"storage_type": storage_type},
            )
