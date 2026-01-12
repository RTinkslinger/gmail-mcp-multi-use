"""Build email agent MCP prompt."""

from __future__ import annotations

from gmail_mcp_server.server import mcp


@mcp.prompt
def build_email_agent(
    framework: str = "custom",
    use_case: str = "email assistant",
) -> str:
    """Scaffold an email-capable AI agent.

    Args:
        framework: Target framework ("langchain", "crewai", "vercel-ai", or "custom").
        use_case: Description of the agent's purpose.

    Guides through:
    1. Verifying Gmail setup
    2. Recommending tools for use case
    3. Generating agent code
    4. Creating test scenarios
    5. Documenting usage

    Returns instructions for the AI assistant to follow.
    """
    return f"""# Build Email-Capable AI Agent

You are helping the user build an AI agent with Gmail capabilities.

**Framework**: {framework}
**Use Case**: {use_case}

## Step 1: Verify Gmail Setup

First, ensure Gmail integration is ready:

```
gmail_check_setup()
```

If not ready, suggest running `setup-gmail` prompt first.

## Step 2: Understand the Use Case

Based on the use case "{use_case}", identify:
- What email operations are needed?
- What's the agent's primary workflow?
- What human oversight is needed?

### Common Email Agent Use Cases

1. **Email Assistant**: Summarize inbox, draft replies, organize emails
2. **Customer Support**: Auto-respond, categorize tickets, escalate issues
3. **Sales Outreach**: Send personalized emails, track responses
4. **Newsletter Manager**: Send bulk emails, manage subscriptions
5. **Meeting Scheduler**: Coordinate via email, send calendar invites

## Step 3: Recommend Tools

Based on the use case, recommend which Gmail tools to use:

### Read Operations
- `gmail_search` - Find specific emails (use Gmail query syntax)
- `gmail_get_message` - Get full message content
- `gmail_get_thread` - Get entire conversation
- `gmail_get_attachment` - Download attachments

### Write Operations
- `gmail_send` - Send new emails
- `gmail_create_draft` - Create drafts for human review
- `gmail_send_draft` - Send approved drafts

### Management Operations
- `gmail_modify_labels` - Organize with labels
- `gmail_archive` - Archive processed emails
- `gmail_trash` - Delete spam/unwanted

## Step 4: Generate Agent Code

{"### LangChain Agent" if framework == "langchain" else ""}
{"Generate a LangChain agent with Gmail tools:" if framework == "langchain" else ""}

{"### CrewAI Agent" if framework == "crewai" else ""}
{"Generate a CrewAI crew with Gmail-enabled agents:" if framework == "crewai" else ""}

{"### Vercel AI SDK Agent" if framework == "vercel-ai" else ""}
{"Generate a Vercel AI SDK agent with Gmail tools:" if framework == "vercel-ai" else ""}

{"### Custom Agent" if framework == "custom" else ""}
{"Generate a custom Python agent using the Gmail tools directly:" if framework == "custom" else ""}

The agent should:
1. Initialize with a connection_id for the Gmail account
2. Have clear tool descriptions for the LLM to understand
3. Include error handling for API failures
4. Log actions for debugging

## Step 5: Safety and Human Oversight

**Critical**: Email agents can have real-world consequences. Include:

1. **Draft Mode**: Create drafts instead of sending directly
   - Use `gmail_create_draft` instead of `gmail_send`
   - Human reviews and approves before sending

2. **Confirmation Prompts**: Ask before destructive actions
   - "Are you sure you want to send this to X?"
   - "This will archive Y messages. Confirm?"

3. **Rate Limiting**: Prevent spam/abuse
   - Limit sends per hour
   - Detect unusual patterns

4. **Audit Logging**: Track all actions
   - Log what was sent, to whom, when
   - Store for compliance/debugging

## Step 6: Test Scenarios

Create test scenarios for the use case:

### Scenario 1: Happy Path
- Input: [describe typical input]
- Expected: [describe expected behavior]
- Verify: [how to verify it worked]

### Scenario 2: Error Handling
- Input: [describe error case]
- Expected: [how agent should handle]
- Verify: [how to verify graceful handling]

### Scenario 3: Edge Cases
- Input: [describe edge case]
- Expected: [describe expected behavior]
- Verify: [how to verify correct handling]

## Step 7: Document Usage

Generate documentation including:
1. How to configure the agent
2. Required environment variables
3. Example usage
4. Troubleshooting common issues
5. Security considerations

## Framework-Specific Code Templates

Ask what specific code the user needs:
- Complete agent implementation
- Just the Gmail tool definitions
- Example usage script
- Integration with existing agent

Then generate the appropriate code with best practices for {framework}.
"""
