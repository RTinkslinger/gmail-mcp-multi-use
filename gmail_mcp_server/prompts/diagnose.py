"""Diagnose connection MCP prompt."""

from __future__ import annotations

from gmail_mcp_server.server import mcp


@mcp.prompt
def diagnose_connection(connection_id: str | None = None) -> str:
    """Debug a failing Gmail connection.

    Args:
        connection_id: Optional connection ID to diagnose. If not provided,
                       will list connections and ask user to select.

    Guides through:
    1. Listing connections if not specified
    2. Checking connection status
    3. Identifying the issue
    4. Providing solution
    5. Testing the fix

    Returns instructions for the AI assistant to follow.
    """
    connection_filter = ""
    if connection_id:
        connection_filter = f"Diagnose connection: `{connection_id}`"
    else:
        connection_filter = (
            "No connection specified - will list and ask user to select."
        )

    return f"""# Diagnose Gmail Connection

You are helping the user debug a failing Gmail connection.

{connection_filter}

## Step 1: Identify the Connection

{"If no connection_id provided:" if not connection_id else ""}

```
gmail_list_connections(include_inactive=true)
```

{"Ask the user which connection they want to diagnose." if not connection_id else ""}

## Step 2: Check Connection Status

Check the connection's status:

```
gmail_check_connection(connection_id="<connection_id>")
```

Review the output:
- `valid`: Is the connection working?
- `needs_reauth`: Does the user need to re-authorize?
- `token_expires_in`: When does the token expire?
- `error`: What error occurred?

## Step 3: Diagnose the Issue

Based on the status, identify the issue:

### Issue: needs_reauth is true
**Cause**: Token has expired or been revoked.
**Solution**: User needs to re-authorize. Generate a new auth URL:

```
gmail_get_auth_url(user_id="<user_id>")
```

### Issue: Connection not found
**Cause**: Invalid connection ID or connection was deleted.
**Solution**: List all connections and find the correct one:

```
gmail_list_connections()
```

### Issue: Connection is inactive
**Cause**: Connection was disconnected.
**Solution**: User needs to reconnect. Generate a new auth URL.

### Issue: Token validation failed
**Cause**: Could be network issue, Google API issue, or invalid credentials.
**Solution**:
1. Check Google Cloud Console - is the OAuth client still valid?
2. Try again in a few minutes (transient error)
3. If persistent, re-authorize

## Step 4: Test the Fix

After applying the fix, verify it worked:

```
gmail_check_connection(connection_id="<connection_id>")
```

Then test with a simple operation:

```
gmail_search(
    connection_id="<connection_id>",
    query="is:inbox",
    max_results=1
)
```

## Step 5: Additional Diagnostics

If the issue persists, run comprehensive tests:

```
gmail_test_connection(verbose=true)
```

Check:
- Database connectivity
- Google OAuth configuration
- Network connectivity

## Common Issues Reference

Refer to the troubleshooting docs for more information:

Resource: `docs://troubleshooting`

Provide relevant troubleshooting steps based on the specific error.
"""
