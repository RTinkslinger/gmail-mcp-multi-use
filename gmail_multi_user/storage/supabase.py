"""Supabase storage backend implementation.

This module provides a Supabase storage backend for production deployments.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from gmail_multi_user.exceptions import StorageError
from gmail_multi_user.storage.base import StorageBackend
from gmail_multi_user.types import Connection, OAuthState, User

if TYPE_CHECKING:
    from supabase import Client


class SupabaseBackend(StorageBackend):
    """Supabase storage backend for production deployments.

    Uses the Supabase Python client for database operations via PostgreSQL.
    Requires tables to be created via migration before use.

    Example:
        backend = SupabaseBackend(supabase_url, supabase_key)
        await backend.initialize()
        user = await backend.get_or_create_user("user_123")
    """

    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        """Initialize Supabase backend.

        Args:
            supabase_url: Supabase project URL.
            supabase_key: Supabase service role key.
        """
        self._supabase_url = supabase_url
        self._supabase_key = supabase_key
        self._client: Client | None = None

    def _get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            from supabase import create_client

            self._client = create_client(self._supabase_url, self._supabase_key)
        return self._client

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    async def initialize(self) -> None:
        """Initialize the storage backend.

        Note: Tables must be created via migration scripts.
        This method just verifies the connection.
        """
        # Verify connection by attempting a simple query
        try:
            self._get_client().table("users").select("id").limit(1).execute()
        except Exception as e:
            raise StorageError(
                message=f"Failed to connect to Supabase: {e}",
                code="connection_failed",
                details={"error": str(e)},
            ) from e

    async def close(self) -> None:
        """Close the Supabase client."""
        # Supabase client doesn't require explicit closing
        self._client = None

    async def health_check(self) -> bool:
        """Check if Supabase is accessible."""
        try:
            self._get_client().table("users").select("id").limit(1).execute()
            return True
        except Exception:
            return False

    # =========================================================================
    # User Methods
    # =========================================================================

    async def get_or_create_user(
        self,
        external_user_id: str,
        email: str | None = None,
    ) -> User:
        """Get an existing user or create a new one."""
        client = self._get_client()

        # Try to get existing user
        result = (
            client.table("users")
            .select("*")
            .eq("external_user_id", external_user_id)
            .execute()
        )

        if result.data:
            row = result.data[0]
            # Update email if provided and different
            if email and row.get("email") != email:
                client.table("users").update({"email": email}).eq(
                    "id", row["id"]
                ).execute()
                row["email"] = email
            return self._dict_to_user(row)

        # Create new user
        user_id = self._generate_id()
        now = datetime.now(timezone.utc).isoformat()

        data = {
            "id": user_id,
            "external_user_id": external_user_id,
            "email": email,
            "created_at": now,
            "updated_at": now,
        }

        result = client.table("users").insert(data).execute()

        if not result.data:
            raise StorageError(
                message="Failed to create user",
                code="query_failed",
            )

        return self._dict_to_user(result.data[0])

    async def get_user_by_external_id(self, external_user_id: str) -> User | None:
        """Get a user by their external ID."""
        client = self._get_client()
        result = (
            client.table("users")
            .select("*")
            .eq("external_user_id", external_user_id)
            .execute()
        )
        return self._dict_to_user(result.data[0]) if result.data else None

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get a user by their internal ID."""
        client = self._get_client()
        result = client.table("users").select("*").eq("id", user_id).execute()
        return self._dict_to_user(result.data[0]) if result.data else None

    async def list_users(self) -> list[User]:
        """List all users."""
        client = self._get_client()
        result = (
            client.table("users").select("*").order("created_at", desc=True).execute()
        )
        return [self._dict_to_user(row) for row in result.data]

    # =========================================================================
    # Connection Methods
    # =========================================================================

    async def create_connection(
        self,
        user_id: str,
        gmail_address: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str,
        token_expires_at: datetime,
        scopes: list[str],
    ) -> Connection:
        """Create a new Gmail connection."""
        client = self._get_client()
        connection_id = self._generate_id()
        now = datetime.now(timezone.utc).isoformat()

        data = {
            "id": connection_id,
            "user_id": user_id,
            "gmail_address": gmail_address,
            "access_token_encrypted": access_token_encrypted,
            "refresh_token_encrypted": refresh_token_encrypted,
            "token_expires_at": token_expires_at.isoformat(),
            "scopes": json.dumps(scopes),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "last_used_at": None,
        }

        try:
            result = client.table("gmail_connections").insert(data).execute()
        except Exception as e:
            # Check for unique constraint violation
            error_msg = str(e).lower()
            if "unique" in error_msg or "duplicate" in error_msg:
                raise StorageError(
                    message=f"Connection already exists for {gmail_address}",
                    code="query_failed",
                    details={"gmail_address": gmail_address, "error": str(e)},
                ) from e
            raise StorageError(
                message=f"Failed to create connection: {e}",
                code="query_failed",
                details={"error": str(e)},
            ) from e

        if not result.data:
            raise StorageError(
                message="Failed to create connection",
                code="query_failed",
            )

        return self._dict_to_connection(result.data[0])

    async def get_connection(self, connection_id: str) -> Connection | None:
        """Get a connection by ID."""
        client = self._get_client()
        result = (
            client.table("gmail_connections")
            .select("*")
            .eq("id", connection_id)
            .execute()
        )
        return self._dict_to_connection(result.data[0]) if result.data else None

    async def get_connection_by_user_and_email(
        self,
        user_id: str,
        gmail_address: str,
    ) -> Connection | None:
        """Get a connection by user ID and Gmail address."""
        client = self._get_client()
        result = (
            client.table("gmail_connections")
            .select("*")
            .eq("user_id", user_id)
            .eq("gmail_address", gmail_address)
            .execute()
        )
        return self._dict_to_connection(result.data[0]) if result.data else None

    async def list_connections(
        self,
        user_id: str | None = None,
        include_inactive: bool = False,
    ) -> list[Connection]:
        """List connections, optionally filtered by user."""
        client = self._get_client()
        query = client.table("gmail_connections").select("*")

        if user_id:
            query = query.eq("user_id", user_id)

        if not include_inactive:
            query = query.eq("is_active", True)

        result = query.order("created_at", desc=True).execute()
        return [self._dict_to_connection(row) for row in result.data]

    async def update_connection_tokens(
        self,
        connection_id: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        token_expires_at: datetime,
    ) -> Connection:
        """Update a connection's tokens after refresh."""
        client = self._get_client()

        data: dict[str, Any] = {
            "access_token_encrypted": access_token_encrypted,
            "token_expires_at": token_expires_at.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if refresh_token_encrypted:
            data["refresh_token_encrypted"] = refresh_token_encrypted

        result = (
            client.table("gmail_connections")
            .update(data)
            .eq("id", connection_id)
            .execute()
        )

        if not result.data:
            raise StorageError(
                message=f"Connection not found: {connection_id}",
                code="query_failed",
            )

        return self._dict_to_connection(result.data[0])

    async def update_connection_last_used(self, connection_id: str) -> None:
        """Update a connection's last_used_at timestamp."""
        client = self._get_client()
        client.table("gmail_connections").update(
            {"last_used_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", connection_id).execute()

    async def deactivate_connection(self, connection_id: str) -> None:
        """Mark a connection as inactive."""
        client = self._get_client()
        client.table("gmail_connections").update(
            {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", connection_id).execute()

    async def delete_connection(self, connection_id: str) -> None:
        """Permanently delete a connection."""
        client = self._get_client()
        client.table("gmail_connections").delete().eq("id", connection_id).execute()

    async def get_expiring_connections(
        self,
        expires_before: datetime,
    ) -> list[Connection]:
        """Get connections with tokens expiring before a given time."""
        client = self._get_client()
        result = (
            client.table("gmail_connections")
            .select("*")
            .eq("is_active", True)
            .lt("token_expires_at", expires_before.isoformat())
            .execute()
        )
        return [self._dict_to_connection(row) for row in result.data]

    # =========================================================================
    # OAuth State Methods
    # =========================================================================

    async def create_oauth_state(
        self,
        state: str,
        user_id: str,
        scopes: list[str],
        redirect_uri: str,
        code_verifier: str,
        expires_at: datetime,
    ) -> OAuthState:
        """Create a new OAuth state for CSRF protection."""
        client = self._get_client()
        state_id = self._generate_id()
        now = datetime.now(timezone.utc).isoformat()

        data = {
            "id": state_id,
            "state": state,
            "user_id": user_id,
            "scopes": json.dumps(scopes),
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
            "expires_at": expires_at.isoformat(),
            "created_at": now,
        }

        result = client.table("oauth_states").insert(data).execute()

        if not result.data:
            raise StorageError(
                message="Failed to create OAuth state",
                code="query_failed",
            )

        return self._dict_to_oauth_state(result.data[0])

    async def get_oauth_state(self, state: str) -> OAuthState | None:
        """Get an OAuth state by state string."""
        client = self._get_client()
        result = client.table("oauth_states").select("*").eq("state", state).execute()
        return self._dict_to_oauth_state(result.data[0]) if result.data else None

    async def delete_oauth_state(self, state: str) -> None:
        """Delete an OAuth state after use."""
        client = self._get_client()
        client.table("oauth_states").delete().eq("state", state).execute()

    async def cleanup_expired_states(self) -> int:
        """Delete all expired OAuth states."""
        client = self._get_client()
        now = datetime.now(timezone.utc).isoformat()

        # Get count before delete (Supabase doesn't return count on delete)
        count_result = (
            client.table("oauth_states")
            .select("id", count="exact")
            .lt("expires_at", now)
            .execute()
        )
        count = count_result.count or 0

        # Delete expired states
        client.table("oauth_states").delete().lt("expires_at", now).execute()

        return count

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique ID."""
        return uuid.uuid4().hex

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        """Parse an ISO format datetime string."""
        if not value:
            return None
        # Handle various ISO formats
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)

    @classmethod
    def _dict_to_user(cls, data: dict[str, Any]) -> User:
        """Convert a dictionary to a User object."""
        return User(
            id=data["id"],
            external_user_id=data["external_user_id"],
            email=data.get("email"),
            created_at=cls._parse_datetime(data["created_at"]) or datetime.now(timezone.utc),
            updated_at=cls._parse_datetime(data["updated_at"]) or datetime.now(timezone.utc),
        )

    @classmethod
    def _dict_to_connection(cls, data: dict[str, Any]) -> Connection:
        """Convert a dictionary to a Connection object."""
        scopes = data["scopes"]
        if isinstance(scopes, str):
            scopes = json.loads(scopes)

        return Connection(
            id=data["id"],
            user_id=data["user_id"],
            gmail_address=data["gmail_address"],
            access_token_encrypted=data["access_token_encrypted"],
            refresh_token_encrypted=data["refresh_token_encrypted"],
            token_expires_at=cls._parse_datetime(data["token_expires_at"]) or datetime.now(timezone.utc),
            scopes=scopes,
            is_active=data["is_active"],
            created_at=cls._parse_datetime(data["created_at"]) or datetime.now(timezone.utc),
            updated_at=cls._parse_datetime(data["updated_at"]) or datetime.now(timezone.utc),
            last_used_at=cls._parse_datetime(data.get("last_used_at")),
        )

    @classmethod
    def _dict_to_oauth_state(cls, data: dict[str, Any]) -> OAuthState:
        """Convert a dictionary to an OAuthState object."""
        scopes = data["scopes"]
        if isinstance(scopes, str):
            scopes = json.loads(scopes)

        return OAuthState(
            id=data["id"],
            state=data["state"],
            user_id=data["user_id"],
            scopes=scopes,
            redirect_uri=data["redirect_uri"],
            code_verifier=data["code_verifier"],
            expires_at=cls._parse_datetime(data["expires_at"]) or datetime.now(timezone.utc),
            created_at=cls._parse_datetime(data["created_at"]) or datetime.now(timezone.utc),
        )
