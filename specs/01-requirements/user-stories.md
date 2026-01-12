# User Stories

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [Developer Stories - Setup](#1-developer-stories---setup)
2. [Developer Stories - Library Usage](#2-developer-stories---library-usage)
3. [Developer Stories - MCP Usage](#3-developer-stories---mcp-usage)
4. [End-User Stories](#4-end-user-stories)
5. [Error & Recovery Stories](#5-error--recovery-stories)
6. [User Journey Maps](#6-user-journey-maps)

---

## 1. Developer Stories - Setup

### US-SETUP-001: First-Time Setup
**As a** developer new to gmail-multi-user-mcp
**I want to** set up the library in under 30 minutes
**So that** I can start integrating Gmail into my application

**Acceptance Criteria:**
- [ ] pip install works without errors
- [ ] Config file template is available
- [ ] Setup guide walks through Google Cloud setup
- [ ] First connection established in < 30 minutes

---

### US-SETUP-002: Google Cloud Configuration
**As a** developer
**I want to** clear documentation for Google Cloud OAuth setup
**So that** I don't waste time on configuration mistakes

**Acceptance Criteria:**
- [ ] Step-by-step guide with screenshots
- [ ] Common errors listed with solutions
- [ ] Correct scopes explained
- [ ] Redirect URI configuration explained

---

### US-SETUP-003: Local Development Setup
**As a** developer
**I want to** use SQLite for local development
**So that** I can develop without external dependencies

**Acceptance Criteria:**
- [ ] SQLite works without additional setup
- [ ] Tokens stored in local file
- [ ] Easy to reset/clear for testing
- [ ] Works offline (except Gmail API calls)

---

### US-SETUP-004: Production Setup
**As a** developer deploying to production
**I want to** use Supabase for storage
**So that** my tokens persist across deployments

**Acceptance Criteria:**
- [ ] Supabase connection via environment variables
- [ ] Migration script creates required tables
- [ ] Connection pooling for high throughput
- [ ] Clear documentation for Supabase setup

---

### US-SETUP-005: Environment Variable Configuration
**As a** developer using CI/CD
**I want to** configure entirely via environment variables
**So that** I don't need config files in my deployment

**Acceptance Criteria:**
- [ ] All settings available as env vars
- [ ] Env vars override config file values
- [ ] Clear mapping documentation
- [ ] Works with GitHub Secrets, Vercel env, etc.

---

## 2. Developer Stories - Library Usage

### US-LIB-001: Connect User's Gmail
**As a** developer
**I want to** generate an OAuth URL for my user
**So that** they can connect their Gmail account

**Acceptance Criteria:**
- [ ] Single function call to get OAuth URL
- [ ] State parameter generated automatically
- [ ] Custom scopes supported
- [ ] URL valid for 10 minutes

```python
# Example usage
auth = client.get_auth_url(user_id="user_123")
redirect(auth.auth_url)
```

---

### US-LIB-002: Handle OAuth Callback
**As a** developer
**I want to** process the OAuth callback
**So that** user tokens are stored automatically

**Acceptance Criteria:**
- [ ] Single function call with code and state
- [ ] Tokens encrypted and stored
- [ ] Connection ID returned
- [ ] Error handling for invalid/expired state

```python
# Example usage
result = client.handle_oauth_callback(code=request.query.code, state=request.query.state)
if result.success:
    print(f"Connected: {result.gmail_address}")
```

---

### US-LIB-003: Search User's Emails
**As a** developer
**I want to** search emails using Gmail query syntax
**So that** I can find specific emails for my user

**Acceptance Criteria:**
- [ ] Gmail search syntax supported
- [ ] Pagination supported
- [ ] Option to include/exclude body
- [ ] Returns message metadata

```python
# Example usage
messages = client.search(
    connection_id="conn_123",
    query="from:boss@company.com is:unread"
)
```

---

### US-LIB-004: Read Email Content
**As a** developer
**I want to** get full email content
**So that** I can process or display it

**Acceptance Criteria:**
- [ ] Plain text body extracted
- [ ] HTML body available if present
- [ ] Attachments listed with metadata
- [ ] Headers accessible

---

### US-LIB-005: Send Email
**As a** developer
**I want to** send emails from user's account
**So that** my application can communicate on their behalf

**Acceptance Criteria:**
- [ ] Plain text and HTML support
- [ ] Multiple recipients (to, cc, bcc)
- [ ] Reply threading supported
- [ ] Attachments supported

```python
# Example usage
result = client.send(
    connection_id="conn_123",
    to=["recipient@example.com"],
    subject="Hello",
    body="Message content"
)
```

---

### US-LIB-006: Create and Send Draft
**As a** developer
**I want to** create drafts for user review
**So that** users can approve before sending

**Acceptance Criteria:**
- [ ] Draft created in user's Gmail
- [ ] Draft can be updated
- [ ] Draft can be sent programmatically
- [ ] Draft visible in Gmail web UI

---

### US-LIB-007: Manage Labels
**As a** developer
**I want to** add/remove labels from messages
**So that** I can organize user's inbox

**Acceptance Criteria:**
- [ ] Add system labels (STARRED, IMPORTANT)
- [ ] Remove from INBOX (archive)
- [ ] Move to TRASH
- [ ] User labels supported

---

### US-LIB-008: Multi-Account Support
**As a** developer
**I want to** support users with multiple Gmail accounts
**So that** they can connect both personal and work email

**Acceptance Criteria:**
- [ ] Same user_id can have multiple connections
- [ ] Each connection has unique connection_id
- [ ] List all connections for a user
- [ ] Operate on specific connection_id

```python
# Example usage
connections = client.list_connections(user_id="user_123")
# Returns: [conn_personal, conn_work]
```

---

### US-LIB-009: Connection Health Check
**As a** developer
**I want to** check if a connection is still valid
**So that** I can prompt re-authentication if needed

**Acceptance Criteria:**
- [ ] Returns validity status
- [ ] Indicates if re-auth needed
- [ ] Shows token expiration time
- [ ] Includes available scopes

---

### US-LIB-010: Async Support
**As a** developer building async applications
**I want to** use async/await with the library
**So that** I don't block my event loop

**Acceptance Criteria:**
- [ ] AsyncGmailClient available
- [ ] All methods are async
- [ ] Works with asyncio
- [ ] Compatible with FastAPI, etc.

```python
# Example usage
async def handler():
    client = AsyncGmailClient()
    messages = await client.search(connection_id="conn_123", query="is:unread")
```

---

## 3. Developer Stories - MCP Usage

### US-MCP-001: Claude Code Integration
**As a** developer using Claude Code
**I want to** access Gmail via natural language
**So that** I can prototype quickly

**Acceptance Criteria:**
- [ ] MCP server starts with single command
- [ ] Works with Claude Code settings
- [ ] All Gmail operations available as tools
- [ ] Resources provide configuration status

---

### US-MCP-002: Setup via Claude
**As a** developer using Claude Code
**I want to** be guided through setup by Claude
**So that** I don't need to read documentation

**Acceptance Criteria:**
- [ ] `setup-gmail` prompt available
- [ ] Creates config file
- [ ] Guides through Google OAuth setup
- [ ] Tests connection at end

---

### US-MCP-003: Connect Test Account
**As a** developer using Claude Code
**I want to** connect my own Gmail for testing
**So that** I can try operations immediately

**Acceptance Criteria:**
- [ ] Local HTTP server catches OAuth callback
- [ ] Browser opens automatically
- [ ] Connection created without manual steps
- [ ] Test search verifies connection

---

### US-MCP-004: Generate UI Components
**As a** developer building a web app
**I want to** generate OAuth UI components
**So that** I don't have to write boilerplate

**Acceptance Criteria:**
- [ ] React/Next.js/Vue templates
- [ ] Tailwind/shadcn styling options
- [ ] Complete connect flow
- [ ] TypeScript types included

---

### US-MCP-005: Build Email Agent
**As a** developer building an AI agent
**I want to** scaffold a complete email agent
**So that** I have a working starting point

**Acceptance Criteria:**
- [ ] LangChain/CrewAI/Vercel AI support
- [ ] Tool definitions generated
- [ ] Example prompts included
- [ ] Test scenarios provided

---

## 4. End-User Stories

### US-USER-001: Connect Gmail
**As an** end-user of a developer's app
**I want to** connect my Gmail account securely
**So that** the app can access my emails

**Acceptance Criteria:**
- [ ] "Connect Gmail" button visible
- [ ] Standard Google consent screen
- [ ] Clear explanation of permissions
- [ ] Success confirmation after connection

---

### US-USER-002: Multiple Accounts
**As an** end-user with multiple Gmail accounts
**I want to** connect both personal and work email
**So that** I can use the app for all my accounts

**Acceptance Criteria:**
- [ ] Can add multiple connections
- [ ] Each account clearly identified
- [ ] Can choose which account to use
- [ ] Can remove individual accounts

---

### US-USER-003: Disconnect Gmail
**As an** end-user
**I want to** disconnect my Gmail account
**So that** I can revoke access when needed

**Acceptance Criteria:**
- [ ] Clear disconnect option
- [ ] Confirmation before disconnecting
- [ ] Access revoked at Google
- [ ] Data deleted from app

---

### US-USER-004: Transparent Token Refresh
**As an** end-user
**I want** my connection to stay active
**So that** I don't need to reconnect frequently

**Acceptance Criteria:**
- [ ] Automatic token refresh
- [ ] No user action required
- [ ] Connection stays valid for months
- [ ] Only re-auth if Google revokes

---

## 5. Error & Recovery Stories

### US-ERR-001: Expired Token Recovery
**As a** developer
**I want** automatic recovery from expired tokens
**So that** my application doesn't fail silently

**Acceptance Criteria:**
- [ ] Automatic refresh attempted
- [ ] Clear error if refresh fails
- [ ] needs_reauth flag set
- [ ] User can be prompted to reconnect

---

### US-ERR-002: Revoked Access Handling
**As a** developer
**I want** clear notification when access is revoked
**So that** I can prompt user to reconnect

**Acceptance Criteria:**
- [ ] Error code: token_revoked
- [ ] Connection marked inactive
- [ ] Clear message: "User revoked access"
- [ ] Resolution: reconnect

---

### US-ERR-003: Rate Limit Handling
**As a** developer
**I want** proper rate limit handling
**So that** my application doesn't break under load

**Acceptance Criteria:**
- [ ] 429 error includes Retry-After
- [ ] Automatic backoff on retries
- [ ] Clear error message
- [ ] Quota usage visible

---

### US-ERR-004: Invalid Configuration
**As a** developer
**I want** clear error messages for config issues
**So that** I can fix problems quickly

**Acceptance Criteria:**
- [ ] Missing config: show required fields
- [ ] Invalid values: show valid options
- [ ] File not found: show search paths
- [ ] Google credentials invalid: specific message

---

### US-ERR-005: Connection Not Found
**As a** developer
**I want** helpful errors when connection_id is invalid
**So that** I can debug issues

**Acceptance Criteria:**
- [ ] Error: connection_not_found
- [ ] Suggest listing connections
- [ ] Check user_id association
- [ ] Clear resolution steps

---

## 6. User Journey Maps

### Journey 1: Developer First-Time Setup (30 minutes)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Developer First-Time Setup                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Install         Create Config      Google Cloud        Test Connection         │
│  ────────        ─────────────      ────────────        ───────────────         │
│                                                                                  │
│  pip install     Copy template      Create project      Run test                │
│  gmail-multi-    Edit with          Enable Gmail API    script                  │
│  user-mcp        credentials        Configure OAuth                             │
│                                     consent screen                               │
│  [2 min]         [5 min]           [15-20 min]          [3 min]                 │
│                                                                                  │
│  Emotion:        Emotion:          Emotion:             Emotion:                │
│  Excited         Focused           Frustrated (lots     Relieved                │
│                                    of Google UI)        (it works!)             │
│                                                                                  │
│  Touchpoints:    Touchpoints:      Touchpoints:         Touchpoints:            │
│  - PyPI          - README          - Google Cloud       - Python REPL           │
│  - pip           - Example file    - Our guide          - Library API           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Journey 2: End-User Connecting Gmail

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         End-User Gmail Connection                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  See Button      Click Connect      Google Consent      Success                 │
│  ──────────      ─────────────      ──────────────      ───────                 │
│                                                                                  │
│  User sees       Redirected to      User logs in        Returned to app         │
│  "Connect        Google             Reviews scopes      with confirmation       │
│  Gmail" in       accounts.google    Clicks "Allow"                              │
│  the app                                                                        │
│                                                                                  │
│  [instant]       [2 sec]           [10-30 sec]          [1 sec]                 │
│                                                                                  │
│  Emotion:        Emotion:          Emotion:             Emotion:                │
│  Curious         Cautious          Evaluating trust     Satisfied               │
│                  (leaving app)     (what permissions?)                          │
│                                                                                  │
│  Trust factors:                                                                 │
│  - Recognizes Google UI (not phishing)                                          │
│  - Sees app name they're using                                                  │
│  - Clear scope descriptions                                                     │
│  - Can revoke anytime                                                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Journey 3: Claude Code Prototyping

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Claude Code Prototyping                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  "Help me        Claude runs       Developer           Natural language         │
│  set up Gmail"   setup-gmail       completes           Gmail ops                │
│  ────────────    ───────────       Google OAuth        ──────────────           │
│                                    ────────────                                 │
│                                                                                  │
│  Developer       Claude:           Opens browser       "Search my inbox"        │
│  asks Claude     - Creates config  Completes OAuth     "Draft reply to Bob"     │
│  for help        - Explains setup  Returns to Claude   "Send it"                │
│                  - Tests config                                                  │
│                                                                                  │
│  [instant]       [5 min]           [1 min]             [ongoing]                │
│                                                                                  │
│  Emotion:        Emotion:          Emotion:            Emotion:                 │
│  Hopeful         Impressed         Brief context       Delighted                │
│                  (Claude knows)    switch              (magic!)                 │
│                                                                                  │
│  Key experience:                                                                │
│  - No documentation reading                                                     │
│  - Claude handles config                                                        │
│  - Immediate productivity                                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Journey 4: Production Deployment

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Production Deployment                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Set up          Configure         Set Env Vars        Deploy                   │
│  Supabase        Google for        ────────────        ──────                   │
│  ─────────       production                                                     │
│                  ───────────                                                    │
│                                                                                  │
│  Create project  Add production    Add to deployment   docker-compose up        │
│  Run migrations  redirect URI      platform secrets    or K8s apply             │
│                  Verify app                                                     │
│                                                                                  │
│  [10 min]        [5 min]           [5 min]             [5 min]                  │
│                                                                                  │
│  Touchpoints:                                                                   │
│  - Supabase dashboard                                                           │
│  - Google Cloud Console                                                         │
│  - Deployment platform (Vercel, Railway, K8s)                                   │
│  - Docker                                                                       │
│                                                                                  │
│  Success criteria:                                                              │
│  - Health check passes                                                          │
│  - OAuth flow works with production redirect                                    │
│  - Tokens persist across deployments                                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```
