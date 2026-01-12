# gmail-multi-user-mcp

Multi-user Gmail integration library and MCP server for AI agents and consumer applications.

## Features

- **Hybrid Distribution**: Use as a Python library or MCP server
- **Multi-User OAuth**: End-users authenticate with their own Gmail accounts
- **Automatic Token Management**: Encryption, refresh, and storage handled automatically
- **Full Gmail Operations**: Search, read, send, draft, labels, attachments
- **Flexible Storage**: SQLite for development, Supabase for production

## Quick Start

### Installation

```bash
pip install gmail-multi-user-mcp
```

### Configuration

1. Create a Google Cloud Project and enable the Gmail API
2. Create OAuth 2.0 credentials (Desktop or Web application)
3. Copy `gmail_config.yaml.example` to `gmail_config.yaml`
4. Fill in your credentials

### Usage as Library

```python
from gmail_multi_user import GmailClient

# Initialize client (loads config automatically)
client = GmailClient()

# Generate OAuth URL for a user
result = client.get_auth_url(user_id="user_123")
print(f"Please visit: {result.auth_url}")

# After OAuth callback, search emails
messages = client.search(
    connection_id="conn_abc",
    query="is:unread"
)

for msg in messages.messages:
    print(f"{msg.subject} from {msg.from_.email}")
```

### Usage as MCP Server

```bash
# Start the MCP server
gmail-mcp serve

# Or with HTTP transport
gmail-mcp serve --transport http --port 8000
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black --check .
mypy gmail_multi_user gmail_mcp_server
```

## License

MIT
