# Google OAuth Setup Guide

This guide walks through setting up Google OAuth credentials for gmail-multi-user-mcp.

## Overview

Gmail API access requires OAuth 2.0 authentication. You'll need:
1. A Google Cloud project
2. Gmail API enabled
3. OAuth consent screen configured
4. OAuth 2.0 client credentials

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "Gmail MCP Integration")
5. Click "Create"
6. Wait for the project to be created
7. Select the new project from the dropdown

## Step 2: Enable Gmail API

1. In your project, go to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "Enable"
5. Wait for the API to be enabled

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select user type:
   - **Internal**: Only users in your Google Workspace organization (requires Workspace)
   - **External**: Any Google account (use this for development)
3. Click "Create"

### App Information

Fill in the required fields:
- **App name**: Your application name (e.g., "My Email App")
- **User support email**: Your email address
- **Developer contact information**: Your email address

Click "Save and Continue"

### Scopes

Click "Add or Remove Scopes" and add:

| Scope | Description |
|-------|-------------|
| `https://www.googleapis.com/auth/gmail.readonly` | Read emails |
| `https://www.googleapis.com/auth/gmail.send` | Send emails |
| `https://www.googleapis.com/auth/gmail.modify` | Modify labels, archive, trash |
| `https://www.googleapis.com/auth/userinfo.email` | Get user's email address |

Click "Update" then "Save and Continue"

### Test Users (External Only)

For external apps in testing mode, add test users:
1. Click "Add Users"
2. Enter the Gmail addresses that will test your app
3. Click "Add"
4. Click "Save and Continue"

### Summary

Review your settings and click "Back to Dashboard"

## Step 4: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Enter a name (e.g., "Gmail MCP Client")
5. Under "Authorized redirect URIs", add:
   ```
   http://localhost:8000/oauth/callback
   ```
6. Click "Create"
7. **Copy the Client ID and Client Secret** - you'll need these!

## Step 5: Update Configuration

Edit your `gmail_config.yaml`:

```yaml
google:
  client_id: "123456789-abcdefg.apps.googleusercontent.com"
  client_secret: "GOCSPX-your-secret-here"
  redirect_uri: "http://localhost:8000/oauth/callback"
  scopes:
    - "https://www.googleapis.com/auth/gmail.readonly"
    - "https://www.googleapis.com/auth/gmail.send"
    - "https://www.googleapis.com/auth/gmail.modify"
    - "https://www.googleapis.com/auth/userinfo.email"
```

## Production Considerations

### Publishing Your App

For production with external users:

1. Go to "OAuth consent screen"
2. Click "Publish App"
3. Complete the verification process (may take days/weeks)

Until published, only test users can use your app.

### Redirect URIs

For production, add your actual domain:
```
https://yourdomain.com/oauth/callback
```

Update `gmail_config.yaml`:
```yaml
google:
  redirect_uri: "https://yourdomain.com/oauth/callback"
```

### Security Best Practices

1. **Never commit credentials**: Add `gmail_config.yaml` to `.gitignore`
2. **Use environment variables**: Override config with env vars
   ```bash
   export GMAIL_MCP_GOOGLE__CLIENT_ID="your-client-id"
   export GMAIL_MCP_GOOGLE__CLIENT_SECRET="your-client-secret"
   ```
3. **Rotate secrets**: Periodically regenerate client secret
4. **Limit scopes**: Only request scopes you actually need

## Troubleshooting

### "redirect_uri_mismatch"

**Cause**: Redirect URI doesn't match exactly.

**Fix**: Ensure URIs match exactly:
- Check trailing slashes
- Check http vs https
- Check port numbers

### "Access denied"

**Cause**: User not added as test user (for apps in testing).

**Fix**: Add user to test users list in OAuth consent screen.

### "This app isn't verified"

**Cause**: App is in testing mode and shows warning.

**Fix**: This is expected during development. Users can:
1. Click "Advanced"
2. Click "Go to [App Name] (unsafe)"

For production, complete the verification process.

### "Error 400: invalid_request"

**Cause**: Often a scope issue.

**Fix**: Verify scopes are:
1. Added to OAuth consent screen
2. Listed in your config file
3. Using correct format (full URL)

### "Quota exceeded"

**Cause**: Too many API calls.

**Fix**: Gmail API has rate limits:
- 250 quota units per user per second
- 1,000,000,000 quota units per day

Implement rate limiting in your application.

## Scope Reference

| Scope | Allows | Use When |
|-------|--------|----------|
| `gmail.readonly` | Read emails, labels, threads | Read-only access |
| `gmail.send` | Send emails | Sending emails |
| `gmail.modify` | Modify labels, archive, trash | Managing emails |
| `gmail.compose` | Create drafts | Draft management |
| `gmail.labels` | Create/edit labels | Custom labels |
| `userinfo.email` | Get user's email | Identifying user |

## Environment Variable Reference

All Google OAuth settings can be overridden via environment variables:

| Setting | Environment Variable |
|---------|---------------------|
| client_id | `GMAIL_MCP_GOOGLE__CLIENT_ID` |
| client_secret | `GMAIL_MCP_GOOGLE__CLIENT_SECRET` |
| redirect_uri | `GMAIL_MCP_GOOGLE__REDIRECT_URI` |

Note the double underscore (`__`) for nested settings.
