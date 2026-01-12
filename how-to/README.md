# Gmail MCP - How-To Guides

Welcome! This folder contains step-by-step guides for setting up and using the Gmail MCP (Model Context Protocol) server.

## Which Guide Should I Read?

### I want to use this for my own email

| Scenario | Guide |
|----------|-------|
| I want to use Gmail with Claude Desktop | [Personal Setup with Claude Desktop](02-personal-claude-desktop.md) |
| I want to use Gmail in my own scripts/tools | [Personal Local Setup](01-personal-local-setup.md) |

### I'm building something for others

| Scenario | Guide |
|----------|-------|
| I'm building an AI agent that needs Gmail access | [Production Agent Setup](03-production-agent-setup.md) |
| I need to let multiple users connect their Gmail | [Multi-User Production Guide](03-production-agent-setup.md) |

### I need help with something specific

| Topic | Guide |
|-------|-------|
| Setting up Google OAuth credentials | [Google OAuth Setup](04-google-oauth-setup.md) |
| Something isn't working | [Troubleshooting Guide](05-troubleshooting.md) |
| Docker deployment | [Docker Guide](06-docker-deployment.md) |

## Quick Start (TL;DR)

**For personal use with Claude Desktop:**

```bash
# 1. Install the package
pip install gmail-multi-user-mcp

# 2. Initialize config
gmail-mcp init

# 3. Edit config with your Google OAuth credentials
# (see 04-google-oauth-setup.md for getting these)

# 4. Add to Claude Desktop config
# See 02-personal-claude-desktop.md
```

**For production agents:**

```bash
# 1. Install
pip install gmail-multi-user-mcp

# 2. Set environment variables
export GMAIL_MCP_ENCRYPTION_KEY="your-32-byte-key-base64"
export GMAIL_MCP_GOOGLE_CLIENT_ID="your-client-id"
export GMAIL_MCP_GOOGLE_CLIENT_SECRET="your-client-secret"
export GMAIL_MCP_STORAGE_TYPE="supabase"  # or "sqlite" for simple setups

# 3. Run server
gmail-mcp serve --transport http --port 8080
```

## Glossary

| Term | What it means |
|------|---------------|
| **MCP** | Model Context Protocol - a way for AI assistants to use tools |
| **OAuth** | The secure way to let apps access Gmail without sharing your password |
| **Connection** | A link between a user and their Gmail account |
| **Token** | A temporary "key" that lets the MCP access Gmail |
| **PKCE** | Extra security for OAuth (pronounced "pixie") |

## Need Help?

- Check the [Troubleshooting Guide](05-troubleshooting.md)
- Open an issue on GitHub
- Make sure you've completed the [Google OAuth Setup](04-google-oauth-setup.md)
