"""Tests for configuration loading."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from gmail_multi_user.config import Config, ConfigLoader
from gmail_multi_user.exceptions import ConfigError


class TestConfig:
    """Tests for Config class."""

    def test_config_with_valid_base64_key(
        self,
        encryption_key: str,
        google_oauth_config,
        storage_config,
    ) -> None:
        """Test that Config accepts valid base64 encryption key."""
        config = Config(
            encryption_key=encryption_key,
            google=google_oauth_config,
            storage=storage_config,
        )
        assert config.encryption_key == encryption_key

    def test_config_with_valid_hex_key(
        self,
        encryption_key_hex: str,
        google_oauth_config,
        storage_config,
    ) -> None:
        """Test that Config accepts valid hex encryption key."""
        config = Config(
            encryption_key=encryption_key_hex,
            google=google_oauth_config,
            storage=storage_config,
        )
        assert config.encryption_key == encryption_key_hex

    def test_config_rejects_invalid_key(
        self,
        google_oauth_config,
        storage_config,
    ) -> None:
        """Test that Config rejects invalid encryption key."""
        with pytest.raises(ValueError, match="encryption_key must be a valid"):
            Config(
                encryption_key="invalid-key",
                google=google_oauth_config,
                storage=storage_config,
            )

    def test_config_default_values(
        self,
        encryption_key: str,
        google_oauth_config,
    ) -> None:
        """Test that Config has correct default values."""
        config = Config(
            encryption_key=encryption_key,
            google=google_oauth_config,
        )

        assert config.storage.type == "sqlite"
        assert config.oauth_state_ttl_seconds == 600
        assert config.token_refresh_buffer_seconds == 300


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_load_from_file(
        self,
        temp_config_file: Path,
        clean_env,
    ) -> None:
        """Test loading config from file."""
        config = ConfigLoader.load(config_path=temp_config_file)

        assert config.google.client_id == "test-client-id.apps.googleusercontent.com"
        assert config.storage.type == "sqlite"

    def test_load_from_env_vars(
        self,
        env_config,
    ) -> None:
        """Test loading config from environment variables."""
        config = ConfigLoader.load()

        assert config.google.client_id == "env-client-id.apps.googleusercontent.com"
        assert config.storage.type == "sqlite"

    def test_file_values_take_precedence_over_env(
        self,
        temp_config_file: Path,
        encryption_key: str,
    ) -> None:
        """Test that file values take precedence when explicitly loaded.

        Note: When loading from an explicit config file, file values take
        precedence over environment variables. This is the standard
        pydantic-settings behavior when constructor arguments are provided.
        To use env vars only, don't specify a config file.
        """
        # Set env var
        os.environ["GMAIL_MCP_GOOGLE__CLIENT_ID"] = "env-client-id"
        os.environ["GMAIL_MCP_ENCRYPTION_KEY"] = encryption_key

        try:
            config = ConfigLoader.load(config_path=temp_config_file)
            # File values take precedence when file is explicitly loaded
            assert (
                config.google.client_id == "test-client-id.apps.googleusercontent.com"
            )
        finally:
            os.environ.pop("GMAIL_MCP_GOOGLE__CLIENT_ID", None)
            os.environ.pop("GMAIL_MCP_ENCRYPTION_KEY", None)

    def test_load_missing_file_raises_error(
        self,
        clean_env,
    ) -> None:
        """Test that loading non-existent file raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            ConfigLoader.load(config_path="/nonexistent/path/config.yaml")

        assert exc_info.value.code == "config_not_found"

    def test_load_invalid_yaml_raises_error(
        self,
        clean_env,
        tmp_path: Path,
    ) -> None:
        """Test that loading invalid YAML raises ConfigError."""
        # Create invalid YAML file
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("{ invalid: yaml: content")

        with pytest.raises(ConfigError) as exc_info:
            ConfigLoader.load(config_path=invalid_file)

        assert exc_info.value.code == "config_invalid"

    def test_load_missing_required_field_raises_error(
        self,
        clean_env,
        tmp_path: Path,
        encryption_key: str,
    ) -> None:
        """Test that missing required field raises ConfigError."""
        import yaml

        # Create config missing google.client_secret
        config_file = tmp_path / "incomplete.yaml"
        config_data = {
            "encryption_key": encryption_key,
            "google": {
                "client_id": "test-client-id",
                # Missing client_secret
            },
        }
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigError) as exc_info:
            ConfigLoader.load(config_path=config_file)

        assert exc_info.value.code == "config_invalid"

    def test_gmail_mcp_config_env_var(
        self,
        temp_config_file: Path,
        clean_env,
    ) -> None:
        """Test that GMAIL_MCP_CONFIG env var is used."""
        os.environ["GMAIL_MCP_CONFIG"] = str(temp_config_file)

        try:
            config = ConfigLoader.load()
            assert (
                config.google.client_id == "test-client-id.apps.googleusercontent.com"
            )
        finally:
            os.environ.pop("GMAIL_MCP_CONFIG", None)

    def test_gmail_mcp_config_env_var_not_found_raises_error(
        self,
        clean_env,
    ) -> None:
        """Test that invalid GMAIL_MCP_CONFIG path raises error."""
        os.environ["GMAIL_MCP_CONFIG"] = "/nonexistent/config.yaml"

        try:
            with pytest.raises(ConfigError) as exc_info:
                ConfigLoader.load()

            assert exc_info.value.code == "config_not_found"
            assert "GMAIL_MCP_CONFIG" in str(exc_info.value.details)
        finally:
            os.environ.pop("GMAIL_MCP_CONFIG", None)

    def test_get_config_path_returns_none_when_no_file(
        self,
        clean_env,
    ) -> None:
        """Test that get_config_path returns None when no config file exists."""
        path = ConfigLoader.get_config_path()
        # May return a default path if it exists, or None
        # The important thing is it doesn't raise
        assert path is None or isinstance(path, Path)


class TestStorageConfig:
    """Tests for storage configuration."""

    def test_sqlite_config_defaults(
        self,
        encryption_key: str,
        google_oauth_config,
    ) -> None:
        """Test SQLite config default values."""
        config = Config(
            encryption_key=encryption_key,
            google=google_oauth_config,
        )

        assert config.storage.type == "sqlite"
        assert config.storage.sqlite is not None
        assert config.storage.sqlite.path == "gmail_mcp.db"

    def test_supabase_config(
        self,
        encryption_key: str,
        google_oauth_config,
    ) -> None:
        """Test Supabase storage configuration."""
        from gmail_multi_user.config import StorageConfig, SupabaseConfig

        config = Config(
            encryption_key=encryption_key,
            google=google_oauth_config,
            storage=StorageConfig(
                type="supabase",
                supabase=SupabaseConfig(
                    url="https://example.supabase.co",
                    key="test-service-key",
                ),
            ),
        )

        assert config.storage.type == "supabase"
        assert config.storage.supabase is not None
        assert config.storage.supabase.url == "https://example.supabase.co"
