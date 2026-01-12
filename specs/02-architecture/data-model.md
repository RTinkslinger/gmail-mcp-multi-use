# Data Model

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [Entity Relationship Diagram](#1-entity-relationship-diagram)
2. [Table Definitions](#2-table-definitions)
3. [SQLite Schema](#3-sqlite-schema)
4. [Supabase Schema](#4-supabase-schema)
5. [Migration Scripts](#5-migration-scripts)
6. [Index Strategy](#6-index-strategy)

---

## 1. Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA MODEL                                          │
│                                                                                  │
│                                                                                  │
│   ┌───────────────────┐           ┌───────────────────────────────────────┐    │
│   │      users        │           │          gmail_connections             │    │
│   ├───────────────────┤           ├───────────────────────────────────────┤    │
│   │ id (PK)           │──────────<│ user_id (FK)                          │    │
│   │ external_user_id  │     1:N   │ id (PK)                               │    │
│   │ email             │           │ gmail_address                          │    │
│   │ created_at        │           │ access_token_encrypted                 │    │
│   │ updated_at        │           │ refresh_token_encrypted                │    │
│   └───────────────────┘           │ token_expires_at                       │    │
│           │                       │ scopes                                 │    │
│           │                       │ is_active                              │    │
│           │                       │ created_at                             │    │
│           │                       │ updated_at                             │    │
│           │                       │ last_used_at                           │    │
│           │                       └───────────────────────────────────────┘    │
│           │                                                                     │
│           │ 1:N                                                                 │
│           ▼                                                                     │
│   ┌───────────────────┐                                                         │
│   │   oauth_states    │                                                         │
│   ├───────────────────┤                                                         │
│   │ id (PK)           │                                                         │
│   │ state (UNIQUE)    │                                                         │
│   │ user_id (FK)      │                                                         │
│   │ scopes            │                                                         │
│   │ redirect_uri      │                                                         │
│   │ code_verifier     │                                                         │
│   │ expires_at        │                                                         │
│   │ created_at        │                                                         │
│   └───────────────────┘                                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Table Definitions

### 2.1 users

Stores developer's user identifiers mapped to internal IDs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Internal unique identifier |
| `external_user_id` | VARCHAR(255) | UNIQUE, NOT NULL | Developer's user identifier |
| `email` | VARCHAR(255) | NULL | Optional user email (for debugging) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update time |

### 2.2 gmail_connections

Stores OAuth tokens for each Gmail account connection.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Connection identifier |
| `user_id` | UUID | FOREIGN KEY → users(id), NOT NULL | Owner user |
| `gmail_address` | VARCHAR(255) | NOT NULL | Connected Gmail address |
| `access_token_encrypted` | TEXT | NOT NULL | Fernet-encrypted access token |
| `refresh_token_encrypted` | TEXT | NOT NULL | Fernet-encrypted refresh token |
| `token_expires_at` | TIMESTAMP | NOT NULL | Access token expiration |
| `scopes` | TEXT[] / JSON | NOT NULL | Granted OAuth scopes |
| `is_active` | BOOLEAN | DEFAULT TRUE | Connection still valid |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Connection created |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last token refresh |
| `last_used_at` | TIMESTAMP | NULL | Last API call |

**Unique Constraint:** `(user_id, gmail_address)` - One connection per Gmail per user

### 2.3 oauth_states

Temporary storage for OAuth flow state (CSRF protection).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Internal ID |
| `state` | VARCHAR(255) | UNIQUE, NOT NULL | OAuth state parameter |
| `user_id` | UUID | FOREIGN KEY → users(id), NOT NULL | User initiating OAuth |
| `scopes` | TEXT[] / JSON | NOT NULL | Requested scopes |
| `redirect_uri` | VARCHAR(500) | NOT NULL | Callback URL |
| `code_verifier` | VARCHAR(255) | NOT NULL | PKCE code verifier |
| `expires_at` | TIMESTAMP | NOT NULL | State expiration (10 min) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | State created |

---

## 3. SQLite Schema

```sql
-- migrations/sqlite/001_initial.sql

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    external_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Gmail connections table
CREATE TABLE IF NOT EXISTS gmail_connections (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gmail_address TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TEXT NOT NULL,
    scopes TEXT NOT NULL,  -- JSON array stored as text
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    last_used_at TEXT,

    UNIQUE(user_id, gmail_address)
);

-- OAuth states table
CREATE TABLE IF NOT EXISTS oauth_states (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    state TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scopes TEXT NOT NULL,  -- JSON array stored as text
    redirect_uri TEXT NOT NULL,
    code_verifier TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
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

-- Trigger to update updated_at
CREATE TRIGGER IF NOT EXISTS update_users_timestamp
    AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_gmail_connections_timestamp
    AFTER UPDATE ON gmail_connections
BEGIN
    UPDATE gmail_connections SET updated_at = datetime('now') WHERE id = NEW.id;
END;
```

---

## 4. Supabase Schema

```sql
-- migrations/supabase/001_initial.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gmail connections table
CREATE TABLE IF NOT EXISTS gmail_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gmail_address VARCHAR(255) NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    scopes TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(user_id, gmail_address)
);

-- OAuth states table
CREATE TABLE IF NOT EXISTS oauth_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scopes TEXT[] NOT NULL,
    redirect_uri VARCHAR(500) NOT NULL,
    code_verifier VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_gmail_connections_user_id
    ON gmail_connections(user_id);

CREATE INDEX IF NOT EXISTS idx_gmail_connections_token_expires
    ON gmail_connections(token_expires_at);

CREATE INDEX IF NOT EXISTS idx_gmail_connections_active
    ON gmail_connections(is_active) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_oauth_states_expires_at
    ON oauth_states(expires_at);

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_gmail_connections_updated_at ON gmail_connections;
CREATE TRIGGER update_gmail_connections_updated_at
    BEFORE UPDATE ON gmail_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (optional, for multi-tenant scenarios)
-- Not needed for single-deployment, but useful if sharing Supabase
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE gmail_connections ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE oauth_states ENABLE ROW LEVEL SECURITY;
```

---

## 5. Migration Scripts

### 5.1 Migration Tracking

```sql
-- Both SQLite and Supabase

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 Python Migration Runner

```python
# gmail_multi_user/storage/migrations.py

class MigrationRunner:
    """Run database migrations."""

    MIGRATIONS = [
        "001_initial",
        # Future migrations will be added here
    ]

    def __init__(self, storage: StorageBackend):
        self._storage = storage

    async def run_pending(self) -> list[str]:
        """Run all pending migrations."""
        applied = await self._get_applied_migrations()
        pending = [m for m in self.MIGRATIONS if m not in applied]

        for migration in pending:
            await self._apply_migration(migration)

        return pending

    async def _get_applied_migrations(self) -> set[str]:
        """Get set of already applied migrations."""
        # Query schema_migrations table

    async def _apply_migration(self, version: str) -> None:
        """Apply a single migration."""
        # Load and execute migration SQL
        # Record in schema_migrations
```

---

## 6. Index Strategy

### 6.1 Primary Queries and Their Indexes

| Query Pattern | Index | Rationale |
|--------------|-------|-----------|
| Get user by external_id | `users(external_user_id)` UNIQUE | Lookup on every OAuth flow |
| Get connections for user | `gmail_connections(user_id)` | List user's connections |
| Get connection by id | Primary key | Get single connection |
| Find expiring tokens | `gmail_connections(token_expires_at)` | Background refresh job |
| Find active connections | `gmail_connections(is_active)` WHERE TRUE | List active only |
| Get OAuth state | `oauth_states(state)` UNIQUE | OAuth callback validation |
| Cleanup expired states | `oauth_states(expires_at)` | Periodic cleanup |

### 6.2 Index Recommendations

```sql
-- Essential indexes (already in schema)
CREATE INDEX idx_gmail_connections_user_id ON gmail_connections(user_id);
CREATE INDEX idx_gmail_connections_token_expires ON gmail_connections(token_expires_at);
CREATE INDEX idx_oauth_states_expires_at ON oauth_states(expires_at);

-- Performance optimization (add if needed)
-- Partial index for active connections only
CREATE INDEX idx_gmail_connections_active_users
    ON gmail_connections(user_id)
    WHERE is_active = TRUE;

-- Covering index for token refresh queries
CREATE INDEX idx_gmail_connections_refresh
    ON gmail_connections(token_expires_at, id, refresh_token_encrypted)
    WHERE is_active = TRUE;
```

### 6.3 Query Patterns

```python
# Pattern 1: Get user's active connections
SELECT * FROM gmail_connections
WHERE user_id = ? AND is_active = TRUE;
# Uses: idx_gmail_connections_user_id

# Pattern 2: Find tokens expiring soon
SELECT * FROM gmail_connections
WHERE is_active = TRUE
  AND token_expires_at < NOW() + INTERVAL '5 minutes';
# Uses: idx_gmail_connections_token_expires

# Pattern 3: Cleanup expired OAuth states
DELETE FROM oauth_states
WHERE expires_at < NOW();
# Uses: idx_oauth_states_expires_at

# Pattern 4: Get or create user
INSERT INTO users (external_user_id, email)
VALUES (?, ?)
ON CONFLICT (external_user_id) DO UPDATE
SET email = EXCLUDED.email
RETURNING *;
# Uses: users(external_user_id) unique constraint
```

---

## 7. Data Types Reference

### 7.1 Python Data Classes

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: str
    external_user_id: str
    email: str | None
    created_at: datetime
    updated_at: datetime

@dataclass
class Connection:
    id: str
    user_id: str
    gmail_address: str
    access_token_encrypted: str
    refresh_token_encrypted: str
    token_expires_at: datetime
    scopes: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None

@dataclass
class OAuthState:
    id: str
    state: str
    user_id: str
    scopes: list[str]
    redirect_uri: str
    code_verifier: str
    expires_at: datetime
    created_at: datetime

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
```

### 7.2 Scope Storage Format

**SQLite:** JSON string
```json
["gmail.readonly", "gmail.send"]
```

**Supabase:** PostgreSQL array
```sql
ARRAY['gmail.readonly', 'gmail.send']::TEXT[]
```

### 7.3 Token Encryption Format

Tokens are encrypted using Fernet (AES-128-CBC + HMAC-SHA256):

```python
# Encryption
fernet = Fernet(key)
encrypted = fernet.encrypt(token.encode()).decode()
# Result: "gAAAAABk..." (base64-encoded ciphertext)

# Decryption
token = fernet.decrypt(encrypted.encode()).decode()
```
