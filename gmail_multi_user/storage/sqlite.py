"""SQLite storage backend implementation.

This module provides an async SQLite storage backend for local development.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

import aiosqlite

from gmail_multi_user.exceptions import StorageError
from gmail_multi_user.storage.base import StorageBackend
from gmail_multi_user.types import Connection, OAuthState, User


class SQLiteBackend(StorageBackend):
    """SQLite storage backend for local development.

    Uses aiosqlite for async database operations. Supports both file-based
    databases and in-memory databases (use ":memory:" as path).

    Example:
        backend = SQLiteBackend("gmail_mcp.db")
        await backend.initialize()
        user = await backend.get_or_create_user("user_123")
    """

    def __init__(self, db_path: str) -> None:
        """Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory.
        """
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create database connection."""
        if self._connection is None:
            # Create parent directory if needed (not for :memory:)
            if self._db_path != ":memory:":
                Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

            self._connection = await aiosqlite.connect(self._db_path)
            self._connection.row_factory = aiosqlite.Row
            # Enable foreign keys
            await self._connection.execute("PRAGMA foreign_keys = ON")

        return self._connection

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    async def initialize(self) -> None:
        """Initialize the database with schema."""
        conn = await self._get_connection()

        # Create tables
        await conn.executescript(
            """
            -- Users table
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                external_user_id TEXT UNIQUE NOT NULL,
                email TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            -- Gmail connections table
            CREATE TABLE IF NOT EXISTS gmail_connections (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                gmail_address TEXT NOT NULL,
                access_token_encrypted TEXT NOT NULL,
                refresh_token_encrypted TEXT NOT NULL,
                token_expires_at TEXT NOT NULL,
                scopes TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                last_used_at TEXT,
                UNIQUE(user_id, gmail_address)
            );

            -- OAuth states table
            CREATE TABLE IF NOT EXISTS oauth_states (
                id TEXT PRIMARY KEY,
                state TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                scopes TEXT NOT NULL,
                redirect_uri TEXT NOT NULL,
                code_verifier TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            -- Schema migrations tracking
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT DEFAULT (datetime('now'))
            );

            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_gmail_connections_user_id
                ON gmail_connections(user_id);
            CREATE INDEX IF NOT EXISTS idx_gmail_connections_token_expires
                ON gmail_connections(token_expires_at);
            CREATE INDEX IF NOT EXISTS idx_oauth_states_expires_at
                ON oauth_states(expires_at);
            CREATE INDEX IF NOT EXISTS idx_oauth_states_state
                ON oauth_states(state);
        """
        )
        await conn.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def health_check(self) -> bool:
        """Check if the database is accessible."""
        try:
            conn = await self._get_connection()
            async with conn.execute("SELECT 1") as cursor:
                await cursor.fetchone()
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
        conn = await self._get_connection()

        # Try to get existing user
        async with conn.execute(
            "SELECT * FROM users WHERE external_user_id = ?",
            (external_user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                # Update email if provided and different
                if email and row["email"] != email:
                    await conn.execute(
                        "UPDATE users SET email = ?, updated_at = datetime('now') WHERE id = ?",
                        (email, row["id"]),
                    )
                    await conn.commit()
                    # Re-fetch updated row
                    async with conn.execute(
                        "SELECT * FROM users WHERE id = ?", (row["id"],)
                    ) as cursor2:
                        row = await cursor2.fetchone()

                return self._row_to_user(row)

        # Create new user
        user_id = self._generate_id()
        now = datetime.utcnow().isoformat()

        await conn.execute(
            """
            INSERT INTO users (id, external_user_id, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, external_user_id, email, now, now),
        )
        await conn.commit()

        return User(
            id=user_id,
            external_user_id=external_user_id,
            email=email,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    async def get_user_by_external_id(self, external_user_id: str) -> User | None:
        """Get a user by their external ID."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT * FROM users WHERE external_user_id = ?",
            (external_user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_user(row) if row else None

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get a user by their internal ID."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_user(row) if row else None

    async def list_users(self) -> list[User]:
        """List all users."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_user(row) for row in rows]

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
        conn = await self._get_connection()
        connection_id = self._generate_id()
        now = datetime.utcnow().isoformat()

        try:
            await conn.execute(
                """
                INSERT INTO gmail_connections
                (id, user_id, gmail_address, access_token_encrypted, refresh_token_encrypted,
                 token_expires_at, scopes, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    connection_id,
                    user_id,
                    gmail_address,
                    access_token_encrypted,
                    refresh_token_encrypted,
                    token_expires_at.isoformat(),
                    json.dumps(scopes),
                    now,
                    now,
                ),
            )
            await conn.commit()
        except aiosqlite.IntegrityError as e:
            raise StorageError(
                message=f"Connection already exists for {gmail_address}",
                code="query_failed",
                details={"gmail_address": gmail_address, "error": str(e)},
            ) from e

        return Connection(
            id=connection_id,
            user_id=user_id,
            gmail_address=gmail_address,
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            token_expires_at=token_expires_at,
            scopes=scopes,
            is_active=True,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            last_used_at=None,
        )

    async def get_connection(self, connection_id: str) -> Connection | None:
        """Get a connection by ID."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT * FROM gmail_connections WHERE id = ?",
            (connection_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_connection(row) if row else None

    async def get_connection_by_user_and_email(
        self,
        user_id: str,
        gmail_address: str,
    ) -> Connection | None:
        """Get a connection by user ID and Gmail address."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT * FROM gmail_connections WHERE user_id = ? AND gmail_address = ?",
            (user_id, gmail_address),
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_connection(row) if row else None

    async def list_connections(
        self,
        user_id: str | None = None,
        include_inactive: bool = False,
    ) -> list[Connection]:
        """List connections, optionally filtered by user."""
        conn = await self._get_connection()

        query = "SELECT * FROM gmail_connections WHERE 1=1"
        params: list = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if not include_inactive:
            query += " AND is_active = 1"

        query += " ORDER BY created_at DESC"

        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_connection(row) for row in rows]

    async def update_connection_tokens(
        self,
        connection_id: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        token_expires_at: datetime,
    ) -> Connection:
        """Update a connection's tokens after refresh."""
        conn = await self._get_connection()

        if refresh_token_encrypted:
            await conn.execute(
                """
                UPDATE gmail_connections
                SET access_token_encrypted = ?,
                    refresh_token_encrypted = ?,
                    token_expires_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    access_token_encrypted,
                    refresh_token_encrypted,
                    token_expires_at.isoformat(),
                    connection_id,
                ),
            )
        else:
            await conn.execute(
                """
                UPDATE gmail_connections
                SET access_token_encrypted = ?,
                    token_expires_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (access_token_encrypted, token_expires_at.isoformat(), connection_id),
            )
        await conn.commit()

        connection = await self.get_connection(connection_id)
        if not connection:
            raise StorageError(
                message=f"Connection not found: {connection_id}",
                code="query_failed",
            )
        return connection

    async def update_connection_last_used(self, connection_id: str) -> None:
        """Update a connection's last_used_at timestamp."""
        conn = await self._get_connection()
        await conn.execute(
            """
            UPDATE gmail_connections
            SET last_used_at = datetime('now')
            WHERE id = ?
            """,
            (connection_id,),
        )
        await conn.commit()

    async def deactivate_connection(self, connection_id: str) -> None:
        """Mark a connection as inactive."""
        conn = await self._get_connection()
        await conn.execute(
            """
            UPDATE gmail_connections
            SET is_active = 0, updated_at = datetime('now')
            WHERE id = ?
            """,
            (connection_id,),
        )
        await conn.commit()

    async def delete_connection(self, connection_id: str) -> None:
        """Permanently delete a connection."""
        conn = await self._get_connection()
        await conn.execute(
            "DELETE FROM gmail_connections WHERE id = ?",
            (connection_id,),
        )
        await conn.commit()

    async def get_expiring_connections(
        self,
        expires_before: datetime,
    ) -> list[Connection]:
        """Get connections with tokens expiring before a given time."""
        conn = await self._get_connection()
        async with conn.execute(
            """
            SELECT * FROM gmail_connections
            WHERE is_active = 1 AND token_expires_at < ?
            """,
            (expires_before.isoformat(),),
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_connection(row) for row in rows]

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
        conn = await self._get_connection()
        state_id = self._generate_id()
        now = datetime.utcnow().isoformat()

        await conn.execute(
            """
            INSERT INTO oauth_states
            (id, state, user_id, scopes, redirect_uri, code_verifier, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state_id,
                state,
                user_id,
                json.dumps(scopes),
                redirect_uri,
                code_verifier,
                expires_at.isoformat(),
                now,
            ),
        )
        await conn.commit()

        return OAuthState(
            id=state_id,
            state=state,
            user_id=user_id,
            scopes=scopes,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
            expires_at=expires_at,
            created_at=datetime.fromisoformat(now),
        )

    async def get_oauth_state(self, state: str) -> OAuthState | None:
        """Get an OAuth state by state string."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT * FROM oauth_states WHERE state = ?",
            (state,),
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_oauth_state(row) if row else None

    async def delete_oauth_state(self, state: str) -> None:
        """Delete an OAuth state after use."""
        conn = await self._get_connection()
        await conn.execute(
            "DELETE FROM oauth_states WHERE state = ?",
            (state,),
        )
        await conn.commit()

    async def cleanup_expired_states(self) -> int:
        """Delete all expired OAuth states."""
        conn = await self._get_connection()
        now = datetime.utcnow().isoformat()

        cursor = await conn.execute(
            "DELETE FROM oauth_states WHERE expires_at < ?",
            (now,),
        )
        await conn.commit()
        return cursor.rowcount

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique ID."""
        return uuid.uuid4().hex

    @staticmethod
    def _row_to_user(row: aiosqlite.Row) -> User:
        """Convert a database row to a User object."""
        return User(
            id=row["id"],
            external_user_id=row["external_user_id"],
            email=row["email"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    @staticmethod
    def _row_to_connection(row: aiosqlite.Row) -> Connection:
        """Convert a database row to a Connection object."""
        return Connection(
            id=row["id"],
            user_id=row["user_id"],
            gmail_address=row["gmail_address"],
            access_token_encrypted=row["access_token_encrypted"],
            refresh_token_encrypted=row["refresh_token_encrypted"],
            token_expires_at=datetime.fromisoformat(row["token_expires_at"]),
            scopes=json.loads(row["scopes"]),
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_used_at=(
                datetime.fromisoformat(row["last_used_at"])
                if row["last_used_at"]
                else None
            ),
        )

    @staticmethod
    def _row_to_oauth_state(row: aiosqlite.Row) -> OAuthState:
        """Convert a database row to an OAuthState object."""
        return OAuthState(
            id=row["id"],
            state=row["state"],
            user_id=row["user_id"],
            scopes=json.loads(row["scopes"]),
            redirect_uri=row["redirect_uri"],
            code_verifier=row["code_verifier"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
