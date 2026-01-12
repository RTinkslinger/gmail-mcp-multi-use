# gmail-multi-user-mcp: Specification Overview

**Version:** 1.0
**Date:** January 12, 2026
**Status:** Final Specification

---

## Executive Summary

**gmail-multi-user-mcp** is an open-source Python library and MCP (Model Context Protocol) server that abstracts the complexity of Gmail OAuth integration for developers building AI agents and consumer applications.

### The Problem

Developers building AI-powered applications need Gmail access for their end-users. Currently, this requires:

1. Setting up Google Cloud Project & OAuth consent screen
2. Implementing OAuth flows (authorization codes, PKCE, token exchange)
3. Managing per-user token storage (encrypted, refreshed automatically)
4. Learning Gmail API quirks (MIME parsing, threading, base64 encoding)
5. Handling rate limits and quotas

**This is 2-4 weeks of work before sending the first email programmatically.**

### The Solution

A single Python package providing:

| Feature | Description |
|---------|-------------|
| **Hybrid Distribution** | Use as library (`from gmail_multi_user import GmailClient`) OR as MCP server (`gmail-mcp serve`) |
| **Config-File Simplicity** | Add `gmail_config.yaml` to your project and you're ready |
| **Multi-User OAuth** | End-users authenticate with their Google account via pre-built flow |
| **Automatic Token Management** | Refresh tokens, encryption, and storage handled automatically |
| **Full Gmail Operations** | Search, read, send, draft, labels, attachments (18+ operations) |
| **Flexible Storage** | Supabase (production) or SQLite (local development) |
| **Zero Cost to Maintainers** | Developers bring their own credentials and infrastructure |

### Target Audience

1. **Primary:** Developers building AI agents and consumer apps with Gmail integration
2. **Secondary:** End-users of those applications (seamless OAuth experience)

---

## Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **API Style** | Both sync and async | Broader adoption: sync for scripts, async for production |
| **OAuth (CLI/MCP)** | Local HTTP server | Auto-catches callback, best UX for terminal users |
| **Token Refresh** | Background job + on-demand | Reliability: proactive refresh + fallback |
| **Sandbox Mode** | Full mock mode | CI/CD testing without Google credentials |
| **Docker** | Official image (ghcr.io) | Easy deployment with versioned tags |
| **Features** | All 18+ Gmail operations | Complete functionality in v1 |
| **Key Rotation** | Deferred to v2 | Simpler v1; document re-auth requirement |
| **E2E Testing** | Dedicated test account | Real Gmail in CI for release validation |
| **Telemetry** | GitHub metrics only | Privacy-first approach |
| **Python Version** | 3.10+ | Modern typing, FastMCP compatibility |
| **Demo** | Local docker-compose | No hosted infrastructure needed |

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        gmail-multi-user-mcp                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      Core Library (gmail_multi_user/)                  │ │
│  │                                                                         │ │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐   │ │
│  │   │  Config  │   │  OAuth   │   │  Gmail   │   │  Token Manager   │   │ │
│  │   │  Loader  │   │  Flow    │   │  API     │   │  (Encrypt/Refresh)│   │ │
│  │   └──────────┘   └──────────┘   └──────────┘   └──────────────────┘   │ │
│  │                                                                         │ │
│  │   ┌──────────────────────────────────────────────────────────────┐    │ │
│  │   │              Storage Backend (Abstract)                       │    │ │
│  │   │         SQLite (dev)    │    Supabase (prod)                 │    │ │
│  │   └──────────────────────────────────────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                 ┌───────────────────┴────────────────────┐                  │
│                 ▼                                        ▼                  │
│   ┌─────────────────────────┐           ┌─────────────────────────────────┐│
│   │   Library Import        │           │      MCP Server Wrapper         ││
│   │   (GmailClient)         │           │      (~200 lines)               ││
│   │                         │           │                                 ││
│   │   - Sync API            │           │   - 18 Tools                    ││
│   │   - Async API           │           │   - 8 Resources                 ││
│   │                         │           │   - 5 Prompts                   ││
│   └─────────────────────────┘           └─────────────────────────────────┘│
│                                                                              │
│        80% of production use               20% of production use            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Modes

| Mode | Use Case | Transport | Storage |
|------|----------|-----------|---------|
| **Local MCP** | Claude Code/Desktop prototyping | stdio | SQLite |
| **Library Import** | Python production apps | N/A | Supabase |
| **Remote MCP** | Non-Python apps (TS/Go/Rust) | HTTP | Supabase |

---

## Spec Document Index

### 01-requirements/
| Document | Contents |
|----------|----------|
| [functional-requirements.md](./01-requirements/functional-requirements.md) | All 18 MCP tools, 8 resources, 5 prompts, library API, CLI commands |
| [non-functional-requirements.md](./01-requirements/non-functional-requirements.md) | Security, performance, scalability, compliance |
| [user-stories.md](./01-requirements/user-stories.md) | Developer and end-user journey maps |

### 02-architecture/
| Document | Contents |
|----------|----------|
| [system-design.md](./02-architecture/system-design.md) | Component diagrams, data flow, deployment topology |
| [data-model.md](./02-architecture/data-model.md) | Database schemas, migrations, indexes |
| [api-design.md](./02-architecture/api-design.md) | Library API signatures, MCP tool schemas |
| [security-architecture.md](./02-architecture/security-architecture.md) | OAuth flow, encryption, threat model |

### 03-implementation/
| Document | Contents |
|----------|----------|
| [approach-analysis.md](./03-implementation/approach-analysis.md) | Three approaches with pros/cons matrix |
| [recommended-approach.md](./03-implementation/recommended-approach.md) | Library-first implementation guide |
| [technology-stack.md](./03-implementation/technology-stack.md) | Dependencies, versions, rationale |
| [repository-structure.md](./03-implementation/repository-structure.md) | Complete folder/file layout |

### 04-phase-plan/
| Document | Contents |
|----------|----------|
| [phase-1-foundation.md](./04-phase-plan/phase-1-foundation.md) | Project setup, config system, SQLite |
| [phase-2-oauth.md](./04-phase-plan/phase-2-oauth.md) | OAuth flow, PKCE, token exchange |
| [phase-3-gmail-read.md](./04-phase-plan/phase-3-gmail-read.md) | Gmail read operations |
| [phase-4-gmail-write.md](./04-phase-plan/phase-4-gmail-write.md) | Gmail write operations |
| [phase-5-supabase.md](./04-phase-plan/phase-5-supabase.md) | Supabase storage backend |
| [phase-6-mcp-server.md](./04-phase-plan/phase-6-mcp-server.md) | MCP server wrapper |
| [phase-7-polish.md](./04-phase-plan/phase-7-polish.md) | Documentation, error handling |
| [phase-8-release.md](./04-phase-plan/phase-8-release.md) | Testing, Docker, PyPI release |

### 05-testing/
| Document | Contents |
|----------|----------|
| [testing-strategy.md](./05-testing/testing-strategy.md) | Test pyramid, mock strategy, coverage |
| [test-cases.md](./05-testing/test-cases.md) | Comprehensive test case catalog |
| [ci-cd-pipeline.md](./05-testing/ci-cd-pipeline.md) | GitHub Actions workflows |

### 06-appendix/
| Document | Contents |
|----------|----------|
| [google-oauth-reference.md](./06-appendix/google-oauth-reference.md) | Gmail API and OAuth technical details |
| [mcp-protocol-reference.md](./06-appendix/mcp-protocol-reference.md) | MCP specification notes |
| [glossary.md](./06-appendix/glossary.md) | Terms and definitions |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Time to first API call | < 30 minutes (excluding Google Cloud setup) |
| Test coverage | > 80% |
| GitHub stars (6 months) | 500+ |
| PyPI downloads (6 months) | 5,000+ |
| Setup success rate | > 90% |

---

## Quick Links

- **PRD:** [gmail-multi-user-dev-mcp-prd_1.md](../gmail-multi-user-dev-mcp-prd_1.md)
- **GitHub:** TBD
- **PyPI:** TBD
- **Documentation:** TBD
