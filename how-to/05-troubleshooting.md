# Troubleshooting Guide

Solutions to common problems when using the Gmail MCP.

## Quick Diagnosis

Run this command to check your setup:

```bash
gmail-mcp health
```

This will show:
- ✅ or ❌ for each component
- Specific error messages

## Authentication Issues

### "Invalid client" or "Client not found"

**What it means:** Your Google OAuth credentials are wrong.

**Fix:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click on your OAuth client
3. Verify Client ID and Client Secret
4. Update your config/environment variables

```bash
# Double-check your credentials
echo $GMAIL_MCP_GOOGLE_CLIENT_ID
echo $GMAIL_MCP_GOOGLE_CLIENT_SECRET
```

### "Redirect URI mismatch"

**What it means:** The callback URL doesn't match what Google expects.

**What you see:**
```
Error 400: redirect_uri_mismatch
```

**Fix:**
1. Go to Google Cloud Console > APIs & Services > Credentials
2. Click your OAuth client
3. Check "Authorized redirect URIs"
4. Add the exact URI your app uses:
   - Local: `http://localhost:8080/oauth/callback`
   - Production: `https://your-domain.com/oauth/callback`

**Important:** URIs must match EXACTLY (including http vs https, trailing slashes).

### "Access blocked: App not verified"

**What it means:** Your Google app is in testing mode.

**Fix for testing:**
1. Go to OAuth consent screen
2. Add your email to "Test users"
3. Try again

**Fix for production:**
1. Click "Publish App" in OAuth consent screen
2. Complete Google's verification process

### "This app is blocked" (User sees this)

**What it means:** User's organization blocks unverified apps.

**Fix:**
- Complete Google verification, OR
- User needs to use a personal Gmail (not work/school)

## Connection Issues

### "Connection not found"

**What it means:** The connection_id doesn't exist.

**Fix:**
1. List all connections:
   ```bash
   gmail-mcp connections list
   ```
2. Use a valid connection ID from the list
3. If empty, connect Gmail first:
   ```bash
   gmail-mcp auth login --user-id "myuser"
   ```

### "Connection inactive"

**What it means:** The connection was deactivated (usually due to token issues).

**Fix:**
1. Re-authenticate:
   ```bash
   gmail-mcp auth login --user-id "myuser"
   ```
2. Or check if user revoked access in Google settings

### "Token expired" or "Token refresh failed"

**What it means:** The stored tokens can't be refreshed.

**Causes:**
- User revoked access in Google Account settings
- Refresh token expired (rare, after 6 months of non-use)
- Encryption key changed

**Fix:**
```bash
# Re-authenticate
gmail-mcp auth login --user-id "your-user-id"
```

If encryption key changed, old tokens can't be decrypted - users must reconnect.

## Configuration Issues

### "Config file not found"

**What it means:** Gmail MCP can't find configuration.

**Fix:**
1. Create config:
   ```bash
   gmail-mcp init
   ```
2. Or set environment variables:
   ```bash
   export GMAIL_MCP_GOOGLE_CLIENT_ID="..."
   export GMAIL_MCP_GOOGLE_CLIENT_SECRET="..."
   export GMAIL_MCP_ENCRYPTION_KEY="..."
   ```
3. Or specify config path:
   ```bash
   export GMAIL_MCP_CONFIG="/path/to/config.yaml"
   ```

### "Invalid encryption key"

**What it means:** The encryption key format is wrong.

**Requirements:**
- Must be 32 bytes, base64-encoded
- Or 64 hex characters

**Generate a valid key:**
```bash
# Base64 format
python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"

# Hex format
python -c "import os; print(os.urandom(32).hex())"
```

### "Storage initialization failed"

**For SQLite:**
```bash
# Check the directory exists and is writable
ls -la ~/.gmail_mcp/

# Check disk space
df -h
```

**For Supabase:**
```bash
# Verify connection
curl -H "apikey: YOUR_KEY" https://YOUR_PROJECT.supabase.co/rest/v1/

# Check environment variables
echo $GMAIL_MCP_STORAGE_SUPABASE_URL
echo $GMAIL_MCP_STORAGE_SUPABASE_KEY
```

## Gmail API Issues

### "Rate limit exceeded"

**What it means:** Too many requests to Gmail API.

**Gmail API limits:**
- 250 quota units per user per second
- 1 billion quota units per day

**Fix:**
1. Add delays between requests
2. Implement exponential backoff
3. Batch requests when possible
4. Cache responses

### "Insufficient permissions"

**What it means:** Missing required OAuth scope.

**Fix:**
1. Check which scopes are needed for your operation
2. Re-authenticate with correct scopes:
   ```bash
   gmail-mcp auth login --user-id "myuser" --scopes "gmail.readonly,gmail.send"
   ```

**Common scopes:**
| Scope | Allows |
|-------|--------|
| `gmail.readonly` | Read emails, labels |
| `gmail.send` | Send emails |
| `gmail.modify` | Modify labels, archive |
| `gmail.compose` | Create drafts |

### "Message not found"

**What it means:** The message ID doesn't exist or was deleted.

**Fix:**
1. Verify the message ID is correct
2. Check if message was deleted/moved
3. Search again to get current message IDs

## Claude Desktop Issues

### Gmail tools not showing up

**Fix:**
1. Quit Claude Desktop completely
2. Check config file syntax:
   ```bash
   # Mac
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
   ```
3. Look for JSON errors
4. Restart Claude Desktop

### "Command not found: gmail-mcp"

**Fix:**
1. Check it's installed:
   ```bash
   pip show gmail-multi-user-mcp
   ```
2. If not installed:
   ```bash
   pip install gmail-multi-user-mcp
   ```
3. Check it's in PATH:
   ```bash
   which gmail-mcp
   ```
4. Use full path in Claude config if needed:
   ```json
   {
     "command": "/Users/you/.local/bin/gmail-mcp"
   }
   ```

### Claude says "I don't have access to Gmail"

**Fix:**
1. Make sure MCP is configured in Claude Desktop config
2. Restart Claude Desktop
3. Check the connection:
   ```
   You: "What Gmail tools do you have available?"
   ```
4. If no tools listed, check server logs

## Docker Issues

### Container exits immediately

**Fix:**
```bash
# Check logs
docker logs gmail-mcp

# Common causes:
# - Missing environment variables
# - Invalid config
# - Port already in use
```

### Can't connect to MCP server

**Fix:**
```bash
# Check container is running
docker ps

# Check port mapping
docker port gmail-mcp

# Test connectivity
curl http://localhost:8080/health
```

### "Permission denied" in container

**Fix:**
```bash
# Check volume permissions
ls -la /path/to/data

# Container runs as non-root user (gmailmcp)
# Make sure mounted volumes are accessible
chmod 755 /path/to/data
```

## Getting Help

### Collect debug information

```bash
# Version info
gmail-mcp --version
python --version

# Configuration (without secrets)
gmail-mcp health

# Recent logs (if using file logging)
tail -100 ~/.gmail_mcp/logs/gmail_mcp.log
```

### Enable debug logging

```bash
export GMAIL_MCP_LOG_LEVEL=DEBUG
gmail-mcp serve
```

### Check for updates

```bash
pip install --upgrade gmail-multi-user-mcp
```

## Error Code Reference

| Code | Meaning | Fix |
|------|---------|-----|
| `AUTH_001` | Invalid state parameter | Restart OAuth flow |
| `AUTH_002` | State expired | Complete OAuth within 10 minutes |
| `AUTH_003` | Code exchange failed | Check client secret |
| `TOKEN_001` | Decryption failed | Encryption key changed |
| `TOKEN_002` | Refresh failed | Re-authenticate |
| `TOKEN_003` | Token revoked | Re-authenticate |
| `GMAIL_001` | API error | Check scopes, quotas |
| `GMAIL_002` | Rate limited | Slow down requests |
| `GMAIL_003` | Not found | Check message/thread ID |
| `CONFIG_001` | Missing required field | Check config file |
| `CONFIG_002` | Invalid value | Check config format |

## Still Stuck?

1. Check [existing issues](https://github.com/yourorg/gmail-multi-user-mcp/issues)
2. Open a new issue with:
   - Error message (full text)
   - What you were trying to do
   - Output of `gmail-mcp health`
   - Steps to reproduce
