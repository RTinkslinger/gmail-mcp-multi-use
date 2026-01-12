# Product Requirements Document (PRD)

## gmail-multi-user-mcp

**Version:** 2.3  
**Date:** January 12, 2026  
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Vision

Build an **open-source Python library and MCP server** that abstracts the complexity of Gmail OAuth integration for developers building agentic workflows and consumer applications. Developers should be able to add multi-user Gmail capabilities by simply adding a config file to their project.

### 1.2 Problem Statement

Developers building AI agents and automation tools need to access their end-users' Gmail accounts. Currently, this requires:

1. Setting up a Google Cloud Project
2. Configuring OAuth consent screens and credentials
3. Implementing OAuth flows (authorization codes, PKCE, token exchange)
4. Managing token storage (encrypted, per-user)
5. Handling token refresh (Google access tokens expire in 1 hour)
6. Learning the Gmail API (threading, labels, MIME parsing, base64 encoding)
7. Handling Gmail API rate limits and quotas

**This is 2-4 weeks of work before a developer can send their first email programmatically.**

### 1.3 Solution

An **open-source Python package** that provides:

- **Hybrid distribution**: Use as a library (import and call) OR as an MCP server (for AI agents)
- **Config-file simplicity**: Add `gmail_config.yaml` to your project and you're ready
- **Built-in multi-user OAuth**: End-users authenticate with their Google account via pre-built flow
- **Automatic token management**: Refresh tokens, encryption, and storage handled automatically
- **Comprehensive Gmail operations**: Search, read, send, draft, labels, attachments
- **Flexible storage backends**: Supabase (production) or SQLite (local development)
- **Zero cost to us**: Developers bring their own credentials and infrastructure

### 1.4 Distribution Model

**Package name:** `gmail-multi-user-mcp`

**Two ways to use the same package:**

| Usage Mode | Installation | Best For |
|------------|--------------|----------|
| **As MCP Server** | `pip install gmail-multi-user-mcp` then `gmail-mcp serve` | Claude Code, AI agents, conversational Gmail access |
| **As Library** | `pip install gmail-multi-user-mcp` then `from gmail_multi_user import GmailClient` | Traditional apps, backend services, programmatic control |

```
┌─────────────────────────────────────────────────────────────────┐
│                     gmail-multi-user-mcp                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Core Library                              ││
│  │  gmail_multi_user/                                          ││
│  │  ├── client.py      (GmailClient - main interface)          ││
│  │  ├── oauth.py       (OAuth flow management)                 ││
│  │  ├── tokens.py      (Token storage & refresh)               ││
│  │  ├── gmail_api.py   (Gmail API wrapper)                     ││
│  │  └── config.py      (Configuration loading)                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                  │
│  ┌─────────────────────┐       ┌─────────────────────────────┐ │
│  │   Use as Library    │       │    Use as MCP Server        │ │
│  │                     │       │                             │ │
│  │  from gmail_multi_  │       │  $ gmail-mcp serve          │ │
│  │  user import Gmail  │       │                             │ │
│  │  Client             │       │  Exposes library as MCP     │ │
│  │                     │       │  tools for AI agents        │ │
│  └─────────────────────┘       └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.5 What Developers Provide

| Requirement | Free Tier Available? | Notes |
|-------------|---------------------|-------|
| Supabase project | ✅ Yes | Or use SQLite for local dev |
| Google Cloud project | ✅ Yes | Gmail API is free |
| Hosting (for MCP server) | ✅ Yes | Can run locally |
| Domain (for OAuth redirect) | ❌ localhost works | Needed only for production |

**Estimated cost:** $0 for development, $0-25/month for production (Supabase paid tier if needed)

### 1.6 Deployment Modes & Primary Use Cases

Understanding when to use MCP server vs library import is critical:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT DECISION TREE                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     What are you building?                           │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│           ┌──────────────────────┼──────────────────────┐                  │
│           ▼                      ▼                      ▼                  │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│  │ Prototyping     │   │ Production app  │   │ Production app          │   │
│  │ with Claude     │   │ in Python       │   │ in TypeScript/Go/Rust   │   │
│  │ Code/Desktop    │   │                 │   │                         │   │
│  └────────┬────────┘   └────────┬────────┘   └────────────┬────────────┘   │
│           │                     │                         │                 │
│           ▼                     ▼                         ▼                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│  │ LOCAL MCP       │   │ LIBRARY IMPORT  │   │ REMOTE MCP SERVER       │   │
│  │ (stdio)         │   │ (no MCP)        │   │ (HTTP, as sidecar)      │   │
│  │                 │   │                 │   │                         │   │
│  │ gmail-mcp serve │   │ from gmail_     │   │ gmail-mcp serve         │   │
│  │ --transport     │   │ multi_user      │   │ --transport http        │   │
│  │ stdio           │   │ import Gmail    │   │ --host 0.0.0.0          │   │
│  │                 │   │ Client          │   │                         │   │
│  └─────────────────┘   └─────────────────┘   └─────────────────────────┘   │
│                                                                             │
│  PRIMARY USE CASE    PRIMARY USE CASE       SECONDARY USE CASE             │
│  (Development)       (Production)           (Production, non-Python)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.6.1 Primary: Local MCP Server for Claude Code/Desktop (Prototyping)

**When:** Developer is prototyping, experimenting, or building with Claude Code/Desktop

**How:**
```bash
gmail-mcp serve --transport stdio
```

**Characteristics:**
- Runs on developer's local machine
- Uses stdio transport (simplest)
- Developer's own Gmail accounts for testing
- SQLite storage (local file)
- Config from local `gmail_config.yaml`

**This is the "vibe coding" experience** — instant Gmail capabilities in Claude.

#### 1.6.2 Primary: Library Import for Python Production Apps

**When:** Developer is building a production application, backend service, or custom AI agent in Python

**How:**
```python
from gmail_multi_user import GmailClient

client = GmailClient()
messages = client.search(user_id="user_123", query="is:unread")
```

**Characteristics:**
- No MCP server process needed
- Direct function calls (faster, simpler)
- Full programmatic control
- Supabase storage (production-ready)
- Config from environment variables

**This is the production path for most developers** — the library provides all Gmail functionality without MCP overhead.

#### 1.6.3 Secondary: Remote MCP Server for Non-Python Production Apps

**When:** Developer is building a production agent in TypeScript, Go, Rust, or another non-Python language and needs our multi-user Gmail abstraction

**How:**
```yaml
# docker-compose.yml
services:
  my-typescript-agent:
    build: ./agent
    environment:
      GMAIL_MCP_URL: http://gmail-mcp:8000

  gmail-mcp:
    image: gmail-multi-user-mcp
    command: gmail-mcp serve --transport http --host 0.0.0.0
    environment:
      GMAIL_MCP_SERVER_AUTH_TOKEN: ${INTERNAL_TOKEN}
      # ... other config from env vars
```

**Characteristics:**
- Runs as a sidecar container/service
- HTTP transport with authentication
- Called over internal network
- Supabase storage (shared with main app)
- Config from environment variables

**This is the cross-language integration path** — when you can't import Python directly.

#### 1.6.4 Decision Matrix

| Scenario | Use Mode | Transport | Storage | Config Source |
|----------|----------|-----------|---------|---------------|
| Prototyping with Claude Code | Local MCP | stdio | SQLite | Local file |
| Python backend/agent | Library import | N/A | Supabase | Env vars |
| Python CLI tool | Library import | N/A | SQLite | Local file |
| TypeScript/Go/Rust agent | Remote MCP | HTTP | Supabase | Env vars |
| Microservice (Gmail as shared service) | Remote MCP | HTTP | Supabase | Env vars |

#### 1.6.5 Why Library-First Architecture Matters

The MCP server is intentionally a **thin wrapper** over the core library:

```
┌─────────────────────────────────────────────────────────────────┐
│                 gmail-multi-user-mcp                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Core Library (gmail_multi_user/)               ││
│  │                                                             ││
│  │  - OAuth flow          - Token management                   ││
│  │  - Gmail API wrapper   - Storage backends                   ││
│  │  - Encryption          - Configuration                      ││
│  │                                                             ││
│  │  THIS IS WHERE ALL THE VALUE LIVES                          ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                  │
│  ┌─────────────────────┐       ┌─────────────────────────────┐ │
│  │   Library Import    │       │    MCP Server Wrapper       │ │
│  │   (Production)      │       │    (~200 lines of code)     │ │
│  │                     │       │                             │ │
│  │   Most users will   │       │   Exposes library as MCP    │ │
│  │   use this path     │       │   tools for Claude/agents   │ │
│  └─────────────────────┘       └─────────────────────────────┘ │
│                                                                 │
│       80% of production                20% of production        │
│       use cases                        use cases                │
└─────────────────────────────────────────────────────────────────┘
```

This architecture means:
- **Python developers** get the simplest, fastest integration (library import)
- **Non-Python developers** can still use our abstraction (MCP server)
- **Claude Code users** get instant prototyping capabilities (local MCP)
- **All paths** share the same battle-tested core logic

### 1.7 Multi-User Architecture: The Core Value Proposition

**This package exists to solve multi-user Gmail integration.** A developer's app serves many end-users, each connecting their own Gmail account.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    YOUR APP (built by developer)                            │
│                                                                             │
│         ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                │
│         │  End User   │   │  End User   │   │  End User   │   ... hundreds │
│         │  Alice      │   │  Bob        │   │  Carol      │      more      │
│         │  (u_001)    │   │  (u_002)    │   │  (u_003)    │                │
│         └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                │
│                │                 │                 │                        │
│                ▼                 ▼                 ▼                        │
│         ┌───────────┐     ┌───────────┐     ┌───────────┐                  │
│         │ Alice's   │     │ Bob's     │     │ Carol's   │                  │
│         │ Gmail     │     │ Gmail(s)  │     │ Gmail     │                  │
│         │           │     │           │     │           │                  │
│         │ alice@    │     │ bob@      │     │ carol@    │                  │
│         │ gmail.com │     │ gmail.com │     │ gmail.com │                  │
│         └───────────┘     │ bob.work@ │     └───────────┘                  │
│                           │ gmail.com │                                     │
│                           └───────────┘                                     │
│                                                                             │
│   Each user:                                                                │
│   • Connects their OWN Gmail (not the developer's)                         │
│   • Authorizes via Google OAuth (sees developer's app name)                │
│   • Can connect multiple Gmail accounts                                    │
│   • Can revoke access anytime                                              │
│                                                                             │
│   Developer's agent:                                                        │
│   • Operates on behalf of each user                                        │
│   • Accesses ONLY that user's Gmail                                        │
│   • Never mixes up user data (enforced by user_id/connection_id)           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.7.1 The user_id vs connection_id Pattern

Two identifiers are used throughout the system:

| Identifier | What It Represents | Who Creates It | Example |
|------------|-------------------|----------------|---------|
| `user_id` | An end-user in developer's app | Developer | `"u_001"`, `"user_alice"`, `"auth0\|123"` |
| `connection_id` | A specific Gmail account | Our system | `"conn_abc123"` |

**Relationship:**
```
user_id: "u_002" (Bob)
    ├── connection_id: "conn_1" → bob@gmail.com
    └── connection_id: "conn_2" → bob.work@company.com

One user can have multiple Gmail connections.
```

**When to use which:**

| Operation | Use | Why |
|-----------|-----|-----|
| Generate OAuth URL | `user_id` | Don't know which Gmail yet |
| List user's connections | `user_id` | Get all accounts for a user |
| Search emails | `connection_id` | Search specific Gmail account |
| Send email | `connection_id` | Send FROM specific account |
| Check connection health | `connection_id` | Check specific account |

#### 1.7.2 Multi-User Code Example

**Library Mode:**
```python
from gmail_multi_user import GmailClient

client = GmailClient()

# ============================================================
# STEP 1: Each end-user connects their Gmail (during onboarding)
# ============================================================

# Alice wants to connect her Gmail
alice_auth = client.get_auth_url(
    user_id="u_001",  # Your identifier for Alice
    scopes=["gmail.readonly", "gmail.send"]
)
# → Redirect Alice to alice_auth["auth_url"]
# → Alice logs into HER Gmail, grants permission
# → Google redirects back, we store her tokens

# Bob wants to connect (he has 2 Gmail accounts)
bob_auth = client.get_auth_url(user_id="u_002")
# → Bob connects bob@gmail.com

bob_auth_2 = client.get_auth_url(user_id="u_002")  # Same user_id!
# → Bob connects bob.work@company.com

# Carol connects
carol_auth = client.get_auth_url(user_id="u_003")
# → Carol connects carol@gmail.com


# ============================================================
# STEP 2: Developer's agent operates on users' Gmail
# ============================================================

# Get Bob's connected accounts
bob_connections = client.list_connections(user_id="u_002")
# Returns:
# [
#   {"id": "conn_1", "gmail_address": "bob@gmail.com"},
#   {"id": "conn_2", "gmail_address": "bob.work@company.com"}
# ]

# Search Bob's personal Gmail
personal_emails = client.search(
    connection_id="conn_1",  # bob@gmail.com
    query="is:unread"
)

# Search Bob's work Gmail
work_emails = client.search(
    connection_id="conn_2",  # bob.work@company.com
    query="from:boss@company.com"
)

# Send email FROM Alice's account (not Bob's!)
alice_connections = client.list_connections(user_id="u_001")
client.send(
    connection_id=alice_connections[0]["id"],
    to=["friend@example.com"],
    subject="Hello!",
    body="This email is from Alice's Gmail"
)


# ============================================================
# STEP 3: Data isolation is enforced
# ============================================================

# This is IMPOSSIBLE - connection_id is tied to user_id
# Trying to access Alice's connection with Bob's user_id will fail
# The system enforces isolation at the database level
```

**MCP Mode (Claude Code):**
```
Developer: "Show me all connected users"

Claude: [reads users://list resource]
        "You have 3 users with Gmail connected:
         - u_001 (Alice): 1 connection
         - u_002 (Bob): 2 connections  
         - u_003 (Carol): 1 connection"

Developer: "Search Bob's work email for messages from his boss"

Claude: [reads users://u_002/connections to find work email]
        [calls gmail_search with connection_id for bob.work@]
        "Found 3 emails from boss@company.com in Bob's work inbox..."

Developer: "Draft a reply from Bob's work account"

Claude: [calls gmail_create_draft with connection_id="conn_2"]
        "Draft created in Bob's work Gmail (bob.work@company.com)"
```

#### 1.7.3 Scale This Supports

| Metric | Tier 1 (Current) | Notes |
|--------|------------------|-------|
| End-users per deployment | 10 - 10,000+ | Limited by Supabase plan |
| Gmail connections per user | Unlimited | Practical limit ~10 |
| Total connections | 100,000+ | With Supabase Pro |
| Concurrent operations | ~100/sec | Gmail API limits apply per-user |

---

## 2. Target Users

### 2.1 Primary: Developers Building Consumer AI Apps

- Building with Claude, GPT, or other LLM-powered systems
- Need Gmail access for their end-users (not just themselves)
- Want to focus on their application logic, not OAuth plumbing
- Comfortable with basic deployment (Docker, environment variables)
- May be using frameworks like LangChain, CrewAI, AutoGen, or custom MCP clients

**Target scale:** 10 to 10,000 end-users per developer

### 2.2 Secondary: End-Users (Developer's Customers)

- People who use applications built by our primary users
- Expect a familiar "Sign in with Google" experience
- Need assurance their email access is secure and revocable
- May connect multiple Gmail accounts

### 2.3 Out of Scope (v1)

- Enterprise/B2B developers (Outlook/Microsoft 365 users)
- Google Workspace admins (service account/domain-wide delegation)
- Developers wanting a fully managed hosted solution

---

## 3. Architecture Overview

### 3.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Developer's Infrastructure                              │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      gmail-multi-user-mcp                            │  │
│  │                                                                      │  │
│  │   ┌────────────────┐    ┌────────────────┐    ┌──────────────────┐  │  │
│  │   │  Config Loader │───▶│  Core Library  │───▶│   Gmail API      │  │  │
│  │   │                │    │                │    │   (Google)       │  │  │
│  │   │  Reads from:   │    │  - OAuth flow  │    └──────────────────┘  │  │
│  │   │  1. Env vars   │    │  - Token mgmt  │                          │  │
│  │   │  2. Local file │    │  - Gmail ops   │    ┌──────────────────┐  │  │
│  │   │  3. Home dir   │    │                │───▶│  Storage Backend │  │  │
│  │   └────────────────┘    └────────────────┘    │  (Supabase/SQL)  │  │  │
│  │                                │              └──────────────────┘  │  │
│  │                ┌───────────────┴───────────────┐                    │  │
│  │                ▼                               ▼                    │  │
│  │   ┌─────────────────────┐       ┌─────────────────────────────┐    │  │
│  │   │   Library Mode      │       │      MCP Server Mode        │    │  │
│  │   │   (import & call)   │       │      (gmail-mcp serve)      │    │  │
│  │   └─────────────────────┘       └─────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Storage Backends

The package supports two storage backends:

| Backend | Use Case | Setup Complexity | Persistence |
|---------|----------|------------------|-------------|
| **SQLite** | Local development, testing, single-machine deployments | Zero (just a file path) | Local file |
| **Supabase** | Production, multi-instance deployments | Low (create project, run migrations) | Cloud |

**SQLite Mode:**
```yaml
database:
  type: sqlite
  sqlite_path: ./gmail_tokens.db  # Or :memory: for tests
```

**Supabase Mode:**
```yaml
database:
  type: supabase
  supabase_url: https://xxx.supabase.co
  supabase_service_key: eyJ...
```

### 3.3 Data Model

```sql
-- Users table (maps to developer's user system)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_user_id VARCHAR(255) UNIQUE NOT NULL,  -- Developer's user ID
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Gmail connections (one user can have multiple Gmail accounts)
CREATE TABLE gmail_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    gmail_address VARCHAR(255) NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMP NOT NULL,
    scopes TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, gmail_address)
);

-- OAuth state (temporary, for CSRF protection)
CREATE TABLE oauth_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scopes TEXT[] NOT NULL,
    redirect_uri VARCHAR(500) NOT NULL,
    code_verifier VARCHAR(255),  -- For PKCE
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for cleanup job
CREATE INDEX idx_oauth_states_expires_at ON oauth_states(expires_at);
CREATE INDEX idx_gmail_connections_token_expires ON gmail_connections(token_expires_at);
```

### 3.4 Configuration System

#### 3.4.1 Config File Priority (Highest to Lowest)

The package searches for configuration in this order:

```
1. Environment variables (GMAIL_MCP_*)     ← Always wins (for production/CI)
       ↓ (if not set)
2. File from GMAIL_MCP_CONFIG env var      ← Explicit path override
       ↓ (if not set)
3. Project-local files (in order):         ← For development convenience
   - ./gmail_config.yaml
   - ./gmail_config.yml
   - ./.gmail_config.yaml
       ↓ (if not found)
4. User home directory:                    ← For personal defaults
   - Linux: ~/.config/gmail-mcp/config.yaml
   - macOS: ~/Library/Application Support/gmail-mcp/config.yaml
   - Windows: %APPDATA%\gmail-mcp\config.yaml
       ↓ (if not found)
5. Error with clear message                ← Tell developer what's missing
```

**Environment variables override file values**, allowing production deployments to inject secrets without files.

#### 3.4.2 Config File Format

```yaml
# gmail_config.yaml

# Database backend: 'supabase' (production) or 'sqlite' (local dev)
database:
  type: supabase  # or 'sqlite'
  
  # SQLite settings (only if type: sqlite)
  sqlite_path: ./gmail_tokens.db  # or ':memory:' for testing
  
  # Supabase settings (only if type: supabase)
  supabase_url: https://your-project.supabase.co
  supabase_service_key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Google OAuth settings (required)
google:
  client_id: your-client-id.apps.googleusercontent.com
  client_secret: GOCSPX-your-secret
  redirect_uri: http://localhost:8000/oauth/callback

# Encryption key for token storage (required)
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
encryption:
  key: your-64-character-hex-key-here

# Server settings (only for MCP server mode)
server:
  host: 127.0.0.1
  port: 8000
  # Optional: Bearer token for API authentication
  auth_token: optional-secret-for-remote-access
```

#### 3.4.3 Environment Variable Mappings

| Environment Variable | Config Path | Example |
|---------------------|-------------|---------|
| `GMAIL_MCP_CONFIG` | (file path) | `/etc/gmail-mcp/config.yaml` |
| `GMAIL_MCP_DATABASE_TYPE` | `database.type` | `supabase` or `sqlite` |
| `GMAIL_MCP_SQLITE_PATH` | `database.sqlite_path` | `./tokens.db` |
| `GMAIL_MCP_SUPABASE_URL` | `database.supabase_url` | `https://xxx.supabase.co` |
| `GMAIL_MCP_SUPABASE_KEY` | `database.supabase_service_key` | `eyJ...` |
| `GMAIL_MCP_GOOGLE_CLIENT_ID` | `google.client_id` | `xxx.apps.googleusercontent.com` |
| `GMAIL_MCP_GOOGLE_CLIENT_SECRET` | `google.client_secret` | `GOCSPX-xxx` |
| `GMAIL_MCP_GOOGLE_REDIRECT_URI` | `google.redirect_uri` | `http://localhost:8000/oauth/callback` |
| `GMAIL_MCP_ENCRYPTION_KEY` | `encryption.key` | `64-char-hex-string` |
| `GMAIL_MCP_SERVER_HOST` | `server.host` | `0.0.0.0` |
| `GMAIL_MCP_SERVER_PORT` | `server.port` | `8000` |
| `GMAIL_MCP_SERVER_AUTH_TOKEN` | `server.auth_token` | `secret-token` |

#### 3.4.4 Config Loading Examples

**Scenario 1: Local development with SQLite**
```yaml
# ./gmail_config.yaml
database:
  type: sqlite
  sqlite_path: ./dev_tokens.db

google:
  client_id: xxx.apps.googleusercontent.com
  client_secret: GOCSPX-xxx
  redirect_uri: http://localhost:8000/oauth/callback

encryption:
  key: dev-key-not-for-production-use-generate-real-one
```

**Scenario 2: Production with environment variables (no file)**
```bash
# In your deployment platform (Render, Railway, K8s, etc.)
GMAIL_MCP_DATABASE_TYPE=supabase
GMAIL_MCP_SUPABASE_URL=https://prod.supabase.co
GMAIL_MCP_SUPABASE_KEY=${{ secrets.SUPABASE_KEY }}
GMAIL_MCP_GOOGLE_CLIENT_ID=${{ secrets.GOOGLE_CLIENT_ID }}
GMAIL_MCP_GOOGLE_CLIENT_SECRET=${{ secrets.GOOGLE_CLIENT_SECRET }}
GMAIL_MCP_GOOGLE_REDIRECT_URI=https://myapp.com/oauth/callback
GMAIL_MCP_ENCRYPTION_KEY=${{ secrets.ENCRYPTION_KEY }}
```

**Scenario 3: CI/CD testing with in-memory SQLite**
```yaml
# .github/workflows/test.yml
env:
  GMAIL_MCP_DATABASE_TYPE: sqlite
  GMAIL_MCP_SQLITE_PATH: ":memory:"
  GMAIL_MCP_GOOGLE_CLIENT_ID: test-client-id
  GMAIL_MCP_GOOGLE_CLIENT_SECRET: test-secret
  GMAIL_MCP_ENCRYPTION_KEY: test-key-for-ci-only
```

**Scenario 4: Shared config across projects (user home)**
```bash
# Set up once
mkdir -p ~/.config/gmail-mcp
cat > ~/.config/gmail-mcp/config.yaml << EOF
database:
  type: sqlite
  sqlite_path: ~/.config/gmail-mcp/tokens.db

google:
  client_id: my-dev-client.apps.googleusercontent.com
  client_secret: GOCSPX-my-dev-secret
  redirect_uri: http://localhost:8000/oauth/callback

encryption:
  key: my-personal-dev-key
EOF

# Now works in any project directory
cd ~/any-project
gmail-mcp serve  # Uses ~/.config/gmail-mcp/config.yaml
```

### 3.5 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.10+ | Best MCP SDK, async support, broad adoption |
| **MCP Framework** | FastMCP | Official Anthropic SDK, clean API |
| **Database (prod)** | Supabase (PostgreSQL) | Free tier, managed, easy setup |
| **Database (dev)** | SQLite | Zero setup, portable, good for testing |
| **HTTP Server** | Starlette/Uvicorn | Async, lightweight, used by FastMCP |
| **Config Parsing** | PyYAML + Pydantic | Validation, type safety |
| **Encryption** | cryptography (Fernet) | Industry standard, simple API |
| **Gmail API** | google-api-python-client | Official Google library |

---

## 4. Functional Requirements

### 4.1 Developer Experience

#### 4.1.1 Installation

```bash
pip install gmail-multi-user-mcp
```

#### 4.1.2 Quick Start (Library Mode)

```python
from gmail_multi_user import GmailClient

# Automatically loads config from gmail_config.yaml or environment
client = GmailClient()

# Connect a user (returns OAuth URL)
auth_url = client.get_auth_url(
    user_id="user_123",
    scopes=["gmail.readonly", "gmail.send"]
)
print(f"Send user to: {auth_url}")

# After user completes OAuth, you'll receive a callback
# The library handles token storage automatically

# Now use Gmail
messages = client.search(user_id="user_123", query="is:unread")
for msg in messages:
    print(f"From: {msg.sender}, Subject: {msg.subject}")

# Send an email
client.send(
    user_id="user_123",
    to=["recipient@example.com"],
    subject="Hello from my app!",
    body="This email was sent via gmail-multi-user-mcp"
)
```

#### 4.1.3 Quick Start (MCP Server Mode)

**Step 1: Create config file**
```bash
# Copy the example config
curl -o gmail_config.yaml https://raw.githubusercontent.com/yourorg/gmail-multi-user-mcp/main/gmail_config.yaml.example

# Edit with your credentials
nano gmail_config.yaml
```

**Step 2: Start the MCP server**
```bash
# HTTP transport (for remote access)
gmail-mcp serve

# Or stdio transport (for Claude Desktop local)
gmail-mcp serve --transport stdio
```

**Step 3: Configure Claude Desktop / Claude Code**

For stdio (local, simpler):
```json
{
  "mcpServers": {
    "gmail": {
      "command": "gmail-mcp",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

For HTTP (remote, more flexible):
```json
{
  "mcpServers": {
    "gmail": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**Step 4: Use Gmail via Claude**
```
You: "Search my Gmail for unread emails from the last week"
Claude: [Calls gmail_search tool]

You: "Summarize the email from Alice and draft a reply"
Claude: [Calls gmail_get_message, then gmail_create_draft]
```

#### 4.1.4 Setup Time Comparison

| Task | Without this package | With gmail-multi-user-mcp |
|------|---------------------|---------------------------|
| Google Cloud setup | 30 min | 30 min (still required) |
| OAuth implementation | 4-8 hours | 0 (included) |
| Token storage | 2-4 hours | 0 (included) |
| Token refresh logic | 2-4 hours | 0 (included) |
| Gmail API wrapper | 4-8 hours | 0 (included) |
| **Total** | **12-24 hours** | **30 minutes** |

#### 4.1.3 User Identity Mapping

Developers must provide their own user identifier when calling MCP tools. This allows them to map their application's users to Gmail connections.

**How it works:**

1. Developer's app has its own user system (e.g., `user_123` in their database)
2. When requesting OAuth URL, developer passes `external_user_id: "user_123"`
3. Server creates/updates a `user` record in Supabase
4. All subsequent MCP calls use this `external_user_id`
5. Developer never needs to store internal user IDs

```python
# Example: Get auth URL for a user
result = await gmail_get_auth_url(
    external_user_id="user_123",  # Developer's user ID
    scopes=["gmail.readonly", "gmail.send"],
    redirect_uri="https://myapp.com/oauth/callback"
)
# Returns: { "auth_url": "https://accounts.google.com/...", "state": "..." }
```

**Benefits:**
- Developer doesn't need to sync user databases
- Multiple Gmail accounts per user supported
- Simple integration with any auth system

#### 4.1.4 Sandbox/Testing Mode

Developers can test without sending real emails:

**Sandbox Features:**
- `sandbox: true` flag on tool calls
- Simulated Gmail responses for testing
- Pre-populated test inbox with various email types
- Send operations log intent but don't actually send
- Useful for CI/CD pipelines

```python
# Sandbox mode
result = await gmail_send(
    connection_id="sandbox_connection",
    to=["test@example.com"],
    subject="Test email",
    body="This won't actually send",
    sandbox=True  # Returns success without sending
)
# Returns: { "id": "sandbox_msg_123", "sandbox": true }
```

**Test Connections:**
- Special `sandbox_connection` ID works without OAuth
- Returns realistic mock data
- Allows full integration testing

#### 4.1.3 End-User Connection Flow

```
Developer's App                    Gmail MCP Server                    Google
      │                                   │                               │
      │  1. User clicks "Connect Gmail"   │                               │
      │ ─────────────────────────────────▶│                               │
      │                                   │  2. Generate OAuth URL        │
      │  3. Redirect URL                  │     (with state, PKCE)        │
      │ ◀─────────────────────────────────│                               │
      │                                   │                               │
      │  4. User redirected to Google ────────────────────────────────────▶
      │                                   │                               │
      │                                   │  5. User consents             │
      │                                   │ ◀──────────────────────────────
      │                                   │                               │
      │                                   │  6. Exchange code for tokens  │
      │                                   │     (access_token,            │
      │                                   │      refresh_token)           │
      │                                   │                               │
      │  7. Success callback              │  8. Store tokens encrypted    │
      │ ◀─────────────────────────────────│     per-user                  │
      │                                   │                               │
```

### 4.2 MCP Tools (Gmail Operations)

#### 4.2.1 Authentication Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `gmail_get_auth_url` | Generate OAuth URL for user to connect | `user_id`, `scopes[]`, `redirect_uri` |
| `gmail_list_connections` | List connected Gmail accounts for a user | `user_id` |
| `gmail_disconnect` | Revoke access and delete tokens | `user_id`, `connection_id` |
| `gmail_check_connection` | Verify a connection is still valid | `connection_id` |

#### 4.2.2 Email Reading Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `gmail_search` | Search emails with Gmail query syntax | `connection_id`, `query`, `max_results`, `page_token` |
| `gmail_get_message` | Get full message content | `connection_id`, `message_id`, `format` (full/metadata/minimal) |
| `gmail_get_thread` | Get all messages in a thread | `connection_id`, `thread_id` |
| `gmail_list_labels` | List all labels (folders) | `connection_id` |
| `gmail_get_attachment` | Download an attachment | `connection_id`, `message_id`, `attachment_id` |

#### 4.2.3 Email Writing Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `gmail_send` | Send an email immediately | `connection_id`, `to[]`, `subject`, `body`, `cc[]`, `bcc[]`, `attachments[]`, `reply_to_message_id` |
| `gmail_create_draft` | Create a draft | `connection_id`, `to[]`, `subject`, `body`, ... |
| `gmail_update_draft` | Update existing draft | `connection_id`, `draft_id`, ... |
| `gmail_send_draft` | Send an existing draft | `connection_id`, `draft_id` |
| `gmail_delete_draft` | Delete a draft | `connection_id`, `draft_id` |

#### 4.2.4 Email Management Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `gmail_modify_labels` | Add/remove labels from messages | `connection_id`, `message_ids[]`, `add_labels[]`, `remove_labels[]` |
| `gmail_trash` | Move messages to trash | `connection_id`, `message_ids[]` |
| `gmail_untrash` | Remove from trash | `connection_id`, `message_ids[]` |
| `gmail_mark_read` | Mark as read | `connection_id`, `message_ids[]` |
| `gmail_mark_unread` | Mark as unread | `connection_id`, `message_ids[]` |
| `gmail_archive` | Archive messages | `connection_id`, `message_ids[]` |

#### 4.2.5 Batch Operations

| Tool | Description | Parameters |
|------|-------------|------------|
| `gmail_batch_get` | Get multiple messages efficiently | `connection_id`, `message_ids[]` |
| `gmail_batch_modify` | Modify multiple messages | `connection_id`, `message_ids[]`, `add_labels[]`, `remove_labels[]` |

### 4.3 Scope Management

#### 4.3.1 Available Scopes

| Scope | Description | Use Case |
|-------|-------------|----------|
| `gmail.readonly` | Read-only access | Inbox monitoring, search |
| `gmail.send` | Send emails only | Outbound campaigns |
| `gmail.compose` | Create drafts | Draft preparation |
| `gmail.modify` | Read + write (no delete) | Full inbox management |
| `gmail.labels` | Manage labels | Organization |
| `mail.google.com` | Full access | Complete control |

#### 4.3.2 Scope Enforcement

- Tools validate that the connection has required scopes before execution
- Error responses indicate which scope is missing
- Developers can request scope upgrade via re-authentication

---

## 5. Non-Functional Requirements

### 5.1 Security

| Requirement | Implementation |
|-------------|----------------|
| Token encryption at rest | Supabase Vault (AES-256-GCM) |
| Token encryption in transit | TLS 1.3 |
| Tenant isolation | PostgreSQL RLS policies |
| API authentication | API key + tenant ID in headers |
| OAuth security | PKCE, state parameter, nonce |
| Audit logging | All token operations logged |
| Token revocation | Immediate revocation via Google API |

### 5.2 Reliability

| Requirement | Target |
|-------------|--------|
| Uptime | 99.9% |
| Token refresh success rate | 99.99% |
| API response time (p95) | < 500ms (excluding Gmail API) |

### 5.3 Scalability

| Metric | Initial Target | Growth Target |
|--------|----------------|---------------|
| Tenants | 100 | 10,000 |
| Users per tenant | 1,000 | 100,000 |
| Connections per user | 5 | 10 |
| Requests per second | 100 | 10,000 |

### 5.4 Compliance

- **GDPR**: Users can request data export and deletion
- **SOC 2**: Audit logging, access controls
- **Google API ToS**: Comply with OAuth verification requirements

### 5.5 Token Lifecycle Management

#### 5.5.1 Proactive Token Refresh

We refresh tokens before they expire to ensure seamless API calls:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Token Refresh Timeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Token issued ──────► 45 min mark ──────► 60 min (expires)     │
│       │                    │                    │               │
│       │                    │                    │               │
│       ▼                    ▼                    ▼               │
│   Store token      Background job          Token invalid        │
│   expires_at       attempts refresh        if not refreshed     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Background Job (runs every 5 minutes):**
1. Query connections where `token_expires_at < NOW() + 15 minutes`
2. For each, attempt refresh with Google API
3. Update `access_token` and `token_expires_at`
4. If refresh fails → mark connection as `needs_reauth`

**On-Demand Refresh:**
- If token is expired when tool is called, refresh inline
- If refresh fails, return `connection_invalid` error

#### 5.5.2 Connection Status Checking (Polling)

Since we're using a polling model, developers check connection status via MCP tools:

```python
# Check if a connection is still valid
result = await gmail_check_connection(connection_id="conn_123")
# Returns: { "valid": true, "gmail_address": "user@gmail.com", "scopes": [...] }

# Or: { "valid": false, "reason": "refresh_token_revoked" }
```

**Recommended Patterns:**
- Check connection validity before critical operations
- Handle `connection_invalid` errors gracefully in your agent
- Prompt users to reconnect when needed

### 5.6 Rate Limiting

#### 5.6.1 Server-Level Rate Limiting (Optional)

Developers can configure rate limiting to protect their deployment:

```python
# config.py
RATE_LIMIT_ENABLED = True
RATE_LIMIT_REQUESTS_PER_MINUTE = 100
RATE_LIMIT_REQUESTS_PER_HOUR = 1000
```

#### 5.6.2 Gmail API Limits (Google's)

| Quota | Limit | Per |
|-------|-------|-----|
| Queries | 250 | User/second |
| Messages sent | 100 | User/day (free Gmail) |
| Messages sent | 2,000 | User/day (Workspace) |
| Batch requests | 100 | Operations/batch |

**Our Handling:**
- Track per-connection usage against Gmail limits
- Return `429` with `Retry-After` header when limits approached
- `gmail_get_quota` tool to check remaining quota

### 5.7 Message Format Handling

#### 5.7.1 Reading Messages

Messages are returned with parsed content:

```json
{
  "id": "msg_123",
  "thread_id": "thread_456",
  "subject": "Meeting tomorrow",
  "from": { "name": "Alice", "email": "alice@example.com" },
  "to": [{ "name": "Bob", "email": "bob@example.com" }],
  "date": "2026-01-12T10:30:00Z",
  "body_plain": "Hi Bob, let's meet tomorrow...",
  "body_html": "<html><body>Hi Bob...</body></html>",
  "attachments": [
    { "id": "att_789", "filename": "agenda.pdf", "mime_type": "application/pdf", "size": 12345 }
  ],
  "labels": ["INBOX", "IMPORTANT"]
}
```

#### 5.7.2 Sending Messages

We accept multiple formats:

```python
# Plain text
gmail_send(
    connection_id="...",
    to=["bob@example.com"],
    subject="Hello",
    body="Plain text message"
)

# HTML
gmail_send(
    connection_id="...",
    to=["bob@example.com"],
    subject="Hello",
    body="<h1>HTML message</h1>",
    content_type="html"
)

# With attachments (base64 encoded)
gmail_send(
    connection_id="...",
    to=["bob@example.com"],
    subject="Files attached",
    body="See attachments",
    attachments=[
        { "filename": "doc.pdf", "content": "base64...", "mime_type": "application/pdf" }
    ]
)
```

---

## 6. User Interface Requirements

### 6.1 No Hosted Dashboard (Self-Hosted Model)

Since developers deploy their own instances, we don't provide a hosted dashboard. Instead:

**Developer Tools:**
- Supabase Dashboard (for database management)
- Server logs (for debugging)
- CLI commands for common operations

**Provided CLI Commands:**
```bash
# Check server health
gmail-mcp health

# List all connections
gmail-mcp connections list

# Revoke a connection
gmail-mcp connections revoke <connection_id>

# Test Gmail API connectivity
gmail-mcp test --connection-id <id>

# Run token refresh manually
gmail-mcp refresh-tokens
```

### 6.2 End-User OAuth Flow

Developers can customize or use our default pages:

1. **Consent Initiation**: Developer redirects user to `/oauth/start?user_id=...`
2. **Google Consent**: User sees Google's standard OAuth consent screen
3. **Success Page**: Simple confirmation page (customizable via templates)
4. **Error Page**: Clear error messages with retry option

**Default Templates (Customizable):**
```
templates/
├── oauth_success.html    # "Gmail connected successfully!"
├── oauth_error.html      # "Connection failed: {error}"
└── oauth_revoked.html    # "Gmail access has been revoked"
```

### 6.3 Reference Implementation

We maintain a **live reference deployment** at `demo.gmail-mcp.dev`:
- Shows the full working system
- Developers can test MCP tools before deploying their own
- Connected to our Supabase/Google Cloud (for demo only)
- Resets daily, not for production use

---

## 7. API Design

### 7.1 REST API (for Dashboard & Integration)

#### Authentication
```
POST /api/v1/auth/tenant
X-API-Key: <api_key>
X-Tenant-ID: <tenant_id>
```

#### Connections
```
GET    /api/v1/users/{user_id}/connections
POST   /api/v1/users/{user_id}/connections/auth-url
DELETE /api/v1/users/{user_id}/connections/{connection_id}
```

#### OAuth Callback
```
GET /api/v1/oauth/callback?code=...&state=...
```

### 7.2 MCP Interface

Transport: HTTP (Streamable HTTP) for remote server

```python
@server.tool()
async def gmail_search(
    connection_id: str,
    query: str,
    max_results: int = 10,
    page_token: str | None = None
) -> dict:
    """Search emails using Gmail query syntax.
    
    Args:
        connection_id: The Gmail connection to use
        query: Gmail search query (e.g., "from:alice@example.com is:unread")
        max_results: Maximum number of results (1-100)
        page_token: Token for pagination
        
    Returns:
        List of matching messages with metadata
    """
    ...
```

---

## 8. Error Handling

### 8.1 Error Categories

| Category | Code Range | Example |
|----------|------------|---------|
| Authentication | 401xx | Invalid API key, expired token |
| Authorization | 403xx | Insufficient scopes, tenant mismatch |
| Validation | 400xx | Invalid parameters, missing fields |
| Not Found | 404xx | Connection not found, message not found |
| Rate Limit | 429xx | Gmail API quota exceeded |
| Server Error | 500xx | Internal errors, Gmail API errors |

### 8.2 Error Response Format

```json
{
  "error": {
    "code": "40101",
    "type": "authentication_error",
    "message": "API key is invalid or expired",
    "details": {
      "tenant_id": "abc123"
    },
    "docs_url": "https://docs.gmail-mcp.com/errors/40101"
  }
}
```

### 8.3 Automatic Recovery

| Scenario | Recovery Action |
|----------|-----------------|
| Access token expired | Auto-refresh using refresh token |
| Refresh token expired | Mark connection as invalid, notify developer |
| Rate limit hit | Exponential backoff with jitter |
| Transient Gmail error | Retry with backoff (3 attempts) |

---

## 9. Implementation Phases

### Phase 1: Project Foundation (Week 1)

- [ ] Repository setup (pyproject.toml, structure, CI)
- [ ] Config system implementation
  - [ ] YAML parsing with Pydantic validation
  - [ ] Environment variable overrides
  - [ ] Config file discovery (local → home)
- [ ] Storage backend interface (abstract base class)
- [ ] SQLite storage implementation
- [ ] Encryption utilities (Fernet wrapper)
- [ ] Basic test infrastructure (pytest, fixtures)

**Deliverable:** `pip install` works, config loading works, SQLite storage works

### Phase 2: OAuth & Token Management (Week 2)

- [ ] Google OAuth flow implementation
  - [ ] Authorization URL generation
  - [ ] PKCE support
  - [ ] Token exchange (code → tokens)
  - [ ] State management (CSRF protection)
- [ ] Token manager
  - [ ] Secure storage (encrypted)
  - [ ] Automatic refresh logic
  - [ ] Expiry tracking
- [ ] OAuth HTTP routes (callback handling)
- [ ] Tests for OAuth flow

**Deliverable:** Can complete OAuth flow and store tokens

### Phase 3: Gmail API Wrapper (Week 3)

- [ ] Gmail API client setup
- [ ] Message operations
  - [ ] Search with query syntax
  - [ ] Get message (full/metadata/minimal)
  - [ ] Get thread
  - [ ] List labels
- [ ] MIME parsing utilities
- [ ] Attachment handling
- [ ] Tests with mocked Gmail API

**Deliverable:** Can read emails via library

### Phase 4: Gmail Write Operations (Week 4)

- [ ] Send email (plain text, HTML)
- [ ] Attachments support
- [ ] Draft operations (create, update, send, delete)
- [ ] Reply/forward (threading)
- [ ] Label management
- [ ] Trash/archive operations
- [ ] Tests for write operations

**Deliverable:** Full Gmail functionality via library

### Phase 5: Supabase Backend (Week 5)

- [ ] Supabase storage implementation
- [ ] Migration scripts
- [ ] RLS policies
- [ ] Connection pooling
- [ ] Tests with Supabase (integration)

**Deliverable:** Production-ready storage backend

### Phase 6: MCP Server Layer (Week 6)

- [ ] FastMCP server setup
- [ ] MCP tools wrapping library functions
  - [ ] Auth tools
  - [ ] Read tools
  - [ ] Write tools
  - [ ] Management tools
- [ ] Stdio transport support
- [ ] HTTP transport support
- [ ] CLI (`gmail-mcp serve`)
- [ ] Tests for MCP tools

**Deliverable:** Full MCP server working

### Phase 7: Polish & Documentation (Week 7)

- [ ] Error handling improvements
- [ ] Logging system
- [ ] README with quick start
- [ ] Setup guides (Google, Supabase)
- [ ] API reference documentation
- [ ] MCP tools documentation
- [ ] Example scripts
- [ ] Troubleshooting guide

**Deliverable:** Developer-ready documentation

### Phase 8: Testing & Release (Week 8)

- [ ] End-to-end integration tests
- [ ] Real Gmail account testing
- [ ] Claude Desktop testing
- [ ] Docker setup
- [ ] GitHub Actions (test, publish)
- [ ] PyPI publication
- [ ] GitHub release
- [ ] Announcement

**Deliverable:** Public v1.0.0 release

---

## 10. Success Metrics

### 10.1 Open-Source Adoption

| Metric | Target (6 months) |
|--------|-------------------|
| GitHub stars | 500 |
| Forks | 100 |
| Contributors | 10 |
| GitHub issues resolved | 80% within 1 week |

### 10.2 Developer Usage (via anonymous telemetry, opt-in)

| Metric | Target |
|--------|--------|
| Active deployments | 100+ |
| End-user connections (aggregate) | 5,000+ |
| Tools called per week | 50,000+ |

### 10.3 Quality

| Metric | Target |
|--------|--------|
| Test coverage | > 80% |
| Documentation completeness | All tools documented |
| Setup success rate | > 90% (measured via GitHub issues) |
| Time to first working deployment | < 1 hour |

### 10.4 Community

| Metric | Target |
|--------|--------|
| Discord/community members | 200 |
| Blog posts / tutorials by others | 5+ |
| Integrations with other tools | 3+ |

---

## 11. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Complex setup deters adoption | Medium | High | Excellent docs, video tutorials, one-click deploy options |
| Google OAuth setup is confusing | High | High | Step-by-step guide with screenshots, common errors FAQ |
| Developers misconfigure security | Medium | High | Secure defaults, warnings for insecure configs |
| Gmail API changes break tools | Low | Medium | Version pinning, integration tests, changelog monitoring |
| Low community engagement | Medium | Medium | Active Discord, respond to issues quickly, feature requests |
| Supabase free tier limitations | Low | Low | Document limits, provide alternatives (self-hosted Postgres) |

---

## 12. Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Distribution model** | Hybrid (Library + MCP) | Serves both traditional devs and AI agent builders |
| **Package name** | `gmail-multi-user-mcp` | MCP-focused naming for vibe coding audience |
| **License** | MIT | Maximum adoption, no restrictions |
| **Primary storage** | Supabase | Production-ready, free tier, managed |
| **Dev storage** | SQLite | Zero setup, portable, great for testing |
| **MCP transports** | Both (stdio + HTTP) | stdio for Claude Desktop, HTTP for remote |
| **Config approach** | Layered (env → local → home) | Flexible for all deployment scenarios |
| **Email providers** | Gmail only (v1) | Consumer focus, simplicity |
| **Real-time updates** | Polling only (v1) | Simpler architecture, sufficient for most |
| **Google Workspace** | Out of scope (v1) | Different trust model, enterprise complexity |

## 13. Remaining Open Questions

1. **Telemetry**: Should we include optional anonymous usage stats? 
   - Recommendation: Skip for v1, add opt-in later if needed

2. **Sandbox mode**: Mock Gmail API for testing without real accounts?
   - Recommendation: Yes, useful for CI/CD and demos

3. **Rate limiting**: Built-in rate limiting for MCP server?
   - Recommendation: Optional config, off by default

4. **Reference deployment**: Should we host a demo instance?
   - Recommendation: Yes, helps developers evaluate before setup

---

## 14. Repository Structure

```
gmail-multi-user-mcp/
├── README.md                        # Quick start guide
├── LICENSE                          # MIT License
├── pyproject.toml                   # Python package config
├── gmail_config.yaml.example        # Config template (COPY THIS)
│
├── gmail_multi_user/                # Core library (the real value)
│   ├── __init__.py                  # Exports GmailClient, Config
│   ├── client.py                    # GmailClient - main public interface
│   ├── config.py                    # Config loading (env → file → home)
│   │
│   ├── oauth/                       # OAuth flow
│   │   ├── __init__.py
│   │   ├── flow.py                  # OAuth URL generation, token exchange
│   │   ├── pkce.py                  # PKCE implementation
│   │   └── routes.py                # HTTP routes for OAuth callbacks
│   │
│   ├── storage/                     # Token storage backends
│   │   ├── __init__.py
│   │   ├── base.py                  # Abstract storage interface
│   │   ├── sqlite.py                # SQLite backend
│   │   └── supabase.py              # Supabase backend
│   │
│   ├── gmail/                       # Gmail API wrapper
│   │   ├── __init__.py
│   │   ├── api.py                   # Gmail API client
│   │   ├── messages.py              # Message operations
│   │   ├── drafts.py                # Draft operations
│   │   ├── labels.py                # Label operations
│   │   └── parser.py                # MIME parsing utilities
│   │
│   ├── tokens/                      # Token management
│   │   ├── __init__.py
│   │   ├── manager.py               # Token refresh, encryption
│   │   └── encryption.py            # Fernet encryption wrapper
│   │
│   └── exceptions.py                # Custom exceptions
│
├── gmail_mcp_server/                # MCP server wrapper (thin layer)
│   ├── __init__.py
│   ├── __main__.py                  # Entry point for `gmail-mcp` CLI
│   ├── server.py                    # FastMCP server setup
│   ├── tools/                       # MCP tool definitions
│   │   ├── __init__.py
│   │   ├── auth.py                  # gmail_get_auth_url, gmail_disconnect, etc.
│   │   ├── read.py                  # gmail_search, gmail_get_message, etc.
│   │   ├── write.py                 # gmail_send, gmail_create_draft, etc.
│   │   └── manage.py                # gmail_modify_labels, gmail_trash, etc.
│   └── cli.py                       # CLI commands (serve, health, etc.)
│
├── migrations/                      # Database migrations
│   ├── sqlite/
│   │   └── 001_initial.sql
│   └── supabase/
│       └── 001_initial.sql
│
├── templates/                       # OAuth flow HTML templates
│   ├── oauth_success.html
│   └── oauth_error.html
│
├── tests/
│   ├── conftest.py                  # Fixtures (uses SQLite :memory:)
│   ├── test_config.py               # Config loading tests
│   ├── test_oauth.py                # OAuth flow tests
│   ├── test_storage.py              # Storage backend tests
│   ├── test_gmail_api.py            # Gmail API wrapper tests
│   ├── test_mcp_tools.py            # MCP tool tests
│   └── test_integration.py          # End-to-end tests
│
├── docs/
│   ├── QUICKSTART.md                # 5-minute getting started
│   ├── GOOGLE_SETUP.md              # Google Cloud setup with screenshots
│   ├── SUPABASE_SETUP.md            # Supabase setup guide
│   ├── CONFIGURATION.md             # Full config reference
│   ├── API_REFERENCE.md             # Library API docs
│   ├── MCP_TOOLS.md                 # MCP tool reference
│   ├── DEPLOYMENT.md                # Production deployment guide
│   └── TROUBLESHOOTING.md           # Common issues and solutions
│
├── examples/
│   ├── basic_usage.py               # Simple library usage
│   ├── multi_account.py             # User with multiple Gmail accounts
│   ├── batch_operations.py          # Efficient bulk operations
│   └── claude_desktop_config.json   # Example Claude Desktop config
│
├── docker-compose.yml               # Local development with Docker
├── Dockerfile                       # Container build
└── .github/
    └── workflows/
        ├── test.yml                 # Run tests on PR
        └── publish.yml              # Publish to PyPI on release
```

---

## 15. MCP Architecture: Tools, Resources, and Prompts

This section defines the complete MCP interface that Claude Code (or any MCP host) will use to interact with gmail-multi-user-mcp.

### 15.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        gmail-multi-user-mcp                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           TOOLS (18)                                 │   │
│  │  (Actions the AI can perform)                                       │   │
│  │                                                                      │   │
│  │  Setup & Config    OAuth & Users       Gmail Operations             │   │
│  │  ─────────────     ─────────────       ────────────────             │   │
│  │  • check_setup     • get_auth_url      • search                     │   │
│  │  • init_config     • handle_callback   • get_message                │   │
│  │  • test_connection • list_connections  • get_thread                 │   │
│  │  • run_migrations  • disconnect        • send                       │   │
│  │                    • check_connection  • create_draft               │   │
│  │                                        • send_draft                 │   │
│  │                                        • modify_labels              │   │
│  │                                        • archive                    │   │
│  │                                        • trash                      │   │
│  │                                        • get_attachment             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         RESOURCES (8)                                │   │
│  │  (Data the AI can read)                                             │   │
│  │                                                                      │   │
│  │  • config://status          Current configuration status            │   │
│  │  • config://schema          Config file schema/template             │   │
│  │  • users://list             All users with connections              │   │
│  │  • users://{id}/connections Gmail accounts for a user               │   │
│  │  • gmail://{conn}/labels    Available labels for a connection       │   │
│  │  • gmail://{conn}/profile   Gmail profile info (email, quota)       │   │
│  │  • docs://setup             Setup guide                             │   │
│  │  • docs://google-oauth      Google Cloud setup guide                │   │
│  │  • docs://troubleshooting   Common issues and fixes                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         PROMPTS (5)                                  │   │
│  │  (Pre-built workflows the AI can execute)                           │   │
│  │                                                                      │   │
│  │  • setup-gmail          Complete setup wizard                       │   │
│  │  • connect-test-account Connect developer's Gmail for testing       │   │
│  │  • diagnose-connection  Debug a failing connection                  │   │
│  │  • generate-oauth-ui    Create OAuth UI components for app          │   │
│  │  • build-email-agent    Scaffold an email-capable agent             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.2 Tools Specification

#### 15.2.1 Setup & Configuration Tools

**gmail_check_setup**
```yaml
name: gmail_check_setup
description: |
  Check if gmail-multi-user-mcp is properly configured.
  Returns status of: config file, database connection, Google OAuth credentials, encryption key.
  Use this first when a developer asks about Gmail integration.
inputs: {}
outputs:
  config_found: boolean
  config_path: string | null
  database_connected: boolean
  database_type: "sqlite" | "supabase"
  google_oauth_configured: boolean
  encryption_key_set: boolean
  issues: string[]           # List of problems to fix
  ready: boolean             # True if everything is configured
```

**gmail_init_config**
```yaml
name: gmail_init_config
description: |
  Create a gmail_config.yaml file with the provided settings.
  Use this to help developers set up their configuration.
inputs:
  database_type: "sqlite" | "supabase"
  sqlite_path: string | null           # Required if sqlite
  supabase_url: string | null          # Required if supabase
  supabase_key: string | null          # Required if supabase
  google_client_id: string | null      # Can be added later
  google_client_secret: string | null  # Can be added later
  redirect_uri: string                 # Default: http://localhost:8000/oauth/callback
  generate_encryption_key: boolean     # Default: true
outputs:
  config_path: string
  encryption_key: string | null        # Only returned if generated, SAVE THIS!
  next_steps: string[]
```

**gmail_test_connection**
```yaml
name: gmail_test_connection
description: |
  Test the database and Google OAuth configuration.
  Attempts to connect to the database and validate Google credentials.
inputs:
  verbose: boolean                     # Include detailed diagnostics
outputs:
  database_ok: boolean
  database_error: string | null
  google_oauth_ok: boolean
  google_oauth_error: string | null
  test_auth_url: string | null         # A working OAuth URL if configured
```

**gmail_run_migrations**
```yaml
name: gmail_run_migrations
description: |
  Run database migrations to set up the required tables.
  Safe to run multiple times (idempotent).
inputs: {}
outputs:
  migrations_run: string[]
  already_applied: string[]
  current_version: string
```

#### 15.2.2 OAuth & User Management Tools

**gmail_get_auth_url**
```yaml
name: gmail_get_auth_url
description: |
  Generate an OAuth URL for a user to connect their Gmail account.
  The user should visit this URL to authorize access.
inputs:
  user_id: string                      # Developer's identifier for the user
  scopes: string[]                     # Default: ["gmail.readonly", "gmail.send"]
  redirect_uri: string | null          # Override default redirect URI
outputs:
  auth_url: string                     # URL to redirect user to
  state: string                        # State parameter (for CSRF protection)
  expires_in: integer                  # Seconds until this URL expires
```

**gmail_handle_oauth_callback**
```yaml
name: gmail_handle_oauth_callback
description: |
  Process an OAuth callback after user authorizes.
  Exchange the authorization code for tokens and store them.
  Usually called automatically by the OAuth callback endpoint,
  but can be called manually for testing.
inputs:
  code: string                         # Authorization code from Google
  state: string                        # State parameter for verification
outputs:
  success: boolean
  connection_id: string | null
  user_id: string | null
  gmail_address: string | null
  error: string | null
```

**gmail_list_connections**
```yaml
name: gmail_list_connections
description: |
  List all Gmail connections for a user, or all connections if no user specified.
inputs:
  user_id: string | null               # Filter by user, or null for all
  include_inactive: boolean            # Include disconnected/expired connections
outputs:
  connections:
    - id: string
      user_id: string
      gmail_address: string
      scopes: string[]
      is_active: boolean
      created_at: string
      last_used_at: string | null
```

**gmail_check_connection**
```yaml
name: gmail_check_connection
description: |
  Check if a specific connection is still valid and working.
  Attempts to refresh the token if needed.
inputs:
  connection_id: string
outputs:
  valid: boolean
  gmail_address: string
  scopes: string[]
  token_expires_in: integer | null     # Seconds until token expires
  error: string | null                 # If invalid, why
  needs_reauth: boolean                # If true, user must re-authorize
```

**gmail_disconnect**
```yaml
name: gmail_disconnect
description: |
  Disconnect a Gmail account and delete stored tokens.
inputs:
  connection_id: string
  revoke_google_access: boolean        # Also revoke access in Google's systems
outputs:
  success: boolean
  gmail_address: string                # Which account was disconnected
```

#### 15.2.3 Gmail Operation Tools

**gmail_search**
```yaml
name: gmail_search
description: |
  Search for emails matching a query.
  Uses Gmail's search syntax (same as the Gmail search box).
inputs:
  connection_id: string                # Which Gmail account to search
  query: string                        # Gmail search query
  max_results: integer                 # Default: 10, max: 100
  include_body: boolean                # Include message body in results (slower)
outputs:
  messages:
    - id: string
      thread_id: string
      subject: string
      from: { name: string, email: string }
      to: { name: string, email: string }[]
      date: string
      snippet: string                  # Preview text
      labels: string[]
      has_attachments: boolean
      body_plain: string | null        # Only if include_body: true
      body_html: string | null         # Only if include_body: true
  total_estimate: integer              # Estimated total matching messages

common_queries:
  - "is:unread"                        # Unread messages
  - "from:example@gmail.com"           # From specific sender
  - "to:me"                            # Sent directly to user
  - "subject:invoice"                  # Subject contains word
  - "has:attachment"                   # Has attachments
  - "after:2024/01/01"                 # After date
  - "newer_than:7d"                    # Within last 7 days
  - "label:important"                  # Has label
```

**gmail_get_message**
```yaml
name: gmail_get_message
description: |
  Get a single email message with full content.
inputs:
  connection_id: string
  message_id: string
  format: "full" | "metadata" | "minimal"  # Default: full
outputs:
  id: string
  thread_id: string
  subject: string
  from: { name: string, email: string }
  to: { name: string, email: string }[]
  cc: { name: string, email: string }[]
  bcc: { name: string, email: string }[]
  date: string
  body_plain: string
  body_html: string | null
  labels: string[]
  attachments:
    - id: string
      filename: string
      mime_type: string
      size: integer
  headers: { name: string, value: string }[]
```

**gmail_get_thread**
```yaml
name: gmail_get_thread
description: |
  Get all messages in an email thread.
inputs:
  connection_id: string
  thread_id: string
outputs:
  id: string
  subject: string                      # Subject of first message
  message_count: integer
  messages: []                         # Array of message objects (same as gmail_get_message)
```

**gmail_send**
```yaml
name: gmail_send
description: |
  Send a new email or reply to an existing message.
inputs:
  connection_id: string
  to: string[]                         # Recipient email addresses
  subject: string
  body: string                         # Plain text body
  body_html: string | null             # Optional HTML body
  cc: string[] | null
  bcc: string[] | null
  reply_to_message_id: string | null   # If replying, the message to reply to
  attachments:                         # Optional attachments
    - filename: string
      content_base64: string           # Base64 encoded content
      mime_type: string
outputs:
  success: boolean
  message_id: string                   # ID of sent message
  thread_id: string                    # Thread ID (same as replied-to if reply)
```

**gmail_create_draft**
```yaml
name: gmail_create_draft
description: |
  Create a draft email (saved but not sent).
inputs:
  connection_id: string
  to: string[]
  subject: string
  body: string
  body_html: string | null
  cc: string[] | null
  bcc: string[] | null
  reply_to_message_id: string | null
outputs:
  draft_id: string
  message_id: string
```

**gmail_send_draft**
```yaml
name: gmail_send_draft
description: |
  Send a previously created draft.
inputs:
  connection_id: string
  draft_id: string
outputs:
  success: boolean
  message_id: string
  thread_id: string
```

**gmail_modify_labels**
```yaml
name: gmail_modify_labels
description: |
  Add or remove labels from a message.
inputs:
  connection_id: string
  message_id: string
  add_labels: string[]                 # Labels to add
  remove_labels: string[]              # Labels to remove
outputs:
  success: boolean
  current_labels: string[]

system_labels:
  - INBOX, SENT, DRAFT, SPAM, TRASH
  - UNREAD, STARRED, IMPORTANT
  - CATEGORY_PERSONAL, CATEGORY_SOCIAL
  - CATEGORY_PROMOTIONS, CATEGORY_UPDATES, CATEGORY_FORUMS
```

**gmail_archive**
```yaml
name: gmail_archive
description: |
  Archive a message (remove from inbox but keep in All Mail).
inputs:
  connection_id: string
  message_id: string
outputs:
  success: boolean
```

**gmail_trash**
```yaml
name: gmail_trash
description: |
  Move a message to trash.
inputs:
  connection_id: string
  message_id: string
outputs:
  success: boolean
```

**gmail_get_attachment**
```yaml
name: gmail_get_attachment
description: |
  Download an attachment from a message.
inputs:
  connection_id: string
  message_id: string
  attachment_id: string
outputs:
  filename: string
  mime_type: string
  size: integer
  content_base64: string               # Base64 encoded content
```

### 15.3 Resources Specification

**config://status**
```yaml
uri: config://status
description: Current configuration status and health.
mime_type: application/json
content:
  configured: boolean
  config_path: string | null
  database:
    type: "sqlite" | "supabase"
    connected: boolean
    path_or_url: string
  google_oauth:
    configured: boolean
    client_id_set: boolean
    client_secret_set: boolean
    redirect_uri: string
  encryption:
    key_set: boolean
  server:
    running: boolean
    transport: "stdio" | "http"
    port: integer | null
```

**config://schema**
```yaml
uri: config://schema
description: The full configuration schema with documentation.
mime_type: text/yaml
```

**users://list**
```yaml
uri: users://list
description: All users who have connected Gmail accounts.
mime_type: application/json
content:
  users:
    - id: string
      external_user_id: string
      email: string | null
      connection_count: integer
      created_at: string
```

**users://{user_id}/connections**
```yaml
uri_template: users://{user_id}/connections
description: All Gmail connections for a specific user.
mime_type: application/json
```

**gmail://{connection_id}/labels**
```yaml
uri_template: gmail://{connection_id}/labels
description: All labels available for a Gmail connection.
mime_type: application/json
```

**gmail://{connection_id}/profile**
```yaml
uri_template: gmail://{connection_id}/profile
description: Profile information and quota for a Gmail connection.
mime_type: application/json
content:
  email_address: string
  messages_total: integer
  threads_total: integer
  history_id: string
```

**docs://setup**
```yaml
uri: docs://setup
description: Quick setup guide for gmail-multi-user-mcp.
mime_type: text/markdown
```

**docs://google-oauth**
```yaml
uri: docs://google-oauth
description: Step-by-step Google Cloud OAuth setup guide.
mime_type: text/markdown
```

**docs://troubleshooting**
```yaml
uri: docs://troubleshooting
description: Common issues and how to fix them.
mime_type: text/markdown
```

### 15.4 Prompts Specification

**setup-gmail**
```yaml
name: setup-gmail
description: Complete setup wizard for gmail-multi-user-mcp.
arguments: []
workflow:
  1. Check current setup status (gmail_check_setup)
  2. Create config if missing (gmail_init_config)
  3. Guide through Google OAuth setup (docs://google-oauth)
  4. Run migrations (gmail_run_migrations)
  5. Test configuration (gmail_test_connection)
  6. Offer to connect test account
```

**connect-test-account**
```yaml
name: connect-test-account
description: Connect the developer's own Gmail account for testing.
arguments: []
workflow:
  1. Verify setup is complete
  2. Generate OAuth URL (user_id: "developer_test")
  3. Guide user through authorization
  4. Verify connection works
  5. Test with simple search
```

**diagnose-connection**
```yaml
name: diagnose-connection
description: Debug a failing Gmail connection.
arguments:
  - name: connection_id
    required: false
    description: The connection to diagnose
workflow:
  1. List connections if not specified
  2. Check connection status
  3. Identify issue (expired, revoked, etc.)
  4. Provide solution from docs://troubleshooting
  5. Test fix
```

**generate-oauth-ui**
```yaml
name: generate-oauth-ui
description: Generate OAuth UI components for the developer's app.
arguments:
  - name: framework
    required: true
    options: [react, vue, nextjs, html]
  - name: style
    required: false
    options: [tailwind, css, shadcn]
workflow:
  1. Generate Connect Gmail button component
  2. Generate OAuth callback handler
  3. Generate connection status component
  4. Generate backend API routes
  5. Add TypeScript types if applicable
```

**build-email-agent**
```yaml
name: build-email-agent
description: Scaffold an email-capable AI agent.
arguments:
  - name: framework
    required: true
    options: [langchain, crewai, vercel-ai, custom]
  - name: use_case
    required: true
    description: What the agent should do with emails
workflow:
  1. Verify Gmail setup
  2. Recommend appropriate Gmail tools for use case
  3. Generate agent code with tool definitions
  4. Create test scenarios
  5. Document usage
```

### 15.5 Developer Experience Flow

**Day 1: Initial Setup**
```
Developer: "I want to add Gmail to my app"

Claude: [reads config://status]
        [calls gmail_check_setup]
        "Let's set up Gmail integration. SQLite or Supabase?"

Developer: "SQLite"

Claude: [calls gmail_init_config]
        "Config created! Save this encryption key: xxx
         Now let's set up Google OAuth..."
        [reads docs://google-oauth]
        [walks through setup]
```

**Day 1: First Connection**
```
Developer: "I added my Google credentials"

Claude: [calls gmail_test_connection]
        "Working! Let's connect your Gmail for testing."
        [calls gmail_get_auth_url]
        "Click this link: https://..."

Developer: "Done!"

Claude: [calls gmail_list_connections]
        [calls gmail_search]
        "Connected! Found 5 unread emails..."
```

**Day 2: Building the App**
```
Developer: "Help me add Gmail to my Next.js app"

Claude: [uses prompt: generate-oauth-ui]
        "Here's the complete implementation:
         - ConnectGmail.tsx component
         - /api/gmail/auth route
         - /api/gmail/callback route
         ..."
```

**Day 3: Production Agent**
```
Developer: "Build me an email assistant agent"

Claude: [uses prompt: build-email-agent]
        "Here's a LangChain agent that can:
         - Search and summarize emails
         - Draft responses
         - Organize with labels
         ..."
```

---

## 16. Scenario Walkthroughs

### Scenario 1: Developer Quick Start (Library Mode)

**Actor:** Developer building an email-enabled app with Python

```bash
# 1. Install
pip install gmail-multi-user-mcp

# 2. Create config (SQLite for local dev)
cat > gmail_config.yaml << EOF
database:
  type: sqlite
  sqlite_path: ./tokens.db
google:
  client_id: $GOOGLE_CLIENT_ID
  client_secret: $GOOGLE_CLIENT_SECRET
  redirect_uri: http://localhost:8000/oauth/callback
encryption:
  key: $(python -c "import secrets; print(secrets.token_hex(32))")
EOF

# 3. Use in code
python << EOF
from gmail_multi_user import GmailClient

client = GmailClient()
auth_url = client.get_auth_url(user_id="test_user")
print(f"Visit: {auth_url}")
EOF
```

**Time to first API call: ~10 minutes** (excluding Google Cloud setup)

### Scenario 2: Claude Code User (MCP Mode)

**Actor:** Developer using Claude Code for vibe coding

```bash
# 1. Install
pip install gmail-multi-user-mcp

# 2. Create config
cp gmail_config.yaml.example gmail_config.yaml
# Edit with credentials...

# 3. Add to Claude Code settings
{
  "mcpServers": {
    "gmail": {
      "command": "gmail-mcp",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}

# 4. Use naturally in Claude Code
```

**Claude Code conversation:**
```
You: "Connect my Gmail account"
Claude: [Calls gmail_get_auth_url, provides link]

You: "Find all unread emails from my boss"
Claude: [Calls gmail_search with query "is:unread from:boss@company.com"]

You: "Draft a reply to the latest one saying I'll handle it tomorrow"
Claude: [Calls gmail_get_message, then gmail_create_draft]
```

### Scenario 3: End-User Connects Gmail

**Actor:** End-user of developer's consumer app

1. User clicks "Connect Gmail" in the app
2. App backend calls `client.get_auth_url(user_id="user_456")`
3. User redirected to Google consent screen (shows developer's app name)
4. User approves requested permissions
5. Google redirects to callback URL with auth code
6. Library exchanges code for tokens, encrypts, stores in database
7. User returned to app with success message
8. User can now use Gmail features

**Time to connect: ~30 seconds**

### Scenario 4: Background Token Refresh

**Actor:** Library/server background process

1. Token for user_123 expires in 5 minutes
2. Library detects approaching expiry on next API call
3. Automatically calls Google refresh endpoint
4. New access token received
5. Token encrypted and stored, expiry updated
6. Original API call proceeds with new token
7. User experiences no interruption

**User impact: None (transparent)**

### Scenario 5: Production Deployment

**Actor:** Developer deploying to production

```yaml
# docker-compose.yml
services:
  gmail-mcp:
    image: python:3.11-slim
    command: gmail-mcp serve --host 0.0.0.0
    environment:
      GMAIL_MCP_DATABASE_TYPE: supabase
      GMAIL_MCP_SUPABASE_URL: ${SUPABASE_URL}
      GMAIL_MCP_SUPABASE_KEY: ${SUPABASE_KEY}
      GMAIL_MCP_GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GMAIL_MCP_GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
      GMAIL_MCP_GOOGLE_REDIRECT_URI: https://myapp.com/oauth/callback
      GMAIL_MCP_ENCRYPTION_KEY: ${ENCRYPTION_KEY}
    ports:
      - "8000:8000"
```

**No config files in production** — all secrets from environment/secrets manager.

### Scenario 6: CI/CD Testing

**Actor:** GitHub Actions workflow

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      GMAIL_MCP_DATABASE_TYPE: sqlite
      GMAIL_MCP_SQLITE_PATH: ":memory:"
      GMAIL_MCP_GOOGLE_CLIENT_ID: test-client
      GMAIL_MCP_GOOGLE_CLIENT_SECRET: test-secret
      GMAIL_MCP_ENCRYPTION_KEY: test-key-for-ci
    steps:
      - uses: actions/checkout@v4
      - run: pip install gmail-multi-user-mcp
      - run: pytest tests/
```

**Tests use in-memory SQLite** — no external dependencies.

### Scenario 7: User with Multiple Gmail Accounts

**Actor:** End-user who needs both personal and work Gmail

1. User connects personal Gmail (user_123 → gmail_connection_1)
2. User connects work Gmail (user_123 → gmail_connection_2)
3. App calls `client.list_connections(user_id="user_123")`
4. Returns both connections with Gmail addresses
5. User selects which account to use for each action
6. App passes specific `connection_id` to operations

```python
# List all connected accounts for a user
connections = client.list_connections(user_id="user_123")
# [
#   {"id": "conn_1", "gmail_address": "personal@gmail.com"},
#   {"id": "conn_2", "gmail_address": "work@company.com"}
# ]

# Use specific account
messages = client.search(connection_id="conn_2", query="is:unread")
```

### Scenario 8: TypeScript Agent Using Remote MCP (Non-Python Production)

**Actor:** Developer building an AI email assistant in TypeScript (Next.js + Vercel AI SDK)

**The Problem:** Can't import Python library in TypeScript

**Solution:** Run gmail-multi-user-mcp as a sidecar service

**Step 1: Docker Compose setup**
```yaml
# docker-compose.yml
services:
  web:
    build: ./nextjs-app
    ports:
      - "3000:3000"
    environment:
      GMAIL_MCP_URL: http://gmail-mcp:8000
      GMAIL_MCP_AUTH_TOKEN: ${INTERNAL_SERVICE_TOKEN}
    depends_on:
      - gmail-mcp

  gmail-mcp:
    image: ghcr.io/yourorg/gmail-multi-user-mcp:latest
    command: gmail-mcp serve --transport http --host 0.0.0.0
    environment:
      GMAIL_MCP_DATABASE_TYPE: supabase
      GMAIL_MCP_SUPABASE_URL: ${SUPABASE_URL}
      GMAIL_MCP_SUPABASE_KEY: ${SUPABASE_SERVICE_KEY}
      GMAIL_MCP_GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GMAIL_MCP_GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
      GMAIL_MCP_ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      GMAIL_MCP_SERVER_AUTH_TOKEN: ${INTERNAL_SERVICE_TOKEN}
```

**Step 2: TypeScript MCP client wrapper**
```typescript
// lib/gmail-mcp-client.ts
class GmailMCPClient {
  private baseUrl = process.env.GMAIL_MCP_URL!;
  private authToken = process.env.GMAIL_MCP_AUTH_TOKEN!;

  async callTool(tool: string, params: Record<string, any>) {
    const response = await fetch(`${this.baseUrl}/mcp/tools/${tool}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.authToken}`,
      },
      body: JSON.stringify(params),
    });
    return response.json();
  }

  async search(userId: string, query: string) {
    return this.callTool('gmail_search', { user_id: userId, query });
  }

  async send(connectionId: string, to: string[], subject: string, body: string) {
    return this.callTool('gmail_send', { connection_id: connectionId, to, subject, body });
  }
}

export const gmailClient = new GmailMCPClient();
```

**Step 3: Use in Vercel AI SDK agent**
```typescript
// app/api/chat/route.ts
import { streamText, tool } from 'ai';
import { gmailClient } from '@/lib/gmail-mcp-client';

export async function POST(req: Request) {
  const { messages, userId } = await req.json();

  return streamText({
    model: openai('gpt-4-turbo'),
    messages,
    tools: {
      searchEmails: tool({
        description: 'Search emails in Gmail',
        parameters: z.object({ query: z.string() }),
        execute: async ({ query }) => {
          return gmailClient.search(userId, query);
        },
      }),
    },
  });
}
```

**Key Points:**
- MCP server runs as internal sidecar (not exposed to internet)
- TypeScript app calls it over HTTP on internal network
- Same Supabase instance shared between Next.js app and MCP server
- Authentication via internal service token (not user-facing)
```

---

## 17. Future Roadmap

This section outlines features that would warrant evolving from a local MCP/library to a remote MCP server or hosted service.

### 17.1 Current Scope: Tier 1 (Local MCP / Library)

**What's included in v1:**

| Category | Features |
|----------|----------|
| **Setup** | Config file, database migrations, encryption |
| **OAuth** | Multi-user OAuth flow, token storage, automatic refresh |
| **Gmail Operations** | Search, read, send, draft, labels, attachments, archive, trash |
| **Storage** | SQLite (local), Supabase (production) |
| **Distribution** | Python library + local MCP server (stdio/HTTP) |

**Target users:** Individual developers, prototyping, simple production apps

**Scale:** 10 - 10,000 end-users per deployment

### 17.2 Future Scope: Tier 2 (Remote MCP Server)

Features that would require a persistent, always-on remote MCP server:

#### 17.2.1 Real-Time Email Push Notifications

**The Feature:** Instant notifications when emails arrive (not polling)

**Why it needs remote MCP:**
- Gmail push requires a publicly accessible HTTPS endpoint
- Needs persistent server to receive Google Pub/Sub notifications
- Must dispatch events to connected agents/apps

**New Tools:**
```yaml
- gmail_subscribe_push      # Subscribe to real-time notifications
- gmail_unsubscribe_push    # Stop notifications
- gmail_list_subscriptions  # View active subscriptions
```

**Value:** Build real-time email assistants, instant response triggers

---

#### 17.2.2 Scheduled Email Operations

**The Feature:** Schedule emails for later, recurring digests, automated cleanup

**Why it needs remote MCP:**
- Agent may not be running at scheduled time
- Requires persistent scheduler that survives restarts
- Must track jobs across connections

**New Tools:**
```yaml
- gmail_schedule_send       # Send email at specific time
- gmail_schedule_digest     # Recurring email summary (cron)
- gmail_list_scheduled      # View pending operations
- gmail_cancel_scheduled    # Cancel pending operation
```

**Value:** Time-zone optimized sending, daily summaries, auto-archive old emails

---

#### 17.2.3 Cross-Connection Operations

**The Feature:** Search/aggregate across multiple Gmail accounts for one user

**Why it needs remote MCP:**
- Library would iterate sequentially; server can parallelize
- Server can maintain unified indexes
- Better UX for "search all my inboxes"

**New Tools:**
```yaml
- gmail_search_all          # Search across ALL user's accounts
- gmail_unified_inbox       # Merged view of recent emails
- gmail_cross_account_stats # Aggregate statistics
```

**Value:** "Find all invoices across personal and work email"

---

#### 17.2.4 Email Queue & Rate Limit Management

**The Feature:** Queue emails when rate limits hit, automatic retry with backoff

**Why it needs remote MCP:**
- Multiple agents don't share state
- Need centralized rate limit tracking
- Queue must persist across restarts

**New Tools:**
```yaml
- gmail_queue_send          # Queue email for sending
- gmail_get_quota_status    # Check usage and limits
- gmail_bulk_send           # Send many with automatic queuing
```

**Value:** Send 1000 emails without hitting limits, priority queues

---

#### 17.2.5 Shared Templates

**The Feature:** Centralized email template management across agents

**Why it needs remote MCP:**
- Templates shared across deployments
- Version control and analytics
- Consistent formatting

**New Tools:**
```yaml
- gmail_create_template     # Create reusable template
- gmail_list_templates      # List available templates
- gmail_send_from_template  # Send using template
```

**Value:** Consistent emails, track template performance

---

### 17.3 Future Scope: Tier 3 (Hosted Service)

Features that would require a fully managed hosted service:

| Feature | Description |
|---------|-------------|
| **Email Analytics** | Response time tracking, volume trends, VIP identification |
| **AI-Powered Features** | Smart categorization, auto-responses, priority inbox |
| **Multi-Tenant Management** | Dashboard for managing multiple developer accounts |
| **Enterprise SSO** | SAML, OIDC integration for enterprise customers |
| **Audit Logging** | Compliance-ready logging of all operations |
| **SLA & Support** | Guaranteed uptime, dedicated support |

**Target:** Businesses, enterprise customers, high-compliance environments

---

### 17.4 Upgrade Path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVOLUTION PATH                                    │
│                                                                             │
│   TIER 1 (Current)              TIER 2                    TIER 3           │
│   Local MCP / Library    →    Remote MCP Server    →    Hosted Service     │
│                                                                             │
│   ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐   │
│   │ • Basic CRUD    │      │ • Everything in │      │ • Everything in │   │
│   │ • Multi-user    │      │   Tier 1        │      │   Tier 2        │   │
│   │ • OAuth mgmt    │      │ • Push notifs   │      │ • Analytics     │   │
│   │ • Token refresh │      │ • Scheduling    │      │ • AI features   │   │
│   │ • SQLite/Supa   │      │ • Cross-account │      │ • Multi-tenant  │   │
│   │                 │      │ • Queue mgmt    │      │ • Enterprise    │   │
│   │                 │      │ • Templates     │      │ • SLA/Support   │   │
│   └─────────────────┘      └─────────────────┘      └─────────────────┘   │
│                                                                             │
│   Free, self-hosted         Free, self-hosted        Paid, managed         │
│   10-10K users              10K-100K users           Unlimited             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.5 Decision Criteria: When to Upgrade

| Signal | Consider |
|--------|----------|
| "I need instant email notifications" | Tier 2 (push notifications) |
| "I'm hitting rate limits with bulk sends" | Tier 2 (queue management) |
| "Users have multiple Gmail accounts" | Tier 2 (cross-account) |
| "I need scheduled sends across timezones" | Tier 2 (scheduling) |
| "I need email analytics and insights" | Tier 3 (analytics) |
| "I need enterprise compliance/audit" | Tier 3 (hosted) |
| "I don't want to manage infrastructure" | Tier 3 (hosted) |

---

## 18. Appendix

### 18.1 Gmail Query Syntax Reference

```
from:alice@example.com         # From specific sender
to:bob@example.com             # To specific recipient
subject:meeting                # Subject contains word
is:unread                      # Unread messages
is:starred                     # Starred messages
has:attachment                 # Has attachments
filename:pdf                   # Attachment type
after:2024/01/01               # After date
before:2024/12/31              # Before date
newer_than:7d                  # Within last 7 days
label:important                # Has label
-label:spam                    # Exclude label
{from:a OR from:b}             # OR queries
```

### 18.2 Supabase Setup

**Migration Script:**

```sql
-- migrations/supabase/001_initial.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gmail connections
CREATE TABLE gmail_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    gmail_address VARCHAR(255) NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    scopes TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, gmail_address)
);

-- OAuth states (temporary)
CREATE TABLE oauth_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scopes TEXT[] NOT NULL,
    redirect_uri VARCHAR(500) NOT NULL,
    code_verifier VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_gmail_connections_user_id ON gmail_connections(user_id);
CREATE INDEX idx_gmail_connections_token_expires ON gmail_connections(token_expires_at);
CREATE INDEX idx_oauth_states_expires_at ON oauth_states(expires_at);
CREATE INDEX idx_oauth_states_state ON oauth_states(state);

-- Enable RLS (recommended even for service-role access)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE gmail_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_states ENABLE ROW LEVEL SECURITY;

-- Policies for service role (full access)
-- Note: Service role bypasses RLS, but these are here for documentation
CREATE POLICY "Service role full access on users" ON users FOR ALL USING (true);
CREATE POLICY "Service role full access on gmail_connections" ON gmail_connections FOR ALL USING (true);
CREATE POLICY "Service role full access on oauth_states" ON oauth_states FOR ALL USING (true);

-- Function to clean up expired OAuth states (run periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_states()
RETURNS void AS $$
BEGIN
    DELETE FROM oauth_states WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER gmail_connections_updated_at
    BEFORE UPDATE ON gmail_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

**SQLite Equivalent:**

```sql
-- migrations/sqlite/001_initial.sql

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    external_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE gmail_connections (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    gmail_address TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TEXT NOT NULL,
    scopes TEXT NOT NULL,  -- JSON array stored as text
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    
    UNIQUE(user_id, gmail_address)
);

CREATE TABLE oauth_states (
    id TEXT PRIMARY KEY,
    state TEXT UNIQUE NOT NULL,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    scopes TEXT NOT NULL,  -- JSON array stored as text
    redirect_uri TEXT NOT NULL,
    code_verifier TEXT,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_gmail_connections_user_id ON gmail_connections(user_id);
CREATE INDEX idx_oauth_states_state ON oauth_states(state);
```

### 18.3 Google OAuth Configuration

```python
# Required OAuth parameters for refresh token
oauth_params = {
    "access_type": "offline",      # Required for refresh token
    "prompt": "consent",           # Force consent to get refresh token
    "scope": "https://mail.google.com/",
    "include_granted_scopes": "true"
}
```

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-12 | Claude | Initial draft (hosted SaaS model) |
| 2.0 | 2026-01-12 | Claude | Pivot to open-source, hybrid library/MCP model; added config system, SQLite support |
| 2.1 | 2026-01-12 | Claude | Added deployment modes section (1.6) clarifying local MCP vs library import vs remote MCP; added TypeScript agent scenario |
| 2.2 | 2026-01-12 | Claude | Added comprehensive MCP Architecture section (15) with 18 tools, 8 resources, and 5 prompts specifications |
| 2.3 | 2026-01-12 | Claude | Added multi-user clarity section (1.7) with user_id vs connection_id pattern; added Future Roadmap (17) with Tier 2/3 features |
