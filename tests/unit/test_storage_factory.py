"""Tests for storage factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gmail_multi_user.exceptions import ConfigError
from gmail_multi_user.storage.factory import StorageFactory


class TestStorageFactory:
    """Tests for StorageFactory."""

    def test_create_sqlite_backend(self):
        """Test creating SQLite backend."""
        config = MagicMock()
        config.storage.type = "sqlite"
        config.storage.sqlite.path = ":memory:"

        backend = StorageFactory.create(config)

        from gmail_multi_user.storage.sqlite import SQLiteBackend
        assert isinstance(backend, SQLiteBackend)

    def test_create_supabase_backend(self):
        """Test creating Supabase backend."""
        config = MagicMock()
        config.storage.type = "supabase"
        config.storage.supabase.url = "https://test.supabase.co"
        config.storage.supabase.key = "test_key"

        # SupabaseBackend is imported lazily inside the create() method
        with patch("gmail_multi_user.storage.supabase.SupabaseBackend") as mock_supabase:
            mock_backend = MagicMock()
            mock_supabase.return_value = mock_backend

            backend = StorageFactory.create(config)

            mock_supabase.assert_called_once_with(
                supabase_url="https://test.supabase.co",
                supabase_key="test_key",
            )
            assert backend == mock_backend

    def test_create_invalid_type_raises_error(self):
        """Test creating backend with invalid type raises error."""
        config = MagicMock()
        config.storage.type = "invalid"

        with pytest.raises(ConfigError, match="Unknown storage type"):
            StorageFactory.create(config)

    def test_create_sqlite_default_path(self):
        """Test SQLite backend with default path."""
        config = MagicMock()
        config.storage.type = "sqlite"
        config.storage.sqlite.path = "test_database.db"

        backend = StorageFactory.create(config)

        from gmail_multi_user.storage.sqlite import SQLiteBackend
        assert isinstance(backend, SQLiteBackend)
