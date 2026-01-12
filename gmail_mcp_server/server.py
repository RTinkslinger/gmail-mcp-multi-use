"""Gmail Multi-User MCP Server.

This module provides the main FastMCP server instance and shared state
management for the Gmail multi-user integration.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

if TYPE_CHECKING:
    from gmail_multi_user.config import Config
    from gmail_multi_user.oauth.manager import OAuthManager
    from gmail_multi_user.service import GmailService
    from gmail_multi_user.storage.base import StorageBackend
    from gmail_multi_user.tokens.encryption import TokenEncryption
    from gmail_multi_user.tokens.manager import TokenManager


class ServerState:
    """Manages the shared state for the MCP server.

    This class handles lazy initialization of all components
    and provides access to the Gmail service layer.
    """

    def __init__(self) -> None:
        """Initialize server state (components are lazily loaded)."""
        self._config: Config | None = None
        self._storage: StorageBackend | None = None
        self._encryption: TokenEncryption | None = None
        self._token_manager: TokenManager | None = None
        self._oauth_manager: OAuthManager | None = None
        self._gmail_service: GmailService | None = None
        self._initialized: bool = False

    @property
    def is_initialized(self) -> bool:
        """Check if the server has been initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize all components.

        This loads config, creates storage backend, and sets up managers.
        """
        if self._initialized:
            return

        from gmail_multi_user.config import ConfigLoader
        from gmail_multi_user.oauth.manager import OAuthManager
        from gmail_multi_user.service import GmailService
        from gmail_multi_user.storage.factory import StorageFactory
        from gmail_multi_user.tokens.encryption import TokenEncryption
        from gmail_multi_user.tokens.manager import TokenManager

        # Load configuration
        loader = ConfigLoader()
        self._config = loader.load()

        # Create storage backend
        self._storage = StorageFactory.create(self._config)
        await self._storage.initialize()

        # Create encryption utility
        self._encryption = TokenEncryption(self._config.encryption_key)

        # Create token manager
        self._token_manager = TokenManager(
            config=self._config,
            storage=self._storage,
            encryption=self._encryption,
        )

        # Create OAuth manager
        self._oauth_manager = OAuthManager(
            config=self._config,
            storage=self._storage,
            encryption=self._encryption,
        )

        # Create Gmail service
        self._gmail_service = GmailService(
            config=self._config,
            storage=self._storage,
            token_manager=self._token_manager,
        )

        self._initialized = True

    async def close(self) -> None:
        """Close all resources."""
        if self._gmail_service:
            await self._gmail_service.close()
        if self._oauth_manager:
            await self._oauth_manager.close()
        if self._storage:
            await self._storage.close()
        self._initialized = False

    @property
    def config(self) -> Config:
        """Get the configuration."""
        if not self._config:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        return self._config

    @property
    def storage(self) -> StorageBackend:
        """Get the storage backend."""
        if not self._storage:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        return self._storage

    @property
    def encryption(self) -> TokenEncryption:
        """Get the encryption utility."""
        if not self._encryption:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        return self._encryption

    @property
    def token_manager(self) -> TokenManager:
        """Get the token manager."""
        if not self._token_manager:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        return self._token_manager

    @property
    def oauth_manager(self) -> OAuthManager:
        """Get the OAuth manager."""
        if not self._oauth_manager:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        return self._oauth_manager

    @property
    def gmail_service(self) -> GmailService:
        """Get the Gmail service."""
        if not self._gmail_service:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        return self._gmail_service


# Global server state
state = ServerState()


@asynccontextmanager
async def lifespan(mcp_server: FastMCP):
    """Manage server lifecycle."""
    try:
        await state.initialize()
        yield
    finally:
        await state.close()


# Create the FastMCP server
mcp = FastMCP(
    name="gmail-multi-user-mcp",
    instructions="Multi-user Gmail integration MCP server for AI agents and applications.",
    lifespan=lifespan,
)


def format_datetime(dt: datetime | None) -> str | None:
    """Format a datetime for JSON output."""
    if dt is None:
        return None
    return dt.isoformat()


def format_response(data: Any) -> dict[str, Any]:
    """Format a response for MCP tools.

    Handles dataclasses, datetimes, and nested structures.
    """
    if hasattr(data, "__dataclass_fields__"):
        result = asdict(data)
        # Convert datetime fields
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = format_datetime(value)
            elif isinstance(value, list):
                result[key] = [
                    format_response(item) if hasattr(item, "__dataclass_fields__") else item
                    for item in value
                ]
        return result
    return data


def register_all() -> None:
    """Register all tools, resources, and prompts.

    This is called separately to avoid circular imports.
    """
    # Import and register tools, resources, and prompts
    # These imports will register their decorators with the mcp instance
    from gmail_mcp_server.prompts import (  # noqa: F401
        setup as setup_prompts,
    )
    from gmail_mcp_server.resources import config as config_resources  # noqa: F401
    from gmail_mcp_server.resources import docs as doc_resources  # noqa: F401
    from gmail_mcp_server.resources import gmail as gmail_resources  # noqa: F401
    from gmail_mcp_server.resources import users as user_resources  # noqa: F401
    from gmail_mcp_server.tools import auth, manage, read, setup, write  # noqa: F401


# Register on import
register_all()
