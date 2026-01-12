"""Pytest fixtures for gmail-multi-user-mcp tests."""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio

from gmail_multi_user.config import (
    Config,
    GoogleOAuthConfig,
    SQLiteConfig,
    StorageConfig,
)
from gmail_multi_user.storage.sqlite import SQLiteBackend
from gmail_multi_user.tokens.encryption import TokenEncryption

# =============================================================================
# Encryption Fixtures
# =============================================================================


@pytest.fixture
def encryption_key() -> str:
    """Generate a valid encryption key for testing."""
    return TokenEncryption.generate_key()


@pytest.fixture
def encryption_key_hex() -> str:
    """Generate a valid hex encryption key for testing."""
    return TokenEncryption.generate_key_hex()


@pytest.fixture
def token_encryptor(encryption_key: str) -> TokenEncryption:
    """Create a TokenEncryption instance with test key."""
    return TokenEncryption(encryption_key)


# =============================================================================
# Config Fixtures
# =============================================================================


@pytest.fixture
def google_oauth_config() -> GoogleOAuthConfig:
    """Create a test Google OAuth configuration."""
    return GoogleOAuthConfig(
        client_id="test-client-id.apps.googleusercontent.com",
        client_secret="test-client-secret",
        redirect_uri="http://localhost:8000/oauth/callback",
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )


@pytest.fixture
def sqlite_config() -> SQLiteConfig:
    """Create a test SQLite configuration."""
    return SQLiteConfig(path=":memory:")


@pytest.fixture
def storage_config(sqlite_config: SQLiteConfig) -> StorageConfig:
    """Create a test storage configuration."""
    return StorageConfig(
        type="sqlite",
        sqlite=sqlite_config,
    )


@pytest.fixture
def test_config(
    encryption_key: str,
    google_oauth_config: GoogleOAuthConfig,
    storage_config: StorageConfig,
) -> Config:
    """Create a complete test configuration."""
    return Config(
        encryption_key=encryption_key,
        google=google_oauth_config,
        storage=storage_config,
    )


@pytest.fixture
def temp_config_file(test_config: Config) -> Generator[Path, None, None]:
    """Create a temporary config file for testing."""
    import yaml

    config_dict = {
        "encryption_key": test_config.encryption_key,
        "google": {
            "client_id": test_config.google.client_id,
            "client_secret": test_config.google.client_secret,
            "redirect_uri": test_config.google.redirect_uri,
            "scopes": test_config.google.scopes,
        },
        "storage": {
            "type": test_config.storage.type,
            "sqlite": {"path": ":memory:"},
        },
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(config_dict, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


# =============================================================================
# Storage Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def sqlite_backend() -> AsyncGenerator[SQLiteBackend, None]:
    """Create an in-memory SQLite backend for testing."""
    backend = SQLiteBackend(":memory:")
    await backend.initialize()
    yield backend
    await backend.close()


@pytest_asyncio.fixture
async def sqlite_backend_with_user(
    sqlite_backend: SQLiteBackend,
) -> AsyncGenerator[tuple[SQLiteBackend, str], None]:
    """Create SQLite backend with a test user."""
    user = await sqlite_backend.get_or_create_user(
        external_user_id="test_user_123",
        email="test@example.com",
    )
    yield sqlite_backend, user.id


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def test_user_data() -> dict:
    """Test user data."""
    return {
        "external_user_id": "test_user_123",
        "email": "test@example.com",
    }


@pytest.fixture
def test_connection_data(token_encryptor: TokenEncryption) -> dict:
    """Test connection data with encrypted tokens."""
    return {
        "gmail_address": "testuser@gmail.com",
        "access_token_encrypted": token_encryptor.encrypt("test_access_token"),
        "refresh_token_encrypted": token_encryptor.encrypt("test_refresh_token"),
        "token_expires_at": datetime.utcnow() + timedelta(hours=1),
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
    }


@pytest.fixture
def test_oauth_state_data() -> dict:
    """Test OAuth state data."""
    return {
        "state": "test_state_abc123",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "redirect_uri": "http://localhost:8000/oauth/callback",
        "code_verifier": "test_code_verifier_xyz789",
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
    }


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Temporarily clean environment variables for config testing."""
    # Store original values
    original_env = {}
    gmail_vars = [k for k in os.environ if k.startswith("GMAIL_MCP_")]

    for key in gmail_vars:
        original_env[key] = os.environ.pop(key)

    yield

    # Restore original values
    for key, value in original_env.items():
        os.environ[key] = value


@pytest.fixture
def env_config(encryption_key: str, tmp_path: Path) -> Generator[None, None, None]:
    """Set up environment variables for config loading.

    Changes to a temp directory to avoid picking up local config files.
    """
    env_vars = {
        "GMAIL_MCP_ENCRYPTION_KEY": encryption_key,
        "GMAIL_MCP_GOOGLE__CLIENT_ID": "env-client-id.apps.googleusercontent.com",
        "GMAIL_MCP_GOOGLE__CLIENT_SECRET": "env-client-secret",
        "GMAIL_MCP_STORAGE__TYPE": "sqlite",
        "GMAIL_MCP_STORAGE__SQLITE__PATH": ":memory:",
    }

    # Save original directory
    original_cwd = os.getcwd()

    # Change to temp directory to avoid local config files
    os.chdir(tmp_path)

    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value

    yield

    # Cleanup
    for key in env_vars:
        os.environ.pop(key, None)

    # Restore original directory
    os.chdir(original_cwd)
