# Using Gmail MCP with Claude Desktop

This guide shows you how to connect Gmail to Claude Desktop so Claude can read and send emails for you.

**Time needed:** 20 minutes  
**Difficulty:** Beginner  
**What you'll need:**
- Claude Desktop installed
- Python 3.10 or newer
- Google OAuth credentials (we'll create these)

## What You'll Be Able to Do

After setup, you can ask Claude things like:
- "What unread emails do I have?"
- "Summarize the emails from my boss this week"
- "Draft a reply to the last email from John"
- "Send an email to team@company.com about the meeting"

## Step 1: Install the Gmail MCP

Open Terminal (Mac) or Command Prompt (Windows) and run:

```bash
pip install gmail-multi-user-mcp
```

**Check it installed:**
```bash
gmail-mcp --version
```

## Step 2: Set Up Google OAuth

You need credentials from Google. Follow the [Google OAuth Setup Guide](04-google-oauth-setup.md).

You'll get a **Client ID** and **Client Secret**.

## Step 3: Create Configuration

**Option A: Quick setup with environment variables**

Create a file called `.env` in your home directory:

```bash
# ~/.gmail_mcp.env (or set these in your shell profile)

export GMAIL_MCP_GOOGLE_CLIENT_ID="your-client-id-here"
export GMAIL_MCP_GOOGLE_CLIENT_SECRET="your-client-secret-here"
export GMAIL_MCP_ENCRYPTION_KEY="generate-a-key-see-below"
```

Generate the encryption key:
```bash
python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

**Option B: Use a config file**

```bash
gmail-mcp init
```

Then edit `~/.gmail_mcp/config.yaml` with your credentials.

## Step 4: Connect Your Gmail

Run:
```bash
gmail-mcp auth login --user-id "claude-user"
```

Your browser will open. Sign in and grant access.

**Save the Connection ID** that's shown - you'll need it!

```
✓ Successfully connected: your.email@gmail.com
Connection ID: conn_abc123xyz    <-- Save this!
```

## Step 5: Configure Claude Desktop

Find your Claude Desktop config file:

| OS | Location |
|----|----------|
| Mac | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Edit the file to add the Gmail MCP:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "gmail-mcp",
      "args": ["serve"],
      "env": {
        "GMAIL_MCP_GOOGLE_CLIENT_ID": "your-client-id",
        "GMAIL_MCP_GOOGLE_CLIENT_SECRET": "your-client-secret",
        "GMAIL_MCP_ENCRYPTION_KEY": "your-encryption-key"
      }
    }
  }
}
```

**If you used a config file instead:**

```json
{
  "mcpServers": {
    "gmail": {
      "command": "gmail-mcp",
      "args": ["serve"],
      "env": {
        "GMAIL_MCP_CONFIG": "/path/to/your/config.yaml"
      }
    }
  }
}
```

## Step 6: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Open Claude Desktop again
3. You should see Gmail tools available

## Step 7: Test It!

In Claude Desktop, try asking:

> "Can you check my Gmail for unread messages?"

Claude should use the Gmail tools to search your inbox.

**If Claude asks for a connection ID**, give it the one from Step 4:

> "Use connection ID conn_abc123xyz"

## Tips for Talking to Claude About Email

### Reading emails
- "Show me unread emails"
- "Find emails from john@example.com"
- "Get emails from the last week with attachments"
- "Search for emails about 'project update'"

### Sending emails
- "Send an email to jane@example.com saying I'll be late"
- "Reply to the last email from my boss"
- "Draft an email to the team about the meeting"

### Managing emails
- "Archive emails older than 30 days"
- "Mark all emails from newsletters as read"
- "Move emails from 'promotions' to trash"

## Troubleshooting

### "No Gmail tools available"

1. Check Claude Desktop was restarted
2. Verify the config file path is correct
3. Check for JSON syntax errors in the config

### "Connection not found"

Run `gmail-mcp connections list` to see your connections and get the right ID.

### "Token expired"

The MCP auto-refreshes tokens, but if it fails:
```bash
gmail-mcp auth login --user-id "claude-user"
```

### "Permission denied"

Make sure you granted all the requested permissions when connecting Gmail.

## Security FAQ

**Q: Can Claude access all my emails?**  
A: Yes, within the scopes you granted. You control this in the Google OAuth setup.

**Q: Are my emails stored anywhere?**  
A: No. Claude reads emails on-demand. Only auth tokens are stored (encrypted).

**Q: Can I revoke access?**  
A: Yes! Go to [Google Account Permissions](https://myaccount.google.com/permissions) and remove the app.

**Q: Is my data sent to anyone else?**  
A: Email content goes: Gmail → MCP → Claude. The MCP doesn't log or store email content.

## Next Steps

- Learn about [production setups](03-production-agent-setup.md) if building for others
- See [troubleshooting](05-troubleshooting.md) for more help
