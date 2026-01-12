# Production Agent Setup

This guide is for developers building AI agents or applications where **your users** will connect their own Gmail accounts.

**Time needed:** 30-45 minutes  
**Difficulty:** Intermediate  
**What you'll need:**
- Server or cloud hosting
- Database (Supabase recommended, or SQLite for simple cases)
- Google Cloud project with OAuth credentials

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│   │   User A     │     │   User B     │     │   User C     │   │
│   │   Browser    │     │   Browser    │     │   Browser    │   │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘   │
│          │                    │                    │            │
│          ▼                    ▼                    ▼            │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                     Gmail MCP Server                     │  │
│   │  - Handles OAuth for each user                          │  │
│   │  - Stores encrypted tokens per user                     │  │
│   │  - Routes Gmail requests to correct account             │  │
│   └─────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Database (Supabase/SQLite)                  │  │
│   │  - Users table                                          │  │
│   │  - Connections table (encrypted tokens)                 │  │
│   │  - OAuth states table                                   │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Step 1: Google Cloud Setup

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "My Email Agent")
3. Note your **Project ID**

### 1.2 Enable Gmail API

1. Go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click **Enable**

### 1.3 Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** (for apps others will use)
3. Fill in:
   - **App name**: Your app's name
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/userinfo.email`
5. Add test users (your email) while in development

### 1.4 Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose **Web application**
4. Add authorized redirect URIs:
   - `https://your-domain.com/oauth/callback`
   - `http://localhost:8080/oauth/callback` (for testing)
5. Download the credentials JSON

You now have:
- **Client ID**: `123456789-xxxxx.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-xxxxxxx`

## Step 2: Database Setup

### Option A: Supabase (Recommended for Production)

1. Create account at [supabase.com](https://supabase.com)
2. Create a new project
3. Run the migration:

```sql
-- Run this in Supabase SQL Editor
-- Copy from: migrations/supabase/001_initial.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Connections table
CREATE TABLE connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    gmail_address VARCHAR(255) NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    scopes TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    UNIQUE(user_id, gmail_address)
);

-- OAuth states table
CREATE TABLE oauth_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scopes TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    code_verifier TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_connections_user_id ON connections(user_id);
CREATE INDEX idx_connections_gmail ON connections(gmail_address);
CREATE INDEX idx_oauth_states_expires ON oauth_states(expires_at);
```

4. Get your Supabase credentials:
   - **URL**: `https://xxxxx.supabase.co`
   - **Key**: Service role key from Settings > API

### Option B: SQLite (Simple/Development)

SQLite works for smaller deployments. Just specify a file path.

```bash
# Data will be stored in this file
GMAIL_MCP_STORAGE_SQLITE_PATH=/app/data/gmail.db
```

## Step 3: Server Configuration

### Environment Variables

Set these on your server:

```bash
# Required
GMAIL_MCP_GOOGLE_CLIENT_ID="your-client-id"
GMAIL_MCP_GOOGLE_CLIENT_SECRET="your-client-secret"
GMAIL_MCP_ENCRYPTION_KEY="your-32-byte-base64-key"

# For Supabase
GMAIL_MCP_STORAGE_TYPE="supabase"
GMAIL_MCP_STORAGE_SUPABASE_URL="https://xxxxx.supabase.co"
GMAIL_MCP_STORAGE_SUPABASE_KEY="your-service-role-key"

# OR for SQLite
GMAIL_MCP_STORAGE_TYPE="sqlite"
GMAIL_MCP_STORAGE_SQLITE_PATH="/app/data/gmail.db"

# OAuth redirect (your server's callback URL)
GMAIL_MCP_GOOGLE_REDIRECT_URI="https://your-domain.com/oauth/callback"

# Logging
GMAIL_MCP_LOG_LEVEL="INFO"
GMAIL_MCP_LOG_FORMAT="json"
```

**Generate an encryption key:**
```bash
python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

### Running the Server

**Direct:**
```bash
pip install gmail-multi-user-mcp
gmail-mcp serve --transport http --host 0.0.0.0 --port 8080
```

**With Docker:**
```bash
docker run -d \
  -p 8080:8080 \
  -e GMAIL_MCP_GOOGLE_CLIENT_ID="..." \
  -e GMAIL_MCP_GOOGLE_CLIENT_SECRET="..." \
  -e GMAIL_MCP_ENCRYPTION_KEY="..." \
  -e GMAIL_MCP_STORAGE_TYPE="supabase" \
  -e GMAIL_MCP_STORAGE_SUPABASE_URL="..." \
  -e GMAIL_MCP_STORAGE_SUPABASE_KEY="..." \
  ghcr.io/yourorg/gmail-multi-user-mcp:latest \
  serve --transport http --host 0.0.0.0 --port 8080
```

## Step 4: Integrate with Your Application

### 4.1 User Connects Gmail

When a user wants to connect their Gmail:

```python
import httpx

async def get_gmail_auth_url(your_user_id: str) -> str:
    """Get OAuth URL for a user to connect Gmail."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://your-mcp-server:8080/tools/gmail_get_auth_url",
            json={
                "user_id": your_user_id,  # YOUR app's user ID
                "scopes": [
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send"
                ]
            }
        )
        data = response.json()
        return data["auth_url"]
```

Redirect the user to this URL. After they approve, Google redirects to your callback.

### 4.2 Handle OAuth Callback

```python
async def handle_oauth_callback(code: str, state: str):
    """Handle the OAuth callback from Google."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://your-mcp-server:8080/tools/gmail_handle_oauth_callback",
            json={
                "code": code,
                "state": state
            }
        )
        data = response.json()
        
        if data["success"]:
            # Save connection_id associated with your user
            connection_id = data["connection_id"]
            gmail_address = data["gmail_address"]
            return {"success": True, "connection_id": connection_id}
        else:
            return {"success": False, "error": data["error"]}
```

### 4.3 Use Gmail on Behalf of User

```python
async def search_user_email(connection_id: str, query: str):
    """Search a user's Gmail."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://your-mcp-server:8080/tools/gmail_search",
            json={
                "connection_id": connection_id,
                "query": query,
                "max_results": 10
            }
        )
        return response.json()

async def send_email_for_user(connection_id: str, to: list, subject: str, body: str):
    """Send email from a user's Gmail."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://your-mcp-server:8080/tools/gmail_send",
            json={
                "connection_id": connection_id,
                "to": to,
                "subject": subject,
                "body": body
            }
        )
        return response.json()
```

## Step 5: User Management

### List a User's Connections

```python
async def get_user_connections(user_id: str):
    """Get all Gmail connections for a user."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://your-mcp-server:8080/tools/gmail_list_connections",
            json={"user_id": user_id}
        )
        return response.json()
```

### Disconnect a User's Gmail

```python
async def disconnect_gmail(connection_id: str, revoke: bool = True):
    """Disconnect a Gmail account."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://your-mcp-server:8080/tools/gmail_disconnect",
            json={
                "connection_id": connection_id,
                "revoke_google_access": revoke
            }
        )
        return response.json()
```

## Step 6: Going to Production

### Security Checklist

- [ ] Encryption key is stored securely (not in code)
- [ ] OAuth client secret is stored securely
- [ ] Using HTTPS for all endpoints
- [ ] Database credentials are secured
- [ ] Rate limiting is configured
- [ ] Logging doesn't include sensitive data

### Google OAuth Verification

For production apps with many users:

1. Go to **OAuth consent screen** in Google Cloud
2. Click **Publish App**
3. Complete Google's verification process
4. This removes the "unverified app" warning for users

### Scaling Considerations

| Users | Recommendation |
|-------|----------------|
| < 100 | SQLite is fine |
| 100-10,000 | Supabase free/pro tier |
| 10,000+ | Supabase pro or self-hosted PostgreSQL |

### Monitoring

The MCP server logs in JSON format. Track:
- OAuth success/failure rates
- Token refresh failures
- API errors

```bash
# View logs
docker logs gmail-mcp | jq '.'
```

## Common Integration Patterns

### Pattern 1: Email Assistant Chatbot

```
User: "What emails did I get today?"
     ↓
Your Bot: Calls gmail_search with query "newer_than:1d"
     ↓
Gmail MCP: Fetches emails using user's connection
     ↓
Your Bot: Summarizes and responds to user
```

### Pattern 2: Email Automation

```
Trigger: New email arrives (via webhook/polling)
     ↓
Your App: Calls gmail_search for new emails
     ↓
Your App: Processes email (AI classification, etc.)
     ↓
Your App: Calls gmail_modify_labels or gmail_send (for auto-reply)
```

### Pattern 3: Multi-Account Dashboard

```
User has 3 Gmail accounts connected
     ↓
Your App: Stores 3 connection_ids for user
     ↓
Your App: Queries each connection for unified inbox view
```

## Troubleshooting

### "Invalid client" error
- Check client ID and secret are correct
- Verify redirect URI matches exactly

### "Token refresh failed"
- User may have revoked access
- Check encryption key hasn't changed
- Connection may need re-authentication

### "Rate limited"
- Gmail API has quotas
- Implement exponential backoff
- Consider caching responses

## Next Steps

- [Docker Deployment Guide](06-docker-deployment.md)
- [Troubleshooting](05-troubleshooting.md)
- [API Reference](../docs/api/library.md)
