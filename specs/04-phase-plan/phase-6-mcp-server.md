# Phase 6: MCP Server Layer

**Duration:** Week 6
**Dependencies:** Phase 5 (Supabase)

---

## Objectives

1. Create MCP server wrapper around library
2. Implement all 18 MCP tools
3. Add 8 MCP resources
4. Create 5 MCP prompts
5. Build CLI commands

---

## Deliverables

- [ ] FastMCP server with all tools
- [ ] All resources functional
- [ ] All prompts defined
- [ ] CLI: `gmail-mcp serve`, `gmail-mcp health`
- [ ] Both stdio and HTTP transport
- [ ] Tests for MCP interface

---

## Task Breakdown

### 6.1 FastMCP Server Setup

```
□ Create gmail_mcp_server/server.py
  □ Initialize FastMCP("gmail-multi-user-mcp")
  □ Lazy client initialization
  □ Error handling wrapper
  □ Response formatting utilities
```

**Testing:**
- Server initializes
- Client lazily created
- Errors properly formatted

### 6.2 Setup & Config Tools

```
□ Create gmail_mcp_server/tools/setup.py
  □ gmail_check_setup tool
    □ Check config exists
    □ Check database connection
    □ Check Google OAuth configured
    □ Check encryption key
    □ Return status + issues
  □ gmail_init_config tool
    □ Generate config file
    □ Generate encryption key
    □ Return path + next steps
  □ gmail_test_connection tool
    □ Test database
    □ Test Google OAuth
    □ Return results
  □ gmail_run_migrations tool
    □ Run pending migrations
    □ Return results
```

**Testing:**
- Check reports correct status
- Init creates valid config
- Test connection works
- Migrations run correctly

### 6.3 OAuth & User Tools

```
□ Create gmail_mcp_server/tools/auth.py
  □ gmail_get_auth_url tool
    □ Generate OAuth URL
    □ Return URL, state, expires_in
  □ gmail_handle_oauth_callback tool
    □ Process callback
    □ Return result
  □ gmail_list_connections tool
    □ List connections
    □ Filter by user_id
  □ gmail_check_connection tool
    □ Check connection health
  □ gmail_disconnect tool
    □ Revoke and delete
```

**Testing:**
- All tools delegate to library
- Responses properly formatted

### 6.4 Gmail Read Tools

```
□ Create gmail_mcp_server/tools/read.py
  □ gmail_search tool
    □ Search with query
    □ Return messages
  □ gmail_get_message tool
    □ Get single message
  □ gmail_get_thread tool
    □ Get thread
  □ gmail_get_attachment tool
    □ Download attachment
```

**Testing:**
- Search returns formatted messages
- Message includes all fields
- Attachment base64 encoded

### 6.5 Gmail Write Tools

```
□ Create gmail_mcp_server/tools/write.py
  □ gmail_send tool
    □ Send email
  □ gmail_create_draft tool
    □ Create draft
  □ gmail_send_draft tool
    □ Send draft
```

**Testing:**
- Send returns message_id
- Draft CRUD works

### 6.6 Gmail Management Tools

```
□ Create gmail_mcp_server/tools/manage.py
  □ gmail_modify_labels tool
  □ gmail_archive tool
  □ gmail_trash tool
```

**Testing:**
- Label operations work
- Archive/trash work

### 6.7 MCP Resources

```
□ Create gmail_mcp_server/resources/config.py
  □ config://status resource
  □ config://schema resource
□ Create gmail_mcp_server/resources/users.py
  □ users://list resource
  □ users://{user_id}/connections resource
□ Create gmail_mcp_server/resources/gmail.py
  □ gmail://{connection_id}/labels resource
  □ gmail://{connection_id}/profile resource
□ Create gmail_mcp_server/resources/docs.py
  □ docs://setup resource
  □ docs://google-oauth resource
  □ docs://troubleshooting resource
```

**Testing:**
- Resources return valid data
- URI templates work
- Docs content embedded

### 6.8 MCP Prompts

```
□ Create gmail_mcp_server/prompts/setup.py
  □ setup-gmail prompt
□ Create gmail_mcp_server/prompts/connect.py
  □ connect-test-account prompt
□ Create gmail_mcp_server/prompts/diagnose.py
  □ diagnose-connection prompt
□ Create gmail_mcp_server/prompts/generate_ui.py
  □ generate-oauth-ui prompt
□ Create gmail_mcp_server/prompts/build_agent.py
  □ build-email-agent prompt
```

**Testing:**
- Prompts return workflow instructions

### 6.9 CLI Commands

```
□ Create gmail_mcp_server/cli.py
  □ Typer app
  □ serve command
    □ --transport [stdio|http]
    □ --host, --port options
    □ --config option
    □ --debug flag
  □ health command
    □ Check configuration
    □ Test connections
  □ connections subcommand
    □ list
    □ revoke
    □ test
  □ init command
    □ Create config interactively
  □ migrate command
    □ Run migrations
□ Create gmail_mcp_server/__main__.py
  □ Entry point for python -m
```

**Testing:**
- serve starts server
- health reports status
- connections commands work

### 6.10 Transport Configuration

```
□ Configure stdio transport (default for Claude)
□ Configure HTTP transport for remote
□ Add authentication for HTTP transport
□ Test both transports
```

**Testing:**
- stdio works with Claude Desktop
- HTTP works with auth token

### 6.11 Integration Tests

```
□ Create tests/integration/test_mcp_tools.py
  □ Test all 18 tools
□ Create tests/integration/test_mcp_resources.py
  □ Test all resources
□ Create tests/integration/test_cli.py
  □ Test CLI commands
```

---

## Definition of Done

- [ ] All tasks checked off
- [ ] 18 MCP tools functional
- [ ] 8 MCP resources functional
- [ ] 5 MCP prompts defined
- [ ] CLI fully functional
- [ ] Both transports work
- [ ] Tests pass with 90%+ coverage

---

## Risks

| Risk | Mitigation |
|------|------------|
| FastMCP API changes | Pin version, check docs |
| Transport compatibility | Test with Claude Desktop |
| Tool schema validation | Test with MCP inspector |
