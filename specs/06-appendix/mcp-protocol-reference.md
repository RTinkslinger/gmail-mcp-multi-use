# MCP Protocol Reference

This appendix provides technical reference information for the Model Context Protocol (MCP) as implemented by `gmail-multi-user-mcp`.

---

## MCP Overview

The Model Context Protocol (MCP) is a standard protocol for AI assistants to interact with external tools and data sources. It defines three main primitives:

1. **Tools** - Functions the AI can invoke
2. **Resources** - Data sources the AI can read
3. **Prompts** - Pre-defined prompt templates

---

## Protocol Structure

### JSON-RPC 2.0

MCP uses JSON-RPC 2.0 for communication.

**Request Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "gmail_search",
    "arguments": {
      "connection_id": "conn_123",
      "query": "is:unread"
    }
  }
}
```

**Response Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 5 messages..."
      }
    ]
  }
}
```

**Error Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "details": "connection_id is required"
    }
  }
}
```

### Standard Error Codes

| Code | Meaning |
|------|---------|
| -32700 | Parse error |
| -32600 | Invalid request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |

---

## Transport Layers

### stdio Transport

Default transport for Claude Desktop integration.

```
Client (Claude) ←→ stdin/stdout ←→ MCP Server
```

**Configuration:**
```json
{
  "mcpServers": {
    "gmail": {
      "command": "gmail-mcp",
      "args": ["serve"],
      "env": {
        "GMAIL_MCP_CONFIG": "/path/to/config.yaml"
      }
    }
  }
}
```

### HTTP Transport

For remote/hosted MCP servers.

```
Client ←→ HTTP POST /mcp ←→ MCP Server
```

**Server Startup:**
```bash
gmail-mcp serve --transport http --host 0.0.0.0 --port 8080
```

**Request:**
```http
POST /mcp HTTP/1.1
Host: localhost:8080
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
```

### SSE Transport

Server-Sent Events for streaming responses.

```
Client ←→ SSE Stream ←→ MCP Server
```

---

## MCP Methods

### Initialization

**initialize:**
```json
{
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {}
    },
    "clientInfo": {
      "name": "Claude Desktop",
      "version": "1.0.0"
    }
  }
}
```

**Response:**
```json
{
  "protocolVersion": "2024-11-05",
  "capabilities": {
    "tools": {},
    "resources": {},
    "prompts": {}
  },
  "serverInfo": {
    "name": "gmail-multi-user-mcp",
    "version": "1.0.0"
  }
}
```

### Tools

**tools/list:**
```json
{
  "method": "tools/list"
}
```

**Response:**
```json
{
  "tools": [
    {
      "name": "gmail_search",
      "description": "Search Gmail messages using Gmail query syntax",
      "inputSchema": {
        "type": "object",
        "properties": {
          "connection_id": {
            "type": "string",
            "description": "The Gmail connection ID"
          },
          "query": {
            "type": "string",
            "description": "Gmail search query"
          },
          "max_results": {
            "type": "integer",
            "default": 20
          }
        },
        "required": ["connection_id", "query"]
      }
    }
  ]
}
```

**tools/call:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "gmail_search",
    "arguments": {
      "connection_id": "conn_123",
      "query": "is:unread"
    }
  }
}
```

**Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Found 3 messages:\n\n1. From: sender@example.com\n   Subject: Meeting tomorrow..."
    }
  ]
}
```

### Resources

**resources/list:**
```json
{
  "method": "resources/list"
}
```

**Response:**
```json
{
  "resources": [
    {
      "uri": "gmail://conn_123/labels",
      "name": "Gmail Labels",
      "description": "List of labels for this Gmail connection",
      "mimeType": "application/json"
    }
  ]
}
```

**resources/read:**
```json
{
  "method": "resources/read",
  "params": {
    "uri": "gmail://conn_123/labels"
  }
}
```

**Response:**
```json
{
  "contents": [
    {
      "uri": "gmail://conn_123/labels",
      "mimeType": "application/json",
      "text": "[{\"id\": \"INBOX\", \"name\": \"INBOX\"}, ...]"
    }
  ]
}
```

### Prompts

**prompts/list:**
```json
{
  "method": "prompts/list"
}
```

**Response:**
```json
{
  "prompts": [
    {
      "name": "setup-gmail",
      "description": "Guide through Gmail OAuth setup",
      "arguments": [
        {
          "name": "user_id",
          "description": "External user identifier",
          "required": true
        }
      ]
    }
  ]
}
```

**prompts/get:**
```json
{
  "method": "prompts/get",
  "params": {
    "name": "setup-gmail",
    "arguments": {
      "user_id": "user_123"
    }
  }
}
```

**Response:**
```json
{
  "description": "Gmail OAuth setup workflow",
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "I want to set up Gmail access for user_123"
      }
    },
    {
      "role": "assistant",
      "content": {
        "type": "text",
        "text": "I'll help you set up Gmail access. First, let me check the current configuration..."
      }
    }
  ]
}
```

---

## FastMCP Implementation

### Server Setup

```python
from fastmcp import FastMCP

mcp = FastMCP("gmail-multi-user-mcp")

@mcp.tool()
async def gmail_search(
    connection_id: str,
    query: str,
    max_results: int = 20
) -> str:
    """Search Gmail messages using Gmail query syntax.

    Args:
        connection_id: The Gmail connection ID
        query: Gmail search query (e.g., "is:unread", "from:sender@example.com")
        max_results: Maximum number of results (default: 20)

    Returns:
        Formatted list of matching messages
    """
    client = get_gmail_client()
    results = await client.search(connection_id, query, max_results)
    return format_search_results(results)
```

### Resource Definition

```python
@mcp.resource("gmail://{connection_id}/labels")
async def get_gmail_labels(connection_id: str) -> str:
    """Get Gmail labels for a connection.

    Args:
        connection_id: The Gmail connection ID

    Returns:
        JSON array of labels
    """
    client = get_gmail_client()
    labels = await client.list_labels(connection_id)
    return json.dumps([label.model_dump() for label in labels])
```

### Prompt Definition

```python
@mcp.prompt()
async def setup_gmail(user_id: str) -> list[dict]:
    """Generate a prompt for Gmail OAuth setup.

    Args:
        user_id: External user identifier

    Returns:
        List of messages for the setup workflow
    """
    return [
        {
            "role": "user",
            "content": f"I want to set up Gmail access for user {user_id}"
        },
        {
            "role": "assistant",
            "content": """I'll help you set up Gmail access. Here's what we need to do:

1. First, let me check if the server is properly configured
2. Generate an OAuth authorization URL
3. Have you complete the authorization
4. Verify the connection is working

Let me start by checking the setup..."""
        }
    ]
```

### Running the Server

```python
# gmail_mcp_server/__main__.py
import asyncio
from .server import mcp

if __name__ == "__main__":
    asyncio.run(mcp.run())
```

**CLI:**
```bash
# stdio transport (default)
gmail-mcp serve

# HTTP transport
gmail-mcp serve --transport http --port 8080

# With debug logging
gmail-mcp serve --debug
```

---

## Tool Schema Reference

### JSON Schema for Tool Inputs

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "connection_id": {
      "type": "string",
      "description": "UUID of the Gmail connection"
    },
    "query": {
      "type": "string",
      "description": "Gmail search query syntax"
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 500,
      "default": 20
    },
    "page_token": {
      "type": "string",
      "description": "Token for pagination"
    }
  },
  "required": ["connection_id", "query"],
  "additionalProperties": false
}
```

### Content Types

MCP supports multiple content types in responses:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Plain text content"
    },
    {
      "type": "image",
      "data": "base64-encoded-image-data",
      "mimeType": "image/png"
    },
    {
      "type": "resource",
      "resource": {
        "uri": "gmail://conn_123/message/msg_456",
        "text": "Message content...",
        "mimeType": "text/plain"
      }
    }
  ]
}
```

---

## Resource URI Templates

### URI Format

```
{scheme}://{identifier}/{path}
```

### Gmail Resources

| URI Pattern | Description |
|-------------|-------------|
| `config://status` | Server configuration status |
| `config://schema` | Configuration JSON schema |
| `users://list` | List all users |
| `users://{user_id}/connections` | User's Gmail connections |
| `gmail://{connection_id}/labels` | Gmail labels |
| `gmail://{connection_id}/profile` | Gmail profile |
| `docs://setup` | Setup documentation |
| `docs://google-oauth` | OAuth documentation |
| `docs://troubleshooting` | Troubleshooting guide |

### Resource Templates

Resources can use URI templates with parameters:

```python
@mcp.resource("users://{user_id}/connections")
async def get_user_connections(user_id: str) -> str:
    """Get connections for a specific user."""
    pass
```

---

## Error Handling

### Tool Errors

When a tool fails, return an error in the content:

```python
@mcp.tool()
async def gmail_search(connection_id: str, query: str) -> str:
    try:
        results = await client.search(connection_id, query)
        return format_results(results)
    except ConnectionNotFoundError:
        return f"Error: Connection '{connection_id}' not found. Use gmail_list_connections to see available connections."
    except AuthenticationError:
        return f"Error: Connection '{connection_id}' requires re-authentication. Use gmail_get_auth_url to start the OAuth flow."
```

### Structured Error Responses

For programmatic error handling:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: Connection not found"
    }
  ],
  "isError": true
}
```

---

## Claude Desktop Configuration

### Configuration File Location

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/claude/claude_desktop_config.json`

### Full Configuration Example

```json
{
  "mcpServers": {
    "gmail": {
      "command": "gmail-mcp",
      "args": ["serve"],
      "env": {
        "GMAIL_MCP_CONFIG": "/Users/name/.gmail_mcp/config.yaml",
        "GMAIL_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Using Docker

```json
{
  "mcpServers": {
    "gmail": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/Users/name/.gmail_mcp:/config:ro",
        "-e", "GMAIL_MCP_CONFIG=/config/config.yaml",
        "ghcr.io/yourorg/gmail-multi-user-mcp:latest",
        "serve"
      ]
    }
  }
}
```

### Using UV/Uvx

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uvx",
      "args": ["gmail-multi-user-mcp", "serve"],
      "env": {
        "GMAIL_MCP_CONFIG": "/path/to/config.yaml"
      }
    }
  }
}
```

---

## Testing MCP Servers

### MCP Inspector

Use the official MCP Inspector tool:

```bash
npx @modelcontextprotocol/inspector gmail-mcp serve
```

This opens a web UI to:
- List and test tools
- List and read resources
- List and get prompts
- View raw JSON-RPC messages

### Manual Testing with JSON-RPC

```bash
# List tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | gmail-mcp serve

# Call a tool
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"gmail_check_setup","arguments":{}}}' | gmail-mcp serve
```

### Python Test Client

```python
import subprocess
import json

def call_mcp_method(method: str, params: dict = None):
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }

    proc = subprocess.run(
        ["gmail-mcp", "serve"],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )

    return json.loads(proc.stdout)

# Test tools/list
result = call_mcp_method("tools/list")
print(f"Available tools: {len(result['result']['tools'])}")

# Test a tool
result = call_mcp_method("tools/call", {
    "name": "gmail_check_setup",
    "arguments": {}
})
print(f"Setup status: {result['result']['content'][0]['text']}")
```

---

## Protocol Version Compatibility

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 2024-11-05 | Nov 2024 | Initial stable release |

### Version Negotiation

During initialization, client and server negotiate the protocol version:

```json
// Client sends
{
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05"
  }
}

// Server responds with supported version
{
  "protocolVersion": "2024-11-05"
}
```

If versions are incompatible, the server returns an error.
