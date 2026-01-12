# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**gmail-multi-user-mcp** is a Python library and MCP (Model Context Protocol) server for multi-user Gmail OAuth integration. It abstracts Gmail OAuth complexity for developers building AI agents and consumer applications.

**Current State:** Specification phase - all design documents complete in `specs/`, no implementation code yet.

## Architecture

### Library-First Design
- Core value lives in `gmail_multi_user/` package (~95% of logic)
- MCP server (`gmail_mcp_server/`) is a thin wrapper (~200 lines) using FastMCP
- Both sync (`GmailClient`) and async (`AsyncGmailClient`) APIs - sync wraps async internally

### Key Components
```
gmail_multi_user/
├── client.py         # Public GmailClient, AsyncGmailClient
├── service.py        # GmailService orchestration layer
├── oauth/            # OAuth 2.0 with PKCE, local callback server
├── tokens/           # Encryption (Fernet) and refresh management
├── storage/          # Abstract backend: SQLiteBackend, SupabaseBackend
└── gmail/            # Gmail API wrapper, MIME parsing

gmail_mcp_server/
├── server.py         # FastMCP server setup
├── tools/            # 18 MCP tools
├── resources/        # 8 MCP resources
└── prompts/          # 5 MCP prompts
```

### Data Flow
1. User authenticates → OAuth flow with PKCE → tokens encrypted with Fernet
2. Operations flow: Client → Service → TokenManager (auto-refresh) → GmailAPIClient → Gmail API
3. Storage abstraction: SQLite for dev, Supabase for production

## Commands (Planned)

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest                              # All tests
pytest tests/unit                   # Unit tests only
pytest tests/integration            # Integration tests
pytest -k "test_oauth"              # Single test pattern
pytest --cov=gmail_multi_user       # With coverage

# Linting & formatting
ruff check .                        # Lint
ruff format .                       # Format
mypy gmail_multi_user gmail_mcp_server  # Type check

# Run MCP server
gmail-mcp serve                     # stdio transport (for Claude Desktop)
gmail-mcp serve --transport http    # HTTP transport
gmail-mcp health                    # Check configuration
```

## Spec Documents

The `specs/` folder contains complete design documentation:

| Path | Contents |
|------|----------|
| `specs/00-overview.md` | Executive summary, key decisions |
| `specs/01-requirements/` | Functional requirements (18 tools, 8 resources, 5 prompts), NFRs, user stories |
| `specs/02-architecture/` | System design, data model (schemas), API design, security architecture |
| `specs/03-implementation/` | Approach analysis, recommended approach, tech stack, repo structure |
| `specs/04-phase-plan/` | 8-week implementation plan with detailed task breakdowns |
| `specs/05-testing/` | Testing strategy, test cases catalog, CI/CD pipeline |
| `specs/06-appendix/` | Google OAuth reference, MCP protocol reference, glossary |

## Key Design Decisions

- **Python 3.10+** required (pattern matching, modern typing)
- **Storage backends:** SQLite (local dev), Supabase (production) via `StorageBackend` abstraction
- **Token security:** Fernet encryption (AES-128-CBC), 5-minute refresh buffer
- **OAuth flow:** Local HTTP server catches callback for CLI/MCP mode
- **Config priority:** Environment vars → `GMAIL_MCP_CONFIG` path → `./gmail_config.yaml` → `~/.gmail_mcp/config.yaml`

## Testing Approach

- Unit tests mock all external services (Gmail API, storage)
- Integration tests use real SQLite, mocked Gmail API
- E2E tests (CI only) use dedicated test Gmail account
- Target: 90%+ coverage, test matrix: Python 3.10, 3.11, 3.12

---

## Build Traces Protocol

Track implementation decisions with minimal context overhead using a rolling window + compaction pattern.

### Quick Reference

| File | Purpose | When to Read |
|------|---------|--------------|
| `TRACES.md` | Rolling window (~80 lines) | Every coding session |
| `traces/archive/milestone-N.md` | Full historical detail | Only when debugging or researching past decisions |

### What Counts as an Iteration

An iteration is a work session where you:
- Write or modify code files (not specs/docs)
- Complete tasks from the phase plan
- Make architectural or implementation decisions

NOT an iteration: Pure research, Q&A, planning, or documentation-only changes.

### After Each Coding Session

1. **Read `TRACES.md`** - find the last iteration number in "Current Work"
2. **Add iteration entry** to "Current Work" section (template below)
3. **If iteration 3, 6, 9...** → run compaction process (see below)

### Iteration Entry Template (Concise ~15 lines)

```markdown
### Iteration N - YYYY-MM-DD
**Phase:** Phase X: Name
**Focus:** Brief description

**Changes:** `file.py` (what), `other.py` (what)
**Decisions:** Key decision → rationale
**Next:** What's next

---
```

### Compaction Process (Every 3 Iterations)

When you complete iteration 3, 6, 9, 12..., perform these steps:

1. **Create archive file** `traces/archive/milestone-N.md`:
   ```markdown
   # Milestone N: [Focus Area]
   **Iterations:** X-Y | **Dates:** YYYY-MM-DD to YYYY-MM-DD

   ## Summary
   [2-3 sentences on what was accomplished]

   ## Key Decisions
   - Decision 1: Rationale
   - Decision 2: Rationale

   ## Iteration Details
   [Copy all 3 iteration entries from Current Work]
   ```

2. **Update Project Summary** in TRACES.md - add key decisions from this milestone

3. **Update Milestone Index** - add one row to the table

4. **Clear Current Work** - remove the 3 archived iterations, keep section header

### When to Read Archive Files

Only read `traces/archive/` if:
- User asks about historical decisions
- Debugging requires understanding why something was built a certain way
- You need context from a specific past milestone

**Do NOT read archive files during normal iteration updates.**
