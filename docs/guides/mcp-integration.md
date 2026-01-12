# MCP Integration Guide

This guide covers integrating the Gmail MCP server with MCP clients like Claude Desktop.

## What is MCP?

Model Context Protocol (MCP) is a standard for AI assistants to interact with external tools and data sources. The Gmail MCP server exposes Gmail functionality as:

- **Tools**: Actions the AI can take (search, send, etc.)
- **Resources**: Data the AI can read (config status, labels, etc.)
- **Prompts**: Pre-defined workflows (setup wizard, diagnostics, etc.)

## Claude Desktop Integration

### Step 1: Configure Claude Desktop

Edit Claude Desktop's MCP configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the Gmail MCP server:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "gmail-mcp",
      "args": ["serve"],
      "env": {
        "GMAIL_MCP_CONFIG": "/path/to/gmail_config.yaml"
      }
    }
  }
}
```

### Step 2: Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

### Step 3: Verify Connection

In Claude Desktop, you should see Gmail tools available. Try:

```
"Check if Gmail is configured"
```

Claude will call `gmail_check_setup()` and report the status.

---

## Available Capabilities

### Tools (18 total)

| Tool | Description |
|------|-------------|
| `gmail_check_setup` | Check configuration status |
| `gmail_init_config` | Create configuration file |
| `gmail_test_connection` | Test database and OAuth |
| `gmail_run_migrations` | Run database migrations |
| `gmail_get_auth_url` | Generate OAuth URL |
| `gmail_handle_oauth_callback` | Process OAuth callback |
| `gmail_list_connections` | List Gmail connections |
| `gmail_check_connection` | Check connection health |
| `gmail_disconnect` | Disconnect Gmail account |
| `gmail_search` | Search emails |
| `gmail_get_message` | Get single message |
| `gmail_get_thread` | Get conversation thread |
| `gmail_get_attachment` | Download attachment |
| `gmail_send` | Send email |
| `gmail_create_draft` | Create draft |
| `gmail_send_draft` | Send existing draft |
| `gmail_modify_labels` | Add/remove labels |
| `gmail_archive` | Archive message |
| `gmail_trash` | Move to trash |

### Resources (8 total)

| Resource URI | Description |
|--------------|-------------|
| `config://status` | Configuration status |
| `config://schema` | Full configuration schema |
| `users://list` | List all users |
| `users://{user_id}/connections` | User's connections |
| `gmail://{connection_id}/labels` | Gmail labels |
| `gmail://{connection_id}/profile` | Gmail profile |
| `docs://setup` | Setup guide |
| `docs://google-oauth` | OAuth setup guide |
| `docs://troubleshooting` | Troubleshooting guide |

### Prompts (5 total)

| Prompt | Description |
|--------|-------------|
| `setup_gmail` | Complete setup wizard |
| `connect_test_account` | Connect Gmail for testing |
| `diagnose_connection` | Debug failing connection |
| `generate_oauth_ui` | Generate OAuth UI components |
| `build_email_agent` | Scaffold email-capable agent |

---

## Example Conversations

### Setup Workflow

```
User: Help me set up Gmail integration

Claude: I'll help you set up Gmail. Let me check the current status.
[Calls gmail_check_setup()]

The system isn't configured yet. I see you need:
- Google OAuth credentials
- An encryption key

Would you like me to:
1. Create a new configuration file
2. Guide you through getting Google OAuth credentials

User: Create the config file

Claude: [Calls gmail_init_config(database_type="sqlite")]
Created gmail_config.yaml with a generated encryption key.

Next, you'll need to set up Google OAuth credentials...
```

### Reading Emails

```
User: Show me my unread emails

Claude: [Calls gmail_list_connections()]
I found 1 connection: personal@gmail.com

[Calls gmail_search(connection_id="conn_123", query="is:unread", max_results=10)]

You have 5 unread emails:
1. "Meeting Tomorrow" from john@company.com
2. "Invoice #1234" from billing@service.com
...
```

### Sending Email

```
User: Send an email to alice@example.com about the project update

Claude: I'll compose that email for you.

[Calls gmail_send(
    connection_id="conn_123",
    to=["alice@example.com"],
    subject="Project Update",
    body="Hi Alice,\n\nHere's the project update..."
)]

Email sent successfully! Message ID: 18abc123def
```

### Creating Drafts (Safer)

```
User: Draft a reply to the email from Bob

Claude: Let me get the email from Bob first.
[Calls gmail_search(connection_id="conn_123", query="from:bob")]
[Calls gmail_get_message(connection_id="conn_123", message_id="msg_456")]

Here's Bob's email:
Subject: Q4 Planning
Body: "Can you send me the quarterly numbers?"

I'll create a draft reply:
[Calls gmail_create_draft(
    connection_id="conn_123",
    to=["bob@company.com"],
    subject="Re: Q4 Planning",
    body="Hi Bob,\n\nHere are the Q4 numbers...",
    reply_to_message_id="msg_456"
)]

Draft created (draft_id: draft_789). Would you like me to:
1. Send it now
2. Let you review it in Gmail first
```

---

## HTTP Transport Mode

For web-based MCP clients, use HTTP transport:

```bash
gmail-mcp serve --transport http --host 0.0.0.0 --port 8000
```

Configure your client to connect to `http://localhost:8000`.

---

## Custom MCP Clients

### Python Client Example

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="gmail-mcp",
        args=["serve"],
        env={"GMAIL_MCP_CONFIG": "./gmail_config.yaml"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            # Call a tool
            result = await session.call_tool("gmail_check_setup", {})
            print("Setup status:", result)

            # Read a resource
            resource = await session.read_resource("config://status")
            print("Config:", resource)

asyncio.run(main())
```

### JavaScript/TypeScript Client

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "gmail-mcp",
  args: ["serve"],
  env: { GMAIL_MCP_CONFIG: "./gmail_config.yaml" }
});

const client = new Client(
  { name: "my-client", version: "1.0.0" },
  { capabilities: {} }
);

await client.connect(transport);

// List tools
const tools = await client.listTools();
console.log("Tools:", tools.tools.map(t => t.name));

// Call tool
const result = await client.callTool({
  name: "gmail_search",
  arguments: {
    connection_id: "conn_123",
    query: "is:unread",
    max_results: 5
  }
});
console.log("Search result:", result);
```

---

## Best Practices

### 1. Use Drafts for Safety

Have the AI create drafts instead of sending directly:

```
User: Reply to all customer emails

Claude: I'll create drafts for each reply so you can review them first.
[Creates drafts instead of sending]
```

### 2. Confirm Before Actions

For sensitive actions, confirm with the user:

```
Claude: I'm about to send this email to 50 recipients.
Should I proceed, or would you like to review the list first?
```

### 3. Handle Errors Gracefully

```
Claude: [Calls gmail_search(...)]

I couldn't search your emails. Let me check why.
[Calls gmail_check_connection(connection_id="conn_123")]

Your Gmail token has expired. Would you like me to help you reconnect?
```

### 4. Provide Context

When showing emails, include relevant context:

```
Claude: Found 3 unread emails in your inbox:

1. **Meeting Tomorrow** (from: john@company.com, 2 hours ago)
   "Hi, let's meet at 2pm tomorrow to discuss..."
   [Labels: INBOX, UNREAD, IMPORTANT]

2. ...
```

---

## Troubleshooting

### "Server not found"

Check that:
1. `gmail-mcp` is installed: `pip show gmail-multi-user-mcp`
2. Command is in PATH: `which gmail-mcp`
3. Config path is correct

### "Config not found"

Set the config path explicitly:
```json
{
  "env": {
    "GMAIL_MCP_CONFIG": "/absolute/path/to/gmail_config.yaml"
  }
}
```

### "Connection refused"

For HTTP transport, check:
1. Server is running: `gmail-mcp serve --transport http`
2. Port is correct
3. Host is accessible

### "Tools not showing"

1. Restart Claude Desktop after config changes
2. Check Claude Desktop's MCP logs
3. Verify server starts: `gmail-mcp serve` (should not error)
