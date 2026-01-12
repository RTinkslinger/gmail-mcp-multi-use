"""Setup wizard MCP prompt."""

from __future__ import annotations

from gmail_mcp_server.server import mcp


@mcp.prompt
def setup_gmail() -> str:
    """Complete setup wizard for gmail-multi-user-mcp.

    Guides through:
    1. Checking current setup status
    2. Creating configuration if needed
    3. Setting up Google OAuth
    4. Running migrations
    5. Testing configuration
    6. Connecting a test account

    Returns instructions for the AI assistant to follow.
    """
    return """# Gmail Multi-User MCP Setup Wizard

You are helping the user set up gmail-multi-user-mcp. Follow these steps:

## Step 1: Check Current Status

First, check what's already configured:

```
gmail_check_setup()
```

Review the output and explain the current state to the user.

## Step 2: Create Configuration (if needed)

If `config_found` is false, help create a config:

1. Ask the user which storage backend they want:
   - **SQLite** (default): Simple, local storage. Great for development.
   - **Supabase**: Cloud PostgreSQL. Great for production/multi-server.

2. Ask if they have Google OAuth credentials already. If not, guide them to:
   - Go to https://console.cloud.google.com
   - Create/select a project
   - Enable Gmail API
   - Set up OAuth consent screen
   - Create OAuth 2.0 credentials (Web application)
   - Add redirect URI: `http://localhost:8000/oauth/callback`

3. Once they have credentials, create the config:

```
gmail_init_config(
    database_type="sqlite",  # or "supabase"
    google_client_id="<their client id>",
    google_client_secret="<their client secret>"
)
```

## Step 3: Run Migrations (for Supabase)

If using Supabase:

```
gmail_run_migrations()
```

If migrations haven't been applied, guide them to:
1. Go to their Supabase project
2. Open SQL Editor
3. Run the migration from `migrations/supabase/001_initial.sql`

## Step 4: Test Configuration

Verify everything is working:

```
gmail_test_connection(verbose=true)
```

Check that:
- `database_ok` is true
- `google_oauth_ok` is true

If there are errors, help troubleshoot using `docs://troubleshooting`.

## Step 5: Offer Test Account Connection

If everything is configured, offer to help connect a test Gmail account:

"Would you like to connect a test Gmail account now? I can help you through the OAuth flow."

If yes, generate an auth URL:

```
gmail_get_auth_url(user_id="test_user")
```

Guide them to:
1. Open the auth_url in a browser
2. Sign in with their Gmail account
3. Authorize the app
4. Copy the authorization code from the callback URL
5. Complete the callback

## Done!

Once setup is complete, show a summary:
- Configuration location
- Storage type
- Connected accounts
- Next steps (using the gmail_search, gmail_send tools)
"""
