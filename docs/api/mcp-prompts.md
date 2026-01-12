# MCP Prompts Reference

This document provides a complete reference for all 5 MCP prompts provided by the Gmail Multi-User MCP Server.

Prompts are pre-defined instructions that guide AI assistants through complex multi-step workflows.

## Overview

| Prompt | Description | Use Case |
|--------|-------------|----------|
| `setup_gmail` | Complete setup wizard | First-time configuration |
| `connect_test_account` | Connect Gmail for testing | Developer onboarding |
| `diagnose_connection` | Debug failing connection | Troubleshooting |
| `generate_oauth_ui` | Generate OAuth UI components | Frontend development |
| `build_email_agent` | Scaffold email-capable agent | AI agent development |

---

## setup_gmail

Complete setup wizard for gmail-multi-user-mcp.

### Description

Guides through the full setup process:
1. Checking current setup status
2. Creating configuration if needed
3. Setting up Google OAuth
4. Running migrations
5. Testing configuration
6. Connecting a test account

### Arguments

None.

### Example Usage

```
User: Help me set up Gmail integration

AI: I'll use the setup_gmail prompt to guide you through the process.

[AI follows the prompt's step-by-step instructions]
```

### Workflow

1. **Check Status**: Calls `gmail_check_setup()` to see what's configured
2. **Create Config**: If needed, asks about storage backend and OAuth credentials
3. **Run Migrations**: For Supabase, guides through SQL migration
4. **Test**: Verifies database and OAuth with `gmail_test_connection()`
5. **Connect**: Offers to help connect a test Gmail account

---

## connect_test_account

Connect developer's Gmail account for testing.

### Description

Guides through connecting a Gmail account:
1. Verifying setup is complete
2. Generating OAuth URL
3. Guiding through authorization
4. Verifying connection works
5. Testing with a search

### Arguments

None.

### Example Usage

```
User: I want to connect my Gmail account to test this

AI: I'll help you connect your Gmail account for testing.

[AI follows the prompt to guide through OAuth flow]
```

### Workflow

1. **Verify Setup**: Checks system is ready with `gmail_check_setup()`
2. **Generate URL**: Creates OAuth URL with `gmail_get_auth_url(user_id="test_user")`
3. **Guide Auth**: Tells user to click link, sign in, authorize
4. **Handle Callback**: Processes code with `gmail_handle_oauth_callback()`
5. **Verify**: Tests with `gmail_check_connection()` and `gmail_search()`

### Expected Output

At the end, provides:
- Connection ID for future use
- Gmail address connected
- Confirmation that the connection works

---

## diagnose_connection

Debug a failing Gmail connection.

### Description

Guides through debugging connection issues:
1. Listing connections if not specified
2. Checking connection status
3. Identifying the issue
4. Providing solution
5. Testing the fix

### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `connection_id` | `string \| null` | `null` | Connection ID to diagnose |

### Example Usage

```
User: My Gmail connection isn't working

AI: I'll help diagnose the issue.

[AI follows prompt to identify and fix the problem]
```

### Common Issues Diagnosed

| Issue | Cause | Solution |
|-------|-------|----------|
| `needs_reauth: true` | Token expired/revoked | Re-authorize with new OAuth URL |
| Connection not found | Invalid ID or deleted | List connections, find correct ID |
| Connection inactive | Was disconnected | Re-authorize |
| Token validation failed | Network/API issue | Check config, retry |

### Workflow

1. **Identify**: Lists connections if needed with `gmail_list_connections()`
2. **Check Status**: Calls `gmail_check_connection(connection_id)`
3. **Diagnose**: Analyzes the status fields
4. **Fix**: Provides specific solution based on issue
5. **Verify**: Tests fix with `gmail_search()` query

---

## generate_oauth_ui

Generate OAuth UI components for web applications.

### Description

Guides through generating frontend components:
1. Connect Gmail button
2. OAuth callback handler
3. Connection status component
4. API routes (backend)
5. TypeScript types

### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `framework` | `string` | `"react"` | Target framework: "react", "vue", "nextjs", "html" |
| `style` | `string \| null` | `null` | Styling approach: "tailwind", "css", "shadcn" |

### Example Usage

```
User: Generate a Gmail connect button for my Next.js app with Tailwind

AI: I'll generate OAuth UI components for Next.js with Tailwind CSS.

[AI generates Connect button, callback handler, status component, API routes]
```

### Components Generated

**1. Connect Gmail Button**
```jsx
// Initiates OAuth flow
// Shows loading state
// Handles errors
```

**2. OAuth Callback Handler**
```jsx
// Extracts code and state from URL
// Sends to backend
// Shows success/error
// Redirects after
```

**3. Connection Status Component**
```jsx
// Lists connected accounts
// Shows connection health
// Disconnect button
```

**4. API Routes**
```typescript
GET /api/gmail/auth-url     // Returns OAuth URL
POST /api/gmail/callback    // Handles callback
GET /api/gmail/connections  // Lists connections
DELETE /api/gmail/connections/:id  // Disconnects
```

**5. TypeScript Types**
```typescript
interface Connection { ... }
interface AuthUrlResponse { ... }
interface CallbackResponse { ... }
```

### Framework Guidelines

**React**: Hooks, react-router, fetch/axios
**Vue**: Composition API, vue-router, $fetch/axios
**Next.js**: App Router, Server Actions, next/navigation
**HTML**: Vanilla JS, Fetch API, redirects

---

## build_email_agent

Scaffold an email-capable AI agent.

### Description

Guides through building an AI agent with Gmail capabilities:
1. Verifying Gmail setup
2. Recommending tools for use case
3. Generating agent code
4. Creating test scenarios
5. Documenting usage

### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `framework` | `string` | `"custom"` | Agent framework: "langchain", "crewai", "vercel-ai", "custom" |
| `use_case` | `string` | `"email assistant"` | Description of the agent's purpose |

### Example Usage

```
User: Build me a customer support agent that can read and respond to emails

AI: I'll help you build a customer support email agent.

[AI generates agent code with appropriate tools and safety measures]
```

### Common Use Cases

| Use Case | Description | Key Tools |
|----------|-------------|-----------|
| Email Assistant | Summarize, draft replies, organize | search, get_message, create_draft |
| Customer Support | Auto-respond, categorize, escalate | search, send, modify_labels |
| Sales Outreach | Send personalized emails, track | send, search, get_thread |
| Newsletter Manager | Send bulk, manage subscriptions | send, modify_labels |
| Meeting Scheduler | Coordinate via email | search, send, get_thread |

### Tool Recommendations

**Read Operations:**
- `gmail_search` - Find emails matching criteria
- `gmail_get_message` - Get full message content
- `gmail_get_thread` - Get conversation context
- `gmail_get_attachment` - Process attachments

**Write Operations:**
- `gmail_send` - Send new emails
- `gmail_create_draft` - Create for human review
- `gmail_send_draft` - Send approved drafts

**Management:**
- `gmail_modify_labels` - Categorize/organize
- `gmail_archive` - Archive processed
- `gmail_trash` - Delete unwanted

### Safety Measures

The prompt emphasizes:

**1. Draft Mode**
```python
# Instead of direct sending
result = gmail_send(...)

# Create draft for human review
draft = gmail_create_draft(...)
# Human approves, then:
result = gmail_send_draft(draft_id=draft.draft_id)
```

**2. Confirmation Prompts**
```
AI: I'm about to send this email to john@example.com:
Subject: Meeting Follow-up
...
Do you want me to proceed?
```

**3. Rate Limiting**
```python
# Limit sends per hour
# Detect unusual patterns
```

**4. Audit Logging**
```python
# Log all actions
log.info("email_sent", to=recipient, subject=subject)
```

### Generated Code Structure

**LangChain:**
```python
from langchain.agents import Agent
from langchain.tools import Tool

gmail_tools = [
    Tool(name="gmail_search", func=gmail_search, description="..."),
    Tool(name="gmail_send", func=gmail_send, description="..."),
]

agent = Agent(tools=gmail_tools, ...)
```

**CrewAI:**
```python
from crewai import Agent, Task, Crew

email_agent = Agent(
    role="Email Assistant",
    goal="Help manage emails",
    tools=[gmail_search, gmail_send, ...],
)
```

**Custom:**
```python
class EmailAgent:
    def __init__(self, connection_id: str):
        self.connection_id = connection_id

    async def process_inbox(self):
        messages = await gmail_search(
            connection_id=self.connection_id,
            query="is:unread"
        )
        # Process messages...
```

---

## Using Prompts

Prompts are invoked through the MCP prompt protocol. In Claude Desktop, they appear as available prompts that can be triggered.

### Triggering a Prompt

```
User: Use the setup_gmail prompt
AI: [Begins following setup_gmail workflow]

User: Help me diagnose my Gmail connection
AI: [Uses diagnose_connection prompt]
```

### Best Practices

1. **Let prompts guide**: Don't skip steps in the workflow
2. **Provide context**: Give the AI any error messages or specific issues
3. **Follow up**: After completing a prompt, verify the outcome
4. **Customize**: Arguments let you tailor prompts to your needs
