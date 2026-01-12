# gmail-multi-user-mcp: PRD Development Journey

## Summary

This document captures the complete journey of developing a Product Requirements Document (PRD) for `gmail-multi-user-mcp` — an open-source Python library and MCP server that abstracts Gmail OAuth complexity for developers building AI agents and consumer applications.

**Starting Point:** A simple question — "Can I setup an MCP server for my Gmail inbox?"

**Ending Point:** A comprehensive PRD for an open-source, hybrid library/MCP package with:
- Dual distribution (use as library OR MCP server)
- Flexible storage backends (Supabase for production, SQLite for development)
- Layered configuration system (environment variables → local file → home directory)
- 20+ Gmail operations (search, read, send, draft, labels, etc.)
- MIT license, 8-week implementation plan

**Key Pivot:** The project evolved from a hosted SaaS model to a fully open-source, self-hosted solution where developers bring their own credentials — driven by the goal of zero infrastructure cost and maximum developer flexibility.

**Total Iterations:** 10 major iterations across the conversation

---

## Table of Contents

1. [Iteration 1: Initial Question & Personal Setup](#iteration-1-initial-question--personal-setup)
2. [Iteration 2: Pivoting to Multi-User Architecture](#iteration-2-pivoting-to-multi-user-architecture)
3. [Iteration 3: PRD Development Process](#iteration-3-prd-development-process)
4. [Iteration 4: First PRD Draft (Hosted SaaS Model)](#iteration-4-first-prd-draft-hosted-saas-model)
5. [Iteration 5: Addressing Open Questions](#iteration-5-addressing-open-questions)
6. [Iteration 6: Pivot to Open-Source Model](#iteration-6-pivot-to-open-source-model)
7. [Iteration 7: Hybrid Library/MCP Architecture](#iteration-7-hybrid-librarymcp-architecture)
8. [Iteration 8: Configuration System Deep Dive](#iteration-8-configuration-system-deep-dive)
9. [Iteration 9: Local vs Remote MCP Clarification](#iteration-9-local-vs-remote-mcp-clarification)
10. [Iteration 10: MCP Architecture Design](#iteration-10-mcp-architecture-design)
11. [Final PRD Summary](#final-prd-summary)

---

## Iteration 1: Initial Question & Personal Setup

### User Input
> "Can I setup an MCP server for my Gmail inbox?"

### Claude's Response
Provided options for personal Gmail MCP setup:
- Google's official MCP server (`@anthropic-ai/google-mcp`)
- Community-built alternatives
- Step-by-step setup for Claude Desktop with OAuth credentials

### Key Outcome
User clarified they wanted to use **Claude Code**, not Claude Desktop, leading to more specific setup instructions.

---

## Iteration 2: Pivoting to Multi-User Architecture

### User Input
> "I want this MCP to be built in such a way that any application I build, other users should be able to connect their own Gmail. So this needs to be built for that. Think hard and figure out what the most simple and elegant approach to do that."

### Claude's Analysis
Identified the fundamental difference between:
- **Personal use:** Desktop OAuth, local token storage
- **Multi-user:** Web OAuth flow, per-user token storage, tenant isolation

### Proposed Architecture
```
Developer's App → Backend (OAuth + MCP) → Gmail API
                       ↓
                 Token Storage (per user)
```

### Recommended Stack
- **Option A:** Build custom OAuth + token management
- **Option B:** Use auth provider (Supabase) for OAuth handling

### User Decision
> "Using Supabase makes sense and would go with that."

---

## Iteration 3: PRD Development Process

### User Input
> "Think hard and first draft a PRD document. The steps to follow to get a robust PRD are as follows:
> - Understanding: What needs to be achieved thoroughly? What problem?
> - Exploring: See where Claude fails without guidance
> - Research: Go deep on the domain
> - Synthesis: Extract principles from research
> - Drafting: Write initial draft
> - Self critique: Review against quality criteria
> - Iterating: Fix gaps, get feedback, improve
> - Testing: Play out various scenarios to check we have covered the handling perfectly
> - Finalizing: Codify the optimal PRD"

### Claude's Process

**Phase 1 — Understanding:**
Identified the core problem: 2-4 weeks of OAuth/Gmail work before developers can send their first email.

**Phase 2 — Exploring:**
Listed common failure points:
- OAuth confusion (Desktop vs Web credentials)
- Token management (refresh token handling)
- Multi-tenancy (mixing up user tokens)
- Gmail API quirks (MIME, threading, labels)

**Phase 3 — Research:**
Conducted web searches on:
- Gmail API OAuth multi-tenant best practices
- Supabase Google OAuth provider token storage
- Existing Gmail MCP server implementations
- Supabase multi-tenant architecture patterns
- MCP server OAuth authentication patterns

**Phase 4 — Synthesis:**
Extracted key principles:
- Use RLS with `tenant_id` in `app_metadata`
- Must pass `access_type: 'offline'` and `prompt: 'consent'` for refresh tokens
- MCP should act as resource server with external auth provider
- Encrypt tokens at rest, use short-lived access tokens

---

## Iteration 4: First PRD Draft (Hosted SaaS Model)

### Initial PRD Structure
1. Executive Summary
2. Target Users
3. Architecture (Multi-tenant with Supabase)
4. Functional Requirements (20+ MCP tools)
5. Non-Functional Requirements (Security, Reliability, Scalability)
6. UI Requirements (Developer Dashboard)
7. API Design
8. Error Handling
9. Implementation Phases (10 weeks)
10. Success Metrics
11. Risks and Mitigations
12. Open Questions

### Self-Critique Gaps Identified
1. Missing: How does developer's app identify end-users?
2. Missing: Token refresh background job architecture
3. Missing: Webhooks for connection status changes
4. Missing: Rate limit specifics
5. Missing: Message format details (HTML vs plain text)
6. Missing: Testing strategy

### Additions Made
- User identity mapping section
- Token lifecycle management with proactive refresh
- Connection status webhooks
- Rate limiting tiers
- Message format handling (reading and sending)
- Sandbox/testing mode

---

## Iteration 5: Addressing Open Questions

### Open Questions Presented
1. **Pricing Model:** Usage-based? Per-seat? Flat tier?
2. **Self-Hosted Option:** Open-source version?
3. **Other Email Providers:** Outlook/Microsoft 365?
4. **Webhook Support:** Real-time notifications?
5. **Google Workspace:** Service accounts?

### Claude's Analysis for Each

**Pricing:**
| Model | Simplicity | Completeness |
|-------|------------|--------------|
| Free forever | ★★★★★ | ★☆☆☆☆ |
| Flat tier | ★★★★☆ | ★★☆☆☆ |
| Per-seat | ★★★☆☆ | ★★★☆☆ |
| Usage-based | ★★☆☆☆ | ★★★★★ |

**Self-Hosted:**
Recommended starting hosted-only, source-available later if demanded.

**Other Providers:**
Gmail first, but design abstraction layer for future Outlook support.

**Webhooks:**
Start with polling, push as premium feature later.

**Google Workspace:**
Out of scope for v1 — different trust model.

### User Decisions
> "Regarding question 1,2: we want to give this as open source fully. I shouldn't be incurring any costs either. Developers who'd use the product would bring their own credentials for Supabase etc."
>
> "Regarding question 3: keep it Gmail only"
>
> "Regarding question 4: let's keep it simple polling based"
>
> "Regarding question 5: we can skip workspace in v1"

---

## Iteration 6: Pivot to Open-Source Model

### Major Architecture Changes

| Aspect | Before (Hosted SaaS) | After (Open-Source) |
|--------|----------------------|---------------------|
| Multi-tenancy | We manage tenants | Single-tenant per deployment |
| Token Storage | Our Supabase | Developer's Supabase |
| API Keys | We issue | Not needed |
| Pricing | We charge | Free (developer pays infra) |
| OAuth Credentials | Shared or BYOC | Always BYOC |
| Dashboard | We build/host | CLI + Supabase dashboard |

### Simplifications
- Removed `tenants` table
- Removed API key authentication
- Removed tenant-scoped RLS
- Removed usage tracking/billing
- Removed hosted dashboard

### New Focus
- Comprehensive documentation
- Easy setup guides
- Reference implementation
- CLI tools for management

---

## Iteration 7: Hybrid Library/MCP Architecture

### User Input
> "Before proceeding need to re-validate our overall approach in depth. Should this be an MCP server way of distribution or simply just a code repo which they can add to their code? In which cases does this make sense as an MCP and in which cases does it make sense as just a library/repo?"

### Claude's Analysis

**When MCP Makes Sense:**
- AI agents interacting with Gmail conversationally
- Claude Desktop/Code users wanting Gmail as a "tool"
- Multi-step reasoning about emails

**When Library Makes Sense:**
- Traditional application development
- Backend services, cron jobs
- When developer wants full programmatic control

### Recommendation: Build Both (Library-First)

```
gmail-multi-user-mcp/
├── gmail_multi_user/        # Core library (the real value)
│   ├── client.py
│   ├── oauth.py
│   └── ...
│
└── gmail_mcp_server/        # MCP wrapper (~200 lines)
    └── server.py            # Imports from gmail_multi_user
```

### Benefits
- Same config file for both usage modes
- MCP server is thin wrapper over library
- Developers can prototype with MCP, productionize with library

### User Decision
> "Hybrid approach seems ideal."

---

## Iteration 8: Configuration System Deep Dive

### User Input
> "Config file location, I'm not equipped to answer, give me a detailed view of what does each option entail, what are the implications of where a config file is, why and how should this be decided, what are the best practices used by engineering teams for this, what would an expert top notch developer in my shoes do."

### Claude's Analysis

**Three Strategies Compared:**

| Strategy | Pros | Cons | Best For |
|----------|------|------|----------|
| Project-local (`./gmail_config.yaml`) | Travels with project, easy to find | Risk of committing secrets | Project-specific configs |
| User home (`~/.config/gmail-mcp/`) | Secrets never in project | Doesn't travel with project | Personal dev tools |
| Environment variables | Most flexible, 12-factor compliant | Verbose for local dev | Production deployments |

**Expert Approach: Layered Configuration**

```
1. Environment variables     ← Always wins (production)
       ↓
2. File from GMAIL_MCP_CONFIG env var
       ↓
3. Project-local files       ← Development convenience
       ↓
4. User home directory       ← Personal defaults
       ↓
5. Error with clear message
```

**Who Uses This Pattern:**
- AWS CLI (`~/.aws/credentials` + env vars)
- Docker Compose (multiple file locations + env)
- Git (`~/.gitconfig` + project `.git/config`)

### Additional Decision: SQLite Support
> "Outside of Supabase I'd only want to solve for SQLite for local dev."

### Final Decisions
- **License:** MIT
- **MCP Transports:** Both stdio and HTTP
- **Package Name:** `gmail-multi-user-mcp`
- **Storage:** Supabase (production) + SQLite (local dev)
- **Config:** Layered approach

---

## Iteration 9: Local vs Remote MCP Clarification

### User Input
> "Would it be fair to say that we are actually building a local MCP server for developers since for most use cases developer's production agent is usually a library import. What scenarios would there be where for developer's production agent our service would be an MCP? Give me a detailed example."

### Claude's Analysis

**Key Realization:** The MCP server mode is primarily for prototyping with Claude Code/Desktop. Production applications typically import the library directly.

**When Remote MCP is Actually Needed:**

| Scenario | Remote MCP Needed? | Why |
|----------|-------------------|-----|
| Claude Code/Desktop | ❌ Local MCP (stdio) | Runs on developer's machine |
| Python agent | ❌ Library import | Same language, direct import |
| TypeScript/Go/Rust agent | ✅ **Yes** | Can't import Python library |
| Microservice architecture | ⚠️ Maybe | Depends on scale/complexity |

### Detailed Example Provided

A complete TypeScript + Next.js + Vercel AI SDK example showing:
- Docker Compose with MCP server as sidecar
- TypeScript MCP client wrapper
- Integration with Vercel AI SDK tools
- Internal service authentication

### PRD Updates Made

Added Section 1.6 "Deployment Modes & Primary Use Cases" with:

1. **Primary (Dev):** Local MCP server for Claude Code/Desktop prototyping
2. **Primary (Prod):** Library import for Python applications  
3. **Secondary (Prod):** Remote MCP server for non-Python applications

Plus a decision matrix and architecture diagram showing the library-first approach.

---

## Iteration 10: MCP Architecture Design

### User Input
> "Now I want you to think of the MCP architecture, and break this down into what tools, resources and prompt templates would be provided to the host (assume Claude Code) that the developer would be using. Remember we want to build the most seamless experience for our developer."

### Claude's Analysis

Designed the complete MCP interface from the developer's perspective, considering the full journey:
1. **Setup** — Getting Gmail integration configured
2. **Test** — Connecting developer's own Gmail
3. **Build** — Creating OAuth flow for end-users
4. **Integrate** — Adding Gmail to agents/apps
5. **Debug** — Fixing issues when things break

### MCP Primitives Designed

**Tools (18 total):**

| Category | Tools | Purpose |
|----------|-------|---------|
| Setup & Config (4) | `check_setup`, `init_config`, `test_connection`, `run_migrations` | Help developers get started |
| OAuth & Users (5) | `get_auth_url`, `handle_callback`, `list_connections`, `check_connection`, `disconnect` | Manage OAuth flows and connections |
| Gmail Operations (9) | `search`, `get_message`, `get_thread`, `send`, `create_draft`, `send_draft`, `modify_labels`, `archive`, `trash`, `get_attachment` | Core email functionality |

**Resources (8 total):**

| Resource URI | Purpose |
|--------------|---------|
| `config://status` | Current configuration health |
| `config://schema` | Config file template |
| `users://list` | All users with connections |
| `users://{id}/connections` | Connections for a user |
| `gmail://{conn}/labels` | Available labels |
| `gmail://{conn}/profile` | Quota and profile info |
| `docs://setup` | Setup guide |
| `docs://google-oauth` | Google Cloud setup guide |
| `docs://troubleshooting` | Common issues and fixes |

**Prompts (5 total):**

| Prompt | Purpose |
|--------|---------|
| `setup-gmail` | Complete setup wizard |
| `connect-test-account` | Connect developer's Gmail for testing |
| `diagnose-connection` | Debug failing connections |
| `generate-oauth-ui` | Create OAuth UI for React/Next.js/Vue |
| `build-email-agent` | Scaffold an email-capable agent |

### Developer Experience Flow

Mapped out the seamless experience across Day 1 (setup), Day 2 (building), and Day 3 (production):

```
Day 1: "I want to add Gmail" 
       → check_setup → init_config → Google OAuth guide → test_connection
       → get_auth_url → connect developer's account → search emails

Day 2: "Add to my Next.js app"
       → generate-oauth-ui prompt → complete UI components + API routes

Day 3: "Build an email agent"
       → build-email-agent prompt → LangChain/Vercel AI agent scaffold
```

### PRD Updates Made

Added Section 15 "MCP Architecture: Tools, Resources, and Prompts" with:
- Complete architecture overview diagram
- Detailed specifications for all 18 tools
- URI templates for all 8 resources
- Workflow definitions for all 5 prompts
- Developer experience flow examples

Renamed PRD file to `gmail-multi-user-dev-mcp-prd.md`

---

## Final PRD Summary

### Package: `gmail-multi-user-mcp`

### Distribution Model
```
┌─────────────────────────────────────────────────────────────────┐
│                     gmail-multi-user-mcp                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Core Library                              ││
│  │  gmail_multi_user/                                          ││
│  │  ├── client.py      (GmailClient - main interface)          ││
│  │  ├── oauth.py       (OAuth flow management)                 ││
│  │  ├── tokens.py      (Token storage & refresh)               ││
│  │  └── config.py      (Configuration loading)                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                  │
│  ┌─────────────────────┐       ┌─────────────────────────────┐ │
│  │   Use as Library    │       │    Use as MCP Server        │ │
│  │   (import & call)   │       │    (gmail-mcp serve)        │ │
│  └─────────────────────┘       └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features
- **Hybrid usage:** Library for programmatic control, MCP for AI agents
- **Flexible storage:** Supabase (production) or SQLite (development)
- **Layered config:** Environment → local file → home directory
- **Dual MCP transport:** stdio (Claude Desktop) and HTTP (remote)
- **Comprehensive Gmail ops:** 20+ operations (search, read, send, draft, labels)
- **Automatic token refresh:** Transparent to developers
- **MIT licensed:** Maximum adoption, no restrictions

### Implementation Timeline
| Phase | Week | Focus |
|-------|------|-------|
| 1 | 1 | Project foundation, config system, SQLite storage |
| 2 | 2 | OAuth flow, token management |
| 3 | 3 | Gmail API wrapper (read operations) |
| 4 | 4 | Gmail write operations |
| 5 | 5 | Supabase backend |
| 6 | 6 | MCP server layer |
| 7 | 7 | Documentation |
| 8 | 8 | Testing & release |

### Developer Experience

**As Library:**
```python
from gmail_multi_user import GmailClient

client = GmailClient()  # Auto-loads config
auth_url = client.get_auth_url(user_id="user_123")
messages = client.search(user_id="user_123", query="is:unread")
```

**As MCP Server:**
```bash
gmail-mcp serve --transport stdio
```

**Config file:**
```yaml
database:
  type: sqlite  # or 'supabase'
  sqlite_path: ./tokens.db

google:
  client_id: xxx.apps.googleusercontent.com
  client_secret: GOCSPX-xxx
  redirect_uri: http://localhost:8000/oauth/callback

encryption:
  key: your-64-char-hex-key
```

---

## Lessons Learned

1. **Start with the user's actual goal** — The question "Can I setup an MCP?" led to understanding they wanted multi-user support for a consumer app.

2. **Research before designing** — Web searches revealed Supabase patterns, existing MCP implementations, and OAuth best practices that shaped the architecture.

3. **Validate assumptions early** — The pivot from hosted SaaS to open-source happened because we asked "what's your primary goal?"

4. **Hybrid approaches beat either/or** — Library + MCP serves more use cases than choosing one.

5. **Configuration is UX** — The layered config system required deep analysis but dramatically improves developer experience.

6. **Scenario testing validates completeness** — Walking through 7 real-world scenarios revealed gaps and confirmed coverage.

---

## Artifacts Produced

1. **gmail-multi-user-dev-mcp-prd.md** — Complete PRD (v2.2) with all specifications including MCP architecture
2. **gmail-mcp-prd-with-claude-chat.md** — This document (development journey)

---

*Document created: January 12, 2026*
*Starting question to final PRD: ~2 hours of conversation*
