"""Generate OAuth UI MCP prompt."""

from __future__ import annotations

from gmail_mcp_server.server import mcp


@mcp.prompt
def generate_oauth_ui(
    framework: str = "react",
    style: str | None = None,
) -> str:
    """Generate OAuth UI components.

    Args:
        framework: Target framework ("react", "vue", "nextjs", or "html").
        style: Optional styling approach ("tailwind", "css", or "shadcn").

    Guides through generating:
    1. Connect button component
    2. Callback handler
    3. Status component
    4. API routes (for nextjs)
    5. TypeScript types

    Returns instructions for the AI assistant to follow.
    """
    return f"""# Generate OAuth UI Components

You are helping the user generate OAuth UI components for their application.

**Framework**: {framework}
**Styling**: {style or "default CSS"}

## Components to Generate

Generate the following components for {framework}:

### 1. Connect Gmail Button

A button that initiates the OAuth flow:
- Calls your backend to get an auth URL
- Redirects the user to Google
- Shows loading state while redirecting
- Handles errors gracefully

### 2. OAuth Callback Handler

A page/component that handles the OAuth callback:
- Extracts `code` and `state` from URL parameters
- Sends to backend to complete OAuth flow
- Shows success/error state
- Redirects to appropriate page after

### 3. Connection Status Component

Shows the current connection status:
- List of connected Gmail accounts
- Last sync time
- Connection health indicator
- Disconnect button

### 4. API Routes (for backend)

Generate server-side routes that:
- `GET /api/gmail/auth-url` - Returns OAuth URL
- `POST /api/gmail/callback` - Handles OAuth callback
- `GET /api/gmail/connections` - Lists user's connections
- `DELETE /api/gmail/connections/:id` - Disconnects account

These routes should call the MCP tools:
- `gmail_get_auth_url(user_id="...")`
- `gmail_handle_oauth_callback(code="...", state_param="...")`
- `gmail_list_connections(user_id="...")`
- `gmail_disconnect(connection_id="...")`

### 5. TypeScript Types

Generate TypeScript interfaces:
- `Connection` - Gmail connection object
- `AuthUrlResponse` - Response from auth URL endpoint
- `CallbackResponse` - Response from callback endpoint

## Framework-Specific Guidelines

{"### React" if framework == "react" else ""}
{"- Use hooks for state management (useState, useEffect)" if framework == "react" else ""}
{"- Use react-router for routing" if framework == "react" else ""}
{"- Fetch API or axios for HTTP requests" if framework == "react" else ""}

{"### Vue" if framework == "vue" else ""}
{"- Use Composition API with <script setup>" if framework == "vue" else ""}
{"- Use vue-router for routing" if framework == "vue" else ""}
{"- Use $fetch or axios for HTTP requests" if framework == "vue" else ""}

{"### Next.js" if framework == "nextjs" else ""}
{"- Use App Router (app/ directory)" if framework == "nextjs" else ""}
{"- Server Actions or Route Handlers for API" if framework == "nextjs" else ""}
{"- Use next/navigation for routing" if framework == "nextjs" else ""}

{"### HTML" if framework == "html" else ""}
{"- Vanilla JavaScript" if framework == "html" else ""}
{"- Fetch API for HTTP requests" if framework == "html" else ""}
{"- Simple redirect-based flow" if framework == "html" else ""}

## Styling Guidelines

{"### Tailwind CSS" if style == "tailwind" else ""}
{"- Use Tailwind utility classes" if style == "tailwind" else ""}
{"- Responsive design with breakpoints" if style == "tailwind" else ""}

{"### shadcn/ui" if style == "shadcn" else ""}
{"- Use shadcn/ui components (Button, Card, etc.)" if style == "shadcn" else ""}
{"- Consistent with shadcn design system" if style == "shadcn" else ""}

{"### CSS" if style == "css" or not style else ""}
{"- Clean, minimal CSS" if style == "css" or not style else ""}
{"- CSS modules or styled-components" if style == "css" or not style else ""}

## Security Considerations

Include these security measures:
1. CSRF protection using the `state` parameter
2. Secure storage of tokens (backend only, never client-side)
3. HTTPS in production
4. Error handling that doesn't leak sensitive info

## Generate the Code

Now generate the components. Ask clarifying questions if needed:
- What's the backend URL?
- What authentication system do they use for their app?
- Do they need multi-account support?
"""
