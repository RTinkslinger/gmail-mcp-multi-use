"""Connect test account MCP prompt."""

from __future__ import annotations

from gmail_mcp_server.server import mcp


@mcp.prompt
def connect_test_account() -> str:
    """Connect developer's Gmail for testing.

    Guides through:
    1. Verifying setup is complete
    2. Generating OAuth URL
    3. Guiding through authorization
    4. Verifying connection
    5. Testing with a search

    Returns instructions for the AI assistant to follow.
    """
    return """# Connect Test Gmail Account

You are helping the user connect their Gmail account for testing.

## Step 1: Verify Setup

First, check that setup is complete:

```
gmail_check_setup()
```

If `ready` is false, suggest running the `setup-gmail` prompt first.

## Step 2: Generate OAuth URL

Generate an authorization URL:

```
gmail_get_auth_url(user_id="test_user")
```

Tell the user:
1. "Click this link to authorize: [auth_url]"
2. "Sign in with your Gmail account"
3. "Click 'Allow' to grant access"
4. "You'll be redirected to a page with an authorization code"

**Important**: The URL expires in ~10 minutes (check `expires_in`).

## Step 3: Handle Callback

Once they have the authorization code:

Ask them to either:
A) Copy the code from the callback URL (after `?code=`)
B) Copy the full callback URL

If they provide the full URL, extract the `code` and `state` parameters.

Then complete the OAuth flow:

```
gmail_handle_oauth_callback(
    code="<authorization_code>",
    state_param="<state_from_url>"
)
```

## Step 4: Verify Connection

If `success` is true, verify the connection works:

```
gmail_check_connection(connection_id="<connection_id>")
```

Confirm:
- `valid` is true
- `gmail_address` matches their email

## Step 5: Test with Search

Run a simple search to verify everything works:

```
gmail_search(
    connection_id="<connection_id>",
    query="is:inbox",
    max_results=5
)
```

Show them the results and confirm:
- They can see their recent emails
- The connection is working properly

## Summary

Provide a summary:
- Connection ID: `<connection_id>`
- Gmail address: `<gmail_address>`
- User ID: `test_user`

Explain how to use the connection:
- Use `connection_id` in gmail_search, gmail_get_message, gmail_send, etc.
- The connection will auto-refresh tokens as needed
- They can disconnect with `gmail_disconnect(connection_id="...")`
"""
