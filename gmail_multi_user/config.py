"""Configuration management for gmail-multi-user-mcp.

This module provides configuration loading from multiple sources:
1. Environment variables (highest priority)
2. GMAIL_MCP_CONFIG environment variable pointing to a YAML file
3. ./gmail_config.yaml in current directory
4. ~/.gmail_mcp/config.yaml in home directory

Environment variables use the GMAIL_MCP_ prefix.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from gmail_multi_user.exceptions import ConfigError


class GoogleOAuthConfig(BaseModel):
    """Google OAuth configuration."""

    client_id: str = Field(..., description="Google OAuth client ID")
    client_secret: str = Field(..., description="Google OAuth client secret")
    redirect_uri: str = Field(
        default="http://localhost:8000/oauth/callback",
        description="OAuth redirect URI",
    )
    scopes: list[str] = Field(
        default=["https://www.googleapis.com/auth/gmail.readonly"],
        description="Default Gmail scopes to request",
    )


class SQLiteConfig(BaseModel):
    """SQLite storage configuration."""

    path: str = Field(
        default="gmail_mcp.db",
        description="Path to SQLite database file",
    )


class SupabaseConfig(BaseModel):
    """Supabase storage configuration."""

    url: str = Field(..., description="Supabase project URL")
    key: str = Field(..., description="Supabase service role key")


class StorageConfig(BaseModel):
    """Storage backend configuration."""

    type: Literal["sqlite", "supabase"] = Field(
        default="sqlite",
        description="Storage backend type",
    )
    sqlite: SQLiteConfig | None = Field(
        default_factory=SQLiteConfig,
        description="SQLite configuration (if type is sqlite)",
    )
    supabase: SupabaseConfig | None = Field(
        default=None,
        description="Supabase configuration (if type is supabase)",
    )


class Config(BaseSettings):
    """Main configuration for gmail-multi-user-mcp.

    Configuration is loaded from environment variables and/or YAML files.
    Environment variables take precedence and use the GMAIL_MCP_ prefix.

    Example environment variables:
        GMAIL_MCP_ENCRYPTION_KEY=your-fernet-key
        GMAIL_MCP_GOOGLE__CLIENT_ID=your-client-id
        GMAIL_MCP_STORAGE__TYPE=sqlite
    """

    model_config = SettingsConfigDict(
        env_prefix="GMAIL_MCP_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Security
    encryption_key: str = Field(
        ...,
        description="Fernet encryption key for token storage (hex or base64)",
    )

    # Google OAuth
    google: GoogleOAuthConfig = Field(
        ...,
        description="Google OAuth configuration",
    )

    # Storage
    storage: StorageConfig = Field(
        default_factory=StorageConfig,
        description="Storage backend configuration",
    )

    # Server settings
    oauth_state_ttl_seconds: int = Field(
        default=600,
        description="OAuth state expiration time in seconds (default: 10 minutes)",
    )
    token_refresh_buffer_seconds: int = Field(
        default=300,
        description="Refresh tokens this many seconds before expiry (default: 5 minutes)",
    )

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate the encryption key format."""
        # Fernet keys are 32 bytes, base64-encoded (44 chars with padding)
        # or hex-encoded (64 chars)
        if len(v) == 44 and v.endswith("="):
            # Looks like base64
            return v
        if len(v) == 64:
            # Looks like hex
            try:
                bytes.fromhex(v)
                return v
            except ValueError:
                pass
        raise ValueError(
            "encryption_key must be a valid Fernet key (44 char base64 or 64 char hex)"
        )


class ConfigLoader:
    """Load configuration from various sources.

    Priority order (highest to lowest):
    1. Environment variables (GMAIL_MCP_*)
    2. GMAIL_MCP_CONFIG environment variable path
    3. ./gmail_config.yaml
    4. ~/.gmail_mcp/config.yaml

    Example:
        config = ConfigLoader.load()
    """

    DEFAULT_PATHS = [
        Path("./gmail_config.yaml"),
        Path.home() / ".gmail_mcp" / "config.yaml",
    ]

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> Config:
        """Load configuration from available sources.

        Args:
            config_path: Optional explicit path to config file.

        Returns:
            Loaded and validated Config object.

        Raises:
            ConfigError: If configuration is invalid or required values are missing.
        """
        # Determine config file path
        file_path = cls._find_config_file(config_path)

        # Load from file if found
        file_config: dict[str, Any] = {}
        if file_path:
            file_config = cls._load_yaml_file(file_path)

        # Merge with environment variables (env vars take precedence)
        try:
            config = Config(**file_config)
            return config
        except Exception as e:
            raise ConfigError(
                message=f"Invalid configuration: {e}",
                code="config_invalid",
                details={"config_path": str(file_path) if file_path else None},
            ) from e

    @classmethod
    def _find_config_file(cls, explicit_path: str | Path | None) -> Path | None:
        """Find the configuration file to use.

        Args:
            explicit_path: Explicitly provided path.

        Returns:
            Path to config file, or None if not found.
        """
        # 1. Explicit path
        if explicit_path:
            path = Path(explicit_path)
            if path.exists():
                return path
            raise ConfigError(
                message=f"Config file not found: {explicit_path}",
                code="config_not_found",
                details={"path": str(explicit_path)},
            )

        # 2. GMAIL_MCP_CONFIG environment variable
        env_path = os.environ.get("GMAIL_MCP_CONFIG")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
            raise ConfigError(
                message=f"Config file specified in GMAIL_MCP_CONFIG not found: {env_path}",
                code="config_not_found",
                details={"path": env_path, "source": "GMAIL_MCP_CONFIG"},
            )

        # 3. Default paths
        for default_path in cls.DEFAULT_PATHS:
            if default_path.exists():
                return default_path

        # 4. No config file found - rely on environment variables only
        return None

    @classmethod
    def _load_yaml_file(cls, path: Path) -> dict[str, Any]:
        """Load a YAML configuration file.

        Args:
            path: Path to the YAML file.

        Returns:
            Dictionary of configuration values.

        Raises:
            ConfigError: If the file cannot be read or parsed.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except yaml.YAMLError as e:
            raise ConfigError(
                message=f"Invalid YAML in config file: {e}",
                code="config_invalid",
                details={"path": str(path)},
            ) from e
        except OSError as e:
            raise ConfigError(
                message=f"Cannot read config file: {e}",
                code="config_not_found",
                details={"path": str(path)},
            ) from e

    @classmethod
    def get_config_path(cls) -> Path | None:
        """Get the path to the active config file, if any.

        Returns:
            Path to config file being used, or None if using env vars only.
        """
        return cls._find_config_file(None)

    @classmethod
    def validate(cls, config: Config | None = None) -> ValidationResult:
        """Validate configuration comprehensively.

        Args:
            config: Config to validate. If None, loads from available sources.

        Returns:
            ValidationResult with issues and warnings.
        """
        issues: list[ValidationIssue] = []
        warnings: list[str] = []

        # Try to load config if not provided
        if config is None:
            try:
                config = cls.load()
            except ConfigError as e:
                issues.append(
                    ValidationIssue(
                        field="config",
                        message=str(e),
                        severity="error",
                        suggestion=e.suggestion,
                    )
                )
                return ValidationResult(valid=False, issues=issues, warnings=warnings)

        # Validate encryption key
        issues.extend(_validate_encryption_key(config.encryption_key))

        # Validate Google OAuth
        issues.extend(_validate_google_oauth(config.google))

        # Validate storage configuration
        issues.extend(_validate_storage(config.storage))

        # Add warnings for common misconfigurations
        warnings.extend(_check_common_warnings(config))

        return ValidationResult(
            valid=len([i for i in issues if i.severity == "error"]) == 0,
            issues=issues,
            warnings=warnings,
        )


@dataclass
class ValidationIssue:
    """A configuration validation issue."""

    field: str
    message: str
    severity: Literal["error", "warning"]
    suggestion: str | None = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    valid: bool
    issues: list[ValidationIssue]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "valid": self.valid,
            "issues": [
                {
                    "field": i.field,
                    "message": i.message,
                    "severity": i.severity,
                    "suggestion": i.suggestion,
                }
                for i in self.issues
            ],
            "warnings": self.warnings,
        }


def _validate_encryption_key(key: str) -> list[ValidationIssue]:
    """Validate the encryption key format."""
    issues: list[ValidationIssue] = []

    # Check if it's a placeholder
    if "YOUR_" in key or key == "":
        issues.append(
            ValidationIssue(
                field="encryption_key",
                message="Encryption key appears to be a placeholder",
                severity="error",
                suggestion=(
                    "Generate a real encryption key with: "
                    'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
                ),
            )
        )
        return issues

    # Try to create a Fernet instance to validate the key
    try:
        import base64

        from cryptography.fernet import Fernet

        # Try base64 format
        if len(key) == 44 and key.endswith("="):
            Fernet(key.encode())
            return issues

        # Try hex format
        if len(key) == 64:
            try:
                key_bytes = bytes.fromhex(key)
                key_b64 = base64.urlsafe_b64encode(key_bytes).decode()
                Fernet(key_b64.encode())
                return issues
            except ValueError:
                pass

        issues.append(
            ValidationIssue(
                field="encryption_key",
                message="Encryption key format is invalid",
                severity="error",
                suggestion="Key must be 44-character base64 or 64-character hex string.",
            )
        )

    except Exception as e:
        issues.append(
            ValidationIssue(
                field="encryption_key",
                message=f"Cannot validate encryption key: {e}",
                severity="error",
                suggestion="Ensure cryptography package is installed.",
            )
        )

    return issues


def _validate_google_oauth(google: GoogleOAuthConfig) -> list[ValidationIssue]:
    """Validate Google OAuth configuration."""
    issues: list[ValidationIssue] = []

    # Check client_id
    if not google.client_id or "YOUR_" in google.client_id:
        issues.append(
            ValidationIssue(
                field="google.client_id",
                message="Google client_id is missing or placeholder",
                severity="error",
                suggestion="Get OAuth credentials from https://console.cloud.google.com/apis/credentials",
            )
        )

    # Check client_secret
    if not google.client_secret or "YOUR_" in google.client_secret:
        issues.append(
            ValidationIssue(
                field="google.client_secret",
                message="Google client_secret is missing or placeholder",
                severity="error",
                suggestion="Get OAuth credentials from https://console.cloud.google.com/apis/credentials",
            )
        )

    # Validate redirect_uri format
    if not google.redirect_uri.startswith(("http://", "https://")):
        issues.append(
            ValidationIssue(
                field="google.redirect_uri",
                message="redirect_uri must start with http:// or https://",
                severity="error",
                suggestion="Use a valid URL like http://localhost:8000/oauth/callback",
            )
        )

    # Check for required scopes
    required_scopes = {"https://www.googleapis.com/auth/userinfo.email"}
    configured_scopes = set(google.scopes)
    if not required_scopes.issubset(configured_scopes):
        issues.append(
            ValidationIssue(
                field="google.scopes",
                message="Missing required scope: userinfo.email",
                severity="warning",
                suggestion="Add https://www.googleapis.com/auth/userinfo.email to scopes for email address retrieval.",
            )
        )

    return issues


def _validate_storage(storage: StorageConfig) -> list[ValidationIssue]:
    """Validate storage configuration."""
    issues: list[ValidationIssue] = []

    if storage.type == "sqlite":
        # SQLite validation
        if storage.sqlite is None:
            issues.append(
                ValidationIssue(
                    field="storage.sqlite",
                    message="SQLite configuration is missing",
                    severity="error",
                    suggestion="Add storage.sqlite.path to configuration.",
                )
            )
        else:
            # Check if parent directory exists
            db_path = Path(storage.sqlite.path)
            if not db_path.parent.exists() and str(db_path.parent) != ".":
                issues.append(
                    ValidationIssue(
                        field="storage.sqlite.path",
                        message=f"Parent directory does not exist: {db_path.parent}",
                        severity="warning",
                        suggestion="Create the directory or use a different path.",
                    )
                )

    elif storage.type == "supabase":
        # Supabase validation
        if storage.supabase is None:
            issues.append(
                ValidationIssue(
                    field="storage.supabase",
                    message="Supabase configuration is missing",
                    severity="error",
                    suggestion="Add storage.supabase.url and storage.supabase.key to configuration.",
                )
            )
        else:
            if not storage.supabase.url or "YOUR_" in storage.supabase.url:
                issues.append(
                    ValidationIssue(
                        field="storage.supabase.url",
                        message="Supabase URL is missing or placeholder",
                        severity="error",
                        suggestion="Get URL from Supabase project settings.",
                    )
                )

            if not storage.supabase.key or "YOUR_" in storage.supabase.key:
                issues.append(
                    ValidationIssue(
                        field="storage.supabase.key",
                        message="Supabase key is missing or placeholder",
                        severity="error",
                        suggestion="Get service role key from Supabase project settings > API.",
                    )
                )

            # Warn if not using service role key
            if storage.supabase.key and not storage.supabase.key.startswith("eyJ"):
                issues.append(
                    ValidationIssue(
                        field="storage.supabase.key",
                        message="Supabase key doesn't look like a JWT",
                        severity="warning",
                        suggestion="Ensure you're using the service role key, not anon key.",
                    )
                )

    return issues


def _check_common_warnings(config: Config) -> list[str]:
    """Check for common configuration warnings."""
    warnings: list[str] = []

    # Warn about localhost redirect URI in what looks like production
    if "localhost" in config.google.redirect_uri:
        warnings.append(
            "Using localhost redirect_uri - ensure this is for development only. "
            "For production, use your actual domain."
        )

    # Warn about short state TTL
    if config.oauth_state_ttl_seconds < 300:
        warnings.append(
            f"OAuth state TTL is {config.oauth_state_ttl_seconds}s - "
            "this may be too short for users to complete authorization."
        )

    # Warn about long refresh buffer
    if config.token_refresh_buffer_seconds > 600:
        warnings.append(
            f"Token refresh buffer is {config.token_refresh_buffer_seconds}s - "
            "this may cause unnecessary token refreshes."
        )

    return warnings
