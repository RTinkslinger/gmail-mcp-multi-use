-- Gmail Multi-User MCP: Initial SQLite Schema
-- Version: 001
-- Date: 2026-01-12

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users table
-- Stores developer's user identifiers mapped to internal IDs
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    external_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Gmail connections table
-- Stores OAuth tokens for each Gmail account connection
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
-- Temporary storage for OAuth flow state (CSRF protection)
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

-- Trigger to update updated_at on users
CREATE TRIGGER IF NOT EXISTS update_users_timestamp
    AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger to update updated_at on gmail_connections
CREATE TRIGGER IF NOT EXISTS update_gmail_connections_timestamp
    AFTER UPDATE ON gmail_connections
BEGIN
    UPDATE gmail_connections SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Mark migration as applied
INSERT OR IGNORE INTO schema_migrations (version) VALUES ('001_initial');
