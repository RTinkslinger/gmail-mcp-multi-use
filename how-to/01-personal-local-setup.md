# Personal Local Setup

This guide helps you set up the Gmail MCP on your own computer to access your Gmail through AI tools or scripts.

**Time needed:** 15-20 minutes  
**Difficulty:** Beginner  
**What you'll need:**
- Python 3.10 or newer
- A Google account
- 15 minutes to set up Google OAuth credentials

## Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Your Script   │ ──► │   Gmail MCP     │ ──► │   Gmail API     │
│   or AI Tool    │     │   (this tool)   │     │   (Google)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Step 1: Install the Package

Open your terminal and run:

```bash
pip install gmail-multi-user-mcp
```

**Verify it worked:**
```bash
gmail-mcp --help
```

You should see a list of commands.

## Step 2: Get Google OAuth Credentials

Before the MCP can access Gmail, you need credentials from Google. This is a one-time setup.

**Quick version:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop app type)
5. Download the credentials

**Detailed instructions:** See [Google OAuth Setup Guide](04-google-oauth-setup.md)

You'll get:
- **Client ID** - looks like: `123456789-abc123.apps.googleusercontent.com`
- **Client Secret** - looks like: `GOCSPX-abc123xyz`

## Step 3: Create Your Configuration

Run the initialization command:

```bash
gmail-mcp init
```

This creates a config file at `~/.gmail_mcp/config.yaml`.

**Edit the config file:**

```yaml
# ~/.gmail_mcp/config.yaml

# Your Google OAuth credentials (from Step 2)
google:
  client_id: "YOUR_CLIENT_ID_HERE"
  client_secret: "YOUR_CLIENT_SECRET_HERE"
  redirect_uri: "http://localhost:8080/oauth/callback"
  scopes:
    - "https://www.googleapis.com/auth/gmail.readonly"
    - "https://www.googleapis.com/auth/gmail.send"
    - "https://www.googleapis.com/auth/gmail.modify"

# Where to store data (SQLite is fine for personal use)
storage:
  type: "sqlite"
  sqlite:
    path: "~/.gmail_mcp/gmail.db"

# Security - generate a random key (see below)
encryption:
  key: "YOUR_ENCRYPTION_KEY_HERE"
```

**Generate an encryption key:**

```bash
python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

Copy the output and paste it as your encryption key.

## Step 4: Connect Your Gmail Account

Start the OAuth flow:

```bash
gmail-mcp auth login --user-id "me"
```

This will:
1. Open your browser
2. Ask you to sign in to Google
3. Ask you to grant access to Gmail
4. Redirect back and save your tokens

**Success looks like:**
```
✓ Successfully connected: your.email@gmail.com
Connection ID: conn_abc123
```

## Step 5: Test It Works

**Check your connection:**
```bash
gmail-mcp connections list
```

**Search your email (using the CLI):**
```bash
gmail-mcp test search "from:someone@example.com"
```

## Step 6: Use It in Your Code

**Python example:**

```python
from gmail_multi_user import GmailService
from gmail_multi_user.config import ConfigLoader

# Load your config
config = ConfigLoader.load()

# Create the service
async def main():
    service = GmailService(config)
    await service.initialize()
    
    # Search emails
    results = await service.search(
        connection_id="conn_abc123",  # from step 4
        query="is:unread",
        max_results=10
    )
    
    for msg in results.messages:
        print(f"From: {msg.from_address}")
        print(f"Subject: {msg.subject}")
        print("---")
    
    await service.close()

import asyncio
asyncio.run(main())
```

## Common Tasks

### Read unread emails
```python
results = await service.search(connection_id, "is:unread")
```

### Send an email
```python
result = await service.send(
    connection_id=connection_id,
    to=["recipient@example.com"],
    subject="Hello!",
    body="This is my message."
)
```

### Get a specific email
```python
message = await service.get_message(connection_id, message_id)
print(message.body_plain)
```

### List labels
```python
labels = await service.list_labels(connection_id)
for label in labels:
    print(label.name)
```

## File Locations

| What | Where |
|------|-------|
| Config file | `~/.gmail_mcp/config.yaml` |
| Database | `~/.gmail_mcp/gmail.db` |
| Logs | `~/.gmail_mcp/logs/` |

## Next Steps

- [Use with Claude Desktop](02-personal-claude-desktop.md)
- [Troubleshooting](05-troubleshooting.md)

## Security Notes

- Your Gmail tokens are encrypted before storage
- The encryption key never leaves your machine
- Tokens auto-refresh (you won't need to re-authenticate)
- You can revoke access anytime in [Google Account Settings](https://myaccount.google.com/permissions)
