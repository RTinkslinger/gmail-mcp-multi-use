"""Documentation MCP resources.

These resources provide embedded documentation for setup and troubleshooting.
"""

from __future__ import annotations

from gmail_mcp_server.server import mcp


@mcp.resource("docs://setup")
async def get_setup_docs() -> str:
    """Get quick setup guide.

    Returns markdown documentation for setting up gmail-multi-user-mcp.
    """
    return """# Gmail Multi-User MCP Setup Guide

## Quick Start

### 1. Check Current Status

Run the `gmail_check_setup` tool to see what's configured:

```
gmail_check_setup()
```

### 2. Create Configuration

If you don't have a config file, use `gmail_init_config`:

```
gmail_init_config(
    database_type="sqlite",  # or "supabase"
    google_client_id="your-client-id",
    google_client_secret="your-client-secret"
)
```

### 3. Google OAuth Setup

You need a Google Cloud project with OAuth credentials:

1. Go to https://console.cloud.google.com
2. Create a new project or select existing
3. Enable the Gmail API
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials (Web application type)
6. Add redirect URI: `http://localhost:8000/oauth/callback`
7. Copy client ID and secret to your config

### 4. Connect a Gmail Account

Generate an OAuth URL for a user:

```
gmail_get_auth_url(user_id="user123")
```

Direct the user to the returned URL. After they authorize, handle the callback:

```
gmail_handle_oauth_callback(
    code="authorization_code",
    state_param="state_from_url"
)
```

### 5. Test the Connection

```
gmail_search(
    connection_id="conn_id",
    query="is:unread",
    max_results=5
)
```

## Configuration File

Default location: `./gmail_config.yaml`

See `config://schema` resource for full schema documentation.

## Troubleshooting

If setup fails, check:
- Google Cloud Console credentials match config
- Redirect URI is exactly `http://localhost:8000/oauth/callback`
- Gmail API is enabled in Google Cloud Console
- OAuth consent screen is configured (can use Testing status)

See `docs://troubleshooting` for more help.
"""


@mcp.resource("docs://google-oauth")
async def get_google_oauth_docs() -> str:
    """Get step-by-step Google Cloud OAuth setup guide.

    Returns detailed markdown documentation for setting up Google OAuth.
    """
    return """# Google Cloud OAuth Setup Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "Gmail MCP Integration")
5. Click "Create"

## Step 2: Enable Gmail API

1. In your project, go to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click on it and click "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (or "Internal" if using Google Workspace)
3. Fill in required fields:
   - App name: Your app name
   - User support email: Your email
   - Developer contact: Your email
4. Click "Save and Continue"
5. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/userinfo.email`
6. Click "Save and Continue"
7. Add test users (your Gmail address for testing)
8. Click "Save and Continue"

## Step 4: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Name it (e.g., "Gmail MCP Client")
5. Add Authorized redirect URI:
   ```
   http://localhost:8000/oauth/callback
   ```
6. Click "Create"
7. Copy the Client ID and Client Secret

## Step 5: Update Configuration

Add credentials to your `gmail_config.yaml`:

```yaml
google:
  client_id: "YOUR_CLIENT_ID.apps.googleusercontent.com"
  client_secret: "YOUR_CLIENT_SECRET"
  redirect_uri: "http://localhost:8000/oauth/callback"
  scopes:
    - "https://www.googleapis.com/auth/gmail.readonly"
    - "https://www.googleapis.com/auth/gmail.send"
    - "https://www.googleapis.com/auth/gmail.modify"
    - "https://www.googleapis.com/auth/userinfo.email"
```

## Production Considerations

For production deployment:

1. **Verify your app**: Submit for Google verification to remove the "unverified app" warning
2. **Use HTTPS**: Update redirect URI to use HTTPS in production
3. **Secure secrets**: Use environment variables or secret managers
4. **Rate limits**: Be aware of Gmail API quotas (250 quota units/user/second)

## Common Issues

### "Access blocked: This app's request is invalid"
- Check redirect URI matches exactly (including trailing slashes)
- Ensure OAuth consent screen is configured

### "This app isn't verified"
- For testing: Add your email as a test user
- For production: Submit for verification

### "invalid_grant" error
- Authorization code may have expired (use within 5 minutes)
- Code may have already been used (codes are single-use)
"""


@mcp.resource("docs://troubleshooting")
async def get_troubleshooting_docs() -> str:
    """Get common issues and fixes.

    Returns markdown documentation for troubleshooting common problems.
    """
    return """# Troubleshooting Guide

## Configuration Issues

### "No configuration file found"

**Cause**: No `gmail_config.yaml` found in expected locations.

**Fix**:
1. Create config with `gmail_init_config()` tool
2. Or create manually at `./gmail_config.yaml`
3. Or set `GMAIL_MCP_CONFIG` environment variable

### "Invalid encryption key"

**Cause**: Encryption key is not a valid Fernet key.

**Fix**:
```python
# Generate a new key
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```
Key should be 44 characters ending in `=`

## OAuth Issues

### "invalid_grant" during token exchange

**Causes**:
1. Authorization code expired (5 minute limit)
2. Code already used (single-use)
3. Redirect URI mismatch

**Fix**:
- Generate a new auth URL and try again
- Ensure redirect URI matches exactly in Google Console

### "Access blocked: This app's request is invalid"

**Cause**: Redirect URI mismatch.

**Fix**:
- Check redirect URI in Google Console matches config exactly
- Include trailing slash if present in config

### "This app isn't verified"

**Cause**: OAuth consent screen not verified.

**Fix** (for testing):
- Add test users in Google Console OAuth consent screen
- User must be a test user to authorize

### "Token has been expired or revoked"

**Cause**: Refresh token no longer valid.

**Fix**:
- User needs to re-authorize: generate new auth URL
- Revoke and reconnect: `gmail_disconnect()` then reconnect

## Database Issues

### "Database connection failed"

**For SQLite**:
- Check path is writable
- Check disk space

**For Supabase**:
- Verify URL and key are correct
- Ensure using service role key (not anon key)
- Check if migrations have been run

### "Table does not exist" (Supabase)

**Cause**: Migrations not applied.

**Fix**:
1. Go to Supabase SQL Editor
2. Run contents of `migrations/supabase/001_initial.sql`

## Gmail API Issues

### "Insufficient Permission"

**Cause**: Missing required scope.

**Fix**:
- Add missing scope to config
- User needs to re-authorize with new scopes

### "Rate Limit Exceeded"

**Cause**: Too many API requests.

**Fix**:
- Implement exponential backoff
- Reduce request frequency
- Use batch operations where possible

### "Message not found"

**Causes**:
1. Message was deleted
2. Message ID is from different account
3. Message is in Trash/Spam (not visible by default)

**Fix**:
- Search in trash: add `in:trash` to query
- Verify connection_id matches the account

## Connection Issues

### "Connection not found"

**Cause**: Invalid connection ID.

**Fix**:
- List connections: `gmail_list_connections()`
- Use correct connection ID from list

### "Connection is inactive"

**Cause**: Connection was disconnected or deactivated.

**Fix**:
- User needs to re-authorize
- Generate new auth URL with `gmail_get_auth_url()`

## Still Having Issues?

1. Check logs for detailed error messages
2. Use `gmail_test_connection(verbose=true)` for diagnostics
3. Verify all config values are correct
4. Try creating a fresh config with `gmail_init_config()`
"""
