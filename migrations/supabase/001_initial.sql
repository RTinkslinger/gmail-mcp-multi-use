-- Gmail Multi-User MCP - Initial Schema for Supabase
-- Migration: 001_initial
-- Description: Create users, gmail_connections, and oauth_states tables

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Users Table
-- =============================================================================
-- Stores application users identified by their external user ID
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    external_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookup by external_user_id
CREATE INDEX IF NOT EXISTS idx_users_external_user_id ON users(external_user_id);

-- =============================================================================
-- Gmail Connections Table
-- =============================================================================
-- Stores OAuth connections between users and their Gmail accounts
CREATE TABLE IF NOT EXISTS gmail_connections (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gmail_address TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    scopes TEXT NOT NULL,  -- JSON array of scopes
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    UNIQUE(user_id, gmail_address)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_gmail_connections_user_id ON gmail_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_gmail_connections_token_expires ON gmail_connections(token_expires_at);
CREATE INDEX IF NOT EXISTS idx_gmail_connections_is_active ON gmail_connections(is_active);

-- =============================================================================
-- OAuth States Table
-- =============================================================================
-- Stores temporary OAuth flow states for CSRF protection
CREATE TABLE IF NOT EXISTS oauth_states (
    id TEXT PRIMARY KEY,
    state TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scopes TEXT NOT NULL,  -- JSON array of scopes
    redirect_uri TEXT NOT NULL,
    code_verifier TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for OAuth state lookup and cleanup
CREATE INDEX IF NOT EXISTS idx_oauth_states_state ON oauth_states(state);
CREATE INDEX IF NOT EXISTS idx_oauth_states_expires_at ON oauth_states(expires_at);

-- =============================================================================
-- Schema Migrations Table
-- =============================================================================
-- Tracks applied migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Trigger for updated_at
-- =============================================================================
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for gmail_connections table
DROP TRIGGER IF EXISTS update_gmail_connections_updated_at ON gmail_connections;
CREATE TRIGGER update_gmail_connections_updated_at
    BEFORE UPDATE ON gmail_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Row Level Security (RLS) - Optional
-- =============================================================================
-- Enable RLS on tables (can be customized based on auth strategy)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE gmail_connections ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE oauth_states ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- Record this migration
-- =============================================================================
INSERT INTO schema_migrations (version) VALUES ('001_initial')
ON CONFLICT (version) DO NOTHING;
