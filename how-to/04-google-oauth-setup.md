# Google OAuth Setup Guide

This guide walks you through creating Google OAuth credentials step-by-step with screenshots descriptions.

**Time needed:** 10-15 minutes  
**What you'll get:** Client ID and Client Secret for Gmail access

## Step 1: Go to Google Cloud Console

1. Open [console.cloud.google.com](https://console.cloud.google.com/)
2. Sign in with your Google account

## Step 2: Create a Project

1. Click the project dropdown at the top (might say "Select a project")
2. Click **New Project**
3. Enter a name: e.g., "Gmail MCP" or "My Email Agent"
4. Click **Create**
5. Wait for it to be created, then select it

```
┌─────────────────────────────────────────┐
│  Google Cloud Console                    │
├─────────────────────────────────────────┤
│  [Select Project ▼]                      │
│                                          │
│  ┌─────────────────────────────────┐    │
│  │  New Project                     │    │
│  │                                  │    │
│  │  Project name: Gmail MCP         │    │
│  │  [Create]                        │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Step 3: Enable Gmail API

1. In the left sidebar, go to **APIs & Services** > **Library**
2. Search for **"Gmail API"**
3. Click on **Gmail API**
4. Click the blue **Enable** button

```
┌─────────────────────────────────────────┐
│  Gmail API                               │
│                                          │
│  Google                                  │
│  Access Gmail mailboxes including        │
│  sending user email.                     │
│                                          │
│  [        ENABLE        ]                │
└─────────────────────────────────────────┘
```

## Step 4: Configure OAuth Consent Screen

Before creating credentials, you must set up the consent screen (what users see when connecting).

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose user type:
   - **Internal**: Only for your Google Workspace org (if applicable)
   - **External**: For any Google account (choose this for most cases)
3. Click **Create**

### Fill in App Information

| Field | What to enter |
|-------|---------------|
| App name | Your app's name (e.g., "My Email Assistant") |
| User support email | Your email address |
| App logo | Optional - upload if you have one |
| App domain | Optional for testing |
| Developer contact | Your email address |

Click **Save and Continue**

### Add Scopes

1. Click **Add or Remove Scopes**
2. Search and select these scopes:

| Scope | Purpose |
|-------|---------|
| `https://www.googleapis.com/auth/gmail.readonly` | Read emails |
| `https://www.googleapis.com/auth/gmail.send` | Send emails |
| `https://www.googleapis.com/auth/gmail.modify` | Modify labels, archive, etc. |
| `https://www.googleapis.com/auth/userinfo.email` | Get user's email address |

3. Click **Update**
4. Click **Save and Continue**

### Add Test Users (Important!)

While your app is in "Testing" mode:

1. Click **Add Users**
2. Enter email addresses that can test the app
3. Add your own email
4. Click **Save and Continue**

**Note:** Only test users can use your app until you publish it.

## Step 5: Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**

### Choose Application Type

| If you're... | Choose |
|--------------|--------|
| Using with Claude Desktop or local scripts | **Desktop app** |
| Building a web application | **Web application** |
| Building a mobile app | **iOS** or **Android** |

### For Desktop App

1. Select **Desktop app**
2. Name it: "Gmail MCP Desktop"
3. Click **Create**

### For Web Application

1. Select **Web application**
2. Name it: "Gmail MCP Web"
3. Under **Authorized redirect URIs**, click **Add URI**
4. Add your callback URL:
   - For local testing: `http://localhost:8080/oauth/callback`
   - For production: `https://yourdomain.com/oauth/callback`
5. Click **Create**

```
┌─────────────────────────────────────────┐
│  Create OAuth client ID                  │
├─────────────────────────────────────────┤
│  Application type: Web application       │
│                                          │
│  Name: Gmail MCP Web                     │
│                                          │
│  Authorized redirect URIs:               │
│  ┌─────────────────────────────────────┐│
│  │ http://localhost:8080/oauth/callback ││
│  │ https://myapp.com/oauth/callback     ││
│  └─────────────────────────────────────┘│
│                                          │
│  [        CREATE        ]                │
└─────────────────────────────────────────┘
```

## Step 6: Get Your Credentials

After clicking Create, you'll see:

```
┌─────────────────────────────────────────┐
│  OAuth client created                    │
├─────────────────────────────────────────┤
│                                          │
│  Client ID:                              │
│  123456789-abc123.apps.googleusercontent.com
│                                          │
│  Client Secret:                          │
│  GOCSPX-abcdef123456                     │
│                                          │
│  [Download JSON]  [OK]                   │
└─────────────────────────────────────────┘
```

**Save these values!** You'll need them for configuration.

**Option:** Click **Download JSON** to save credentials as a file.

## Step 7: Use Your Credentials

### In Environment Variables

```bash
export GMAIL_MCP_GOOGLE_CLIENT_ID="123456789-abc123.apps.googleusercontent.com"
export GMAIL_MCP_GOOGLE_CLIENT_SECRET="GOCSPX-abcdef123456"
```

### In Config File

```yaml
# ~/.gmail_mcp/config.yaml
google:
  client_id: "123456789-abc123.apps.googleusercontent.com"
  client_secret: "GOCSPX-abcdef123456"
  redirect_uri: "http://localhost:8080/oauth/callback"
```

## Common Issues

### "Access blocked: This app's request is invalid"

**Cause:** Redirect URI doesn't match.

**Fix:** Make sure the redirect URI in your config exactly matches what's in Google Cloud Console.

### "Error 403: access_denied"

**Cause:** User not added as test user.

**Fix:** Add the user's email to test users in OAuth consent screen.

### "This app isn't verified"

**Cause:** Normal for apps in testing mode.

**Fix:** 
- For testing: Click "Continue" (user will see warning)
- For production: Submit app for Google verification

## Going to Production

When ready for real users:

1. Go to **OAuth consent screen**
2. Click **Publish App**
3. Complete verification (Google reviews your app)
4. Once verified, any Google user can connect

### Verification Requirements

Google requires:
- Privacy policy URL
- Terms of service URL  
- Explanation of why you need each scope
- Demo video (for sensitive scopes)

This process takes 2-4 weeks typically.

## Security Best Practices

1. **Never commit credentials to git**
   ```bash
   # .gitignore
   .env
   credentials.json
   *secret*
   ```

2. **Use environment variables in production**

3. **Rotate credentials** if they're ever exposed

4. **Use minimum scopes** - only request what you need

5. **Store client secret securely**
   - Use secrets manager (AWS Secrets Manager, HashiCorp Vault)
   - Never log credentials

## Quick Reference

| What | Where to find it |
|------|------------------|
| Client ID | APIs & Services > Credentials |
| Client Secret | APIs & Services > Credentials |
| Add test users | APIs & Services > OAuth consent screen |
| Add redirect URIs | APIs & Services > Credentials > Edit OAuth client |
| Enable APIs | APIs & Services > Library |

## Next Steps

- [Personal Local Setup](01-personal-local-setup.md)
- [Claude Desktop Setup](02-personal-claude-desktop.md)
- [Production Setup](03-production-agent-setup.md)
