"""Setup and configuration MCP tools.

These tools help with initial setup, configuration, and diagnostics.

Each tool has an _impl function that contains the actual logic.
CLI commands use the _impl functions directly, while MCP tools wrap them.
"""

from __future__ import annotations

import base64
import secrets
from pathlib import Path
from typing import Any

from gmail_mcp_server.server import mcp


# =============================================================================
# Implementation Functions (used by both MCP tools and CLI)
# =============================================================================


async def check_setup_impl() -> dict[str, Any]:
    """Check if gmail-multi-user-mcp is properly configured.

    Returns status information about:
    - Configuration file
    - Database connection
    - Google OAuth configuration
    - Encryption key
    """
    issues: list[str] = []
    config_found = False
    config_path: str | None = None
    database_connected = False
    database_type = "unknown"
    google_oauth_configured = False
    encryption_key_set = False

    # Check for config file
    try:
        from gmail_multi_user.config import ConfigLoader

        found_path = ConfigLoader.get_config_path()
        if found_path:
            config_found = True
            config_path = str(found_path)
    except Exception:
        pass

    # Check if we can load config
    try:
        from gmail_multi_user.config import ConfigLoader

        config = ConfigLoader.load()

        # Check encryption key
        if config.encryption_key:
            encryption_key_set = True
        else:
            issues.append("Encryption key not set")

        # Check Google OAuth
        if config.google.client_id and config.google.client_secret:
            google_oauth_configured = True
        else:
            if not config.google.client_id:
                issues.append("Google client_id not configured")
            if not config.google.client_secret:
                issues.append("Google client_secret not configured")

        # Get storage type
        database_type = config.storage.type

        # Test database connection
        try:
            from gmail_multi_user.storage.factory import StorageFactory

            storage = StorageFactory.create(config)
            await storage.initialize()
            database_connected = await storage.health_check()
            await storage.close()
        except Exception as e:
            issues.append(f"Database connection failed: {e}")

    except Exception as e:
        if not config_found:
            issues.append("No configuration file found")
        issues.append(f"Configuration error: {e}")

    ready = (
        config_found
        and database_connected
        and google_oauth_configured
        and encryption_key_set
        and len(issues) == 0
    )

    return {
        "config_found": config_found,
        "config_path": config_path,
        "database_connected": database_connected,
        "database_type": database_type,
        "google_oauth_configured": google_oauth_configured,
        "encryption_key_set": encryption_key_set,
        "issues": issues,
        "ready": ready,
    }


async def init_config_impl(
    database_type: str = "sqlite",
    sqlite_path: str | None = None,
    supabase_url: str | None = None,
    supabase_key: str | None = None,
    google_client_id: str | None = None,
    google_client_secret: str | None = None,
    redirect_uri: str = "http://localhost:8000/oauth/callback",
    generate_encryption_key: bool = True,
    output_path: str = "./gmail_config.yaml",
) -> dict[str, Any]:
    """Create a gmail_config.yaml file with provided settings."""
    import yaml

    # Generate encryption key if requested
    encryption_key: str | None = None
    if generate_encryption_key:
        # Generate a 32-byte key and base64 encode it for Fernet
        key_bytes = secrets.token_bytes(32)
        encryption_key = base64.urlsafe_b64encode(key_bytes).decode()

    # Build config structure
    config: dict[str, Any] = {
        "encryption_key": encryption_key or "YOUR_ENCRYPTION_KEY_HERE",
        "google": {
            "client_id": google_client_id or "YOUR_CLIENT_ID",
            "client_secret": google_client_secret or "YOUR_CLIENT_SECRET",
            "redirect_uri": redirect_uri,
            "scopes": [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/userinfo.email",
            ],
        },
        "storage": {
            "type": database_type,
        },
        "oauth_state_ttl_seconds": 600,
        "token_refresh_buffer_seconds": 300,
    }

    # Add storage-specific config
    if database_type == "sqlite":
        config["storage"]["sqlite"] = {
            "path": sqlite_path or "gmail_mcp.db",
        }
    elif database_type == "supabase":
        config["storage"]["supabase"] = {
            "url": supabase_url or "YOUR_SUPABASE_URL",
            "key": supabase_key or "YOUR_SUPABASE_KEY",
        }

    # Write config file
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w") as f:
        f.write("# Gmail Multi-User MCP Configuration\n")
        f.write("# DO NOT COMMIT - this file contains secrets\n\n")
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Build next steps
    next_steps: list[str] = []

    if not google_client_id or not google_client_secret:
        next_steps.append(
            "Set up Google OAuth credentials at https://console.cloud.google.com/apis/credentials"
        )
        next_steps.append("Update google.client_id and google.client_secret in the config")

    if database_type == "supabase" and (not supabase_url or not supabase_key):
        next_steps.append("Set up Supabase project at https://supabase.com")
        next_steps.append("Update storage.supabase.url and storage.supabase.key in the config")
        next_steps.append("Run the migration SQL from migrations/supabase/001_initial.sql")

    if database_type == "sqlite":
        next_steps.append("Database will be created automatically on first use")

    next_steps.append("Add gmail_config.yaml to .gitignore to protect secrets")

    result: dict[str, Any] = {
        "config_path": str(output.absolute()),
        "next_steps": next_steps,
    }

    if encryption_key:
        result["encryption_key"] = encryption_key

    return result


async def test_connection_impl(verbose: bool = False) -> dict[str, Any]:
    """Test database and Google OAuth configuration."""
    result: dict[str, Any] = {
        "database_ok": False,
        "google_oauth_ok": False,
    }

    # Test database
    try:
        from gmail_multi_user.config import ConfigLoader
        from gmail_multi_user.storage.factory import StorageFactory

        config = ConfigLoader.load()
        storage = StorageFactory.create(config)
        await storage.initialize()

        # Run health check
        healthy = await storage.health_check()
        result["database_ok"] = healthy

        if verbose:
            result["database_type"] = config.storage.type
            users = await storage.list_users()
            result["user_count"] = len(users)
            connections = await storage.list_connections()
            result["connection_count"] = len(connections)

        await storage.close()

    except Exception as e:
        result["database_error"] = str(e)

    # Test Google OAuth config
    try:
        from gmail_multi_user.config import ConfigLoader
        from gmail_multi_user.oauth.google import GoogleOAuthClient

        config = ConfigLoader.load()

        if config.google.client_id and config.google.client_secret:
            result["google_oauth_ok"] = True

            if verbose:
                result["google_redirect_uri"] = config.google.redirect_uri
                result["google_scopes"] = config.google.scopes

            # Generate a test auth URL to verify config is valid
            try:
                client = GoogleOAuthClient(config.google)
                test_url = client.build_auth_url(
                    state="test_state",
                    code_challenge="test_challenge",
                    scopes=config.google.scopes,
                    redirect_uri=config.google.redirect_uri,
                )
                result["test_auth_url"] = test_url
                await client.close()
            except Exception as e:
                result["google_oauth_error"] = f"Failed to build auth URL: {e}"
                result["google_oauth_ok"] = False

    except Exception as e:
        result["google_oauth_error"] = str(e)

    return result


async def run_migrations_impl() -> dict[str, Any]:
    """Run database migrations (idempotent)."""
    from gmail_multi_user.config import ConfigLoader

    config = ConfigLoader.load()

    if config.storage.type == "sqlite":
        # SQLite creates tables on initialization
        from gmail_multi_user.storage.factory import StorageFactory

        storage = StorageFactory.create(config)
        await storage.initialize()
        await storage.close()

        return {
            "migrations_run": ["001_initial"],
            "already_applied": [],
            "current_version": "001_initial",
            "message": "SQLite tables created/verified automatically",
        }

    elif config.storage.type == "supabase":
        # For Supabase, check if tables exist
        from gmail_multi_user.storage.factory import StorageFactory

        storage = StorageFactory.create(config)
        await storage.initialize()

        # Try to check schema_migrations table
        migrations_applied: list[str] = []
        try:
            # Check if we can query the users table
            await storage.list_users()
            migrations_applied.append("001_initial")
        except Exception:
            pass

        await storage.close()

        if migrations_applied:
            return {
                "migrations_run": [],
                "already_applied": migrations_applied,
                "current_version": migrations_applied[-1] if migrations_applied else None,
                "message": "Supabase migrations already applied",
            }
        else:
            return {
                "migrations_run": [],
                "already_applied": [],
                "current_version": None,
                "message": (
                    "Supabase tables not found. "
                    "Run migrations/supabase/001_initial.sql in the Supabase SQL Editor."
                ),
            }

    return {
        "migrations_run": [],
        "already_applied": [],
        "current_version": None,
        "message": f"Unknown storage type: {config.storage.type}",
    }


# =============================================================================
# MCP Tool Wrappers
# =============================================================================


@mcp.tool
async def gmail_check_setup() -> dict[str, Any]:
    """Check if gmail-multi-user-mcp is properly configured.

    Returns status information about:
    - Configuration file
    - Database connection
    - Google OAuth configuration
    - Encryption key

    Returns:
        Status dictionary with config_found, database_connected,
        google_oauth_configured, encryption_key_set, issues list, and ready flag.
    """
    return await check_setup_impl()


@mcp.tool
async def gmail_init_config(
    database_type: str = "sqlite",
    sqlite_path: str | None = None,
    supabase_url: str | None = None,
    supabase_key: str | None = None,
    google_client_id: str | None = None,
    google_client_secret: str | None = None,
    redirect_uri: str = "http://localhost:8000/oauth/callback",
    generate_encryption_key: bool = True,
    output_path: str = "./gmail_config.yaml",
) -> dict[str, Any]:
    """Create a gmail_config.yaml file with provided settings.

    Args:
        database_type: Storage backend type ("sqlite" or "supabase").
        sqlite_path: Path for SQLite database (if using sqlite).
        supabase_url: Supabase project URL (if using supabase).
        supabase_key: Supabase service role key (if using supabase).
        google_client_id: Google OAuth client ID.
        google_client_secret: Google OAuth client secret.
        redirect_uri: OAuth redirect URI.
        generate_encryption_key: Whether to generate a new encryption key.
        output_path: Path for the output config file.

    Returns:
        Dictionary with config_path, encryption_key (if generated), and next_steps.
    """
    return await init_config_impl(
        database_type=database_type,
        sqlite_path=sqlite_path,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
        redirect_uri=redirect_uri,
        generate_encryption_key=generate_encryption_key,
        output_path=output_path,
    )


@mcp.tool
async def gmail_test_connection(verbose: bool = False) -> dict[str, Any]:
    """Test database and Google OAuth configuration.

    Args:
        verbose: Include detailed information in the response.

    Returns:
        Dictionary with database_ok, google_oauth_ok, and any errors.
    """
    return await test_connection_impl(verbose=verbose)


@mcp.tool
async def gmail_run_migrations() -> dict[str, Any]:
    """Run database migrations (idempotent).

    For SQLite, tables are created automatically on initialization.
    For Supabase, migrations must be run manually in the SQL editor.

    Returns:
        Dictionary with migrations_run, already_applied, and current_version.
    """
    return await run_migrations_impl()
