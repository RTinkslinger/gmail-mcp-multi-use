# Quickstart Guide

Get started with gmail-multi-user-mcp in under 5 minutes.

## Prerequisites

- Python 3.10 or higher
- Google Cloud account (for OAuth credentials)
- Gmail account for testing

## Installation

```bash
pip install gmail-multi-user-mcp
```

## Step 1: Create Configuration

Run the init command to create a configuration file:

```bash
gmail-mcp init
```

This creates `gmail_config.yaml` with:
- A generated encryption key
- Placeholder OAuth credentials
- SQLite database configuration

## Step 2: Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Configure OAuth consent screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" user type
   - Fill in app name and developer email
   - Add scopes: `gmail.readonly`, `gmail.send`, `gmail.modify`, `userinfo.email`
5. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application"
   - Add redirect URI: `http://localhost:8000/oauth/callback`
   - Copy the Client ID and Client Secret

## Step 3: Update Configuration

Edit `gmail_config.yaml`:

```yaml
encryption_key: <keep the generated key>

google:
  client_id: "your-client-id.apps.googleusercontent.com"
  client_secret: "your-client-secret"
  redirect_uri: "http://localhost:8000/oauth/callback"
  scopes:
    - "https://www.googleapis.com/auth/gmail.readonly"
    - "https://www.googleapis.com/auth/gmail.send"
    - "https://www.googleapis.com/auth/gmail.modify"
    - "https://www.googleapis.com/auth/userinfo.email"

storage:
  type: sqlite
  sqlite:
    path: gmail_mcp.db
```

## Step 4: Verify Configuration

Check that everything is set up correctly:

```bash
gmail-mcp health
```

Expected output:
```
Gmail MCP Health Check

✓ Config found: /path/to/gmail_config.yaml
✓ Database connected (sqlite)
✓ Google OAuth configured
✓ Encryption key set

System is ready!
```

## Step 5: Connect Your Gmail

Now connect a Gmail account for testing.

### Using the CLI

```bash
gmail-mcp connections list
# (Should show no connections yet)
```

### Using Python

```python
import asyncio
from gmail_multi_user.config import ConfigLoader
from gmail_multi_user.storage.factory import StorageFactory
from gmail_multi_user.tokens.encryption import TokenEncryption
from gmail_multi_user.oauth.manager import OAuthManager

async def connect():
    # Load config
    config = ConfigLoader.load()

    # Initialize storage
    storage = StorageFactory.create(config)
    await storage.initialize()

    # Create OAuth manager
    encryption = TokenEncryption(config.encryption_key)
    oauth = OAuthManager(config=config, storage=storage, encryption=encryption)

    # Generate auth URL
    result = await oauth.get_auth_url(user_id="my_user_id")
    print(f"Open this URL in your browser:\n{result.auth_url}")
    print(f"\nState: {result.state}")

    await oauth.close()
    await storage.close()

asyncio.run(connect())
```

1. Open the printed URL in your browser
2. Sign in with your Gmail account
3. Click "Allow" to grant access
4. You'll be redirected to `localhost:8000/oauth/callback?code=...&state=...`
5. Copy the `code` and `state` parameters

### Complete the OAuth Flow

```python
import asyncio
from gmail_multi_user.config import ConfigLoader
from gmail_multi_user.storage.factory import StorageFactory
from gmail_multi_user.tokens.encryption import TokenEncryption
from gmail_multi_user.oauth.manager import OAuthManager

async def complete_oauth():
    config = ConfigLoader.load()
    storage = StorageFactory.create(config)
    await storage.initialize()
    encryption = TokenEncryption(config.encryption_key)
    oauth = OAuthManager(config=config, storage=storage, encryption=encryption)

    # Use the code and state from the callback URL
    result = await oauth.handle_callback(
        code="your_authorization_code",
        state="your_state_parameter"
    )

    if result.success:
        print(f"Connected! Connection ID: {result.connection_id}")
        print(f"Gmail: {result.gmail_address}")
    else:
        print(f"Error: {result.error}")

    await oauth.close()
    await storage.close()

asyncio.run(complete_oauth())
```

## Step 6: Read Your Emails

Now you can access Gmail:

```python
import asyncio
from gmail_multi_user.config import ConfigLoader
from gmail_multi_user.storage.factory import StorageFactory
from gmail_multi_user.tokens.encryption import TokenEncryption
from gmail_multi_user.tokens.manager import TokenManager
from gmail_multi_user.service import GmailService

async def read_emails():
    # Setup
    config = ConfigLoader.load()
    storage = StorageFactory.create(config)
    await storage.initialize()
    encryption = TokenEncryption(config.encryption_key)
    token_manager = TokenManager(config=config, storage=storage, encryption=encryption)

    # Create service
    service = GmailService(
        config=config,
        storage=storage,
        token_manager=token_manager
    )

    # Search unread emails
    result = await service.search(
        connection_id="your_connection_id",  # From Step 5
        query="is:unread",
        max_results=5
    )

    print(f"Found {len(result.messages)} unread emails:")
    for msg in result.messages:
        print(f"  - {msg.subject} (from {msg.from_.email})")

    # Cleanup
    await service.close()
    await storage.close()

asyncio.run(read_emails())
```

## Next Steps

- **Send emails**: See [Library API Reference](../api/library.md#send)
- **Use MCP server**: See [MCP Integration Guide](mcp-integration.md)
- **Multi-user setup**: See [Multi-User Guide](multi-user.md)
- **Production deployment**: See [Deployment Guide](deployment.md)

## Troubleshooting

### "Config not found"

Make sure you're running commands from the directory containing `gmail_config.yaml`, or set:
```bash
export GMAIL_MCP_CONFIG=/path/to/gmail_config.yaml
```

### "Database connection failed"

For SQLite, ensure the directory exists and is writable:
```bash
mkdir -p /path/to/db/directory
```

### "Google OAuth not configured"

Double-check your `client_id` and `client_secret` in the config file.

### "redirect_uri_mismatch" error

Ensure the redirect URI in your config matches exactly what's in Google Cloud Console.
