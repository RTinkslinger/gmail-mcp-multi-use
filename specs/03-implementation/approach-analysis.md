# Implementation Approach Analysis

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Approach A: MCP-First](#2-approach-a-mcp-first)
3. [Approach B: Library-First](#3-approach-b-library-first)
4. [Approach C: Separate Packages](#4-approach-c-separate-packages)
5. [Comparison Matrix](#5-comparison-matrix)
6. [Recommendation](#6-recommendation)

---

## 1. Overview

Three architectural approaches were considered for implementing gmail-multi-user-mcp:

| Approach | Description | Primary Interface |
|----------|-------------|-------------------|
| **A: MCP-First** | Build MCP server, extract library | MCP tools |
| **B: Library-First** | Build library, wrap with MCP | Python library |
| **C: Separate Packages** | Independent library and MCP server | Both equal |

Each approach has implications for:
- Developer experience
- Code reusability
- Maintenance burden
- Testing complexity
- Adoption path

---

## 2. Approach A: MCP-First

### 2.1 Description

Build the MCP server as the primary artifact, with library functionality as a secondary extraction.

```
gmail-multi-user-mcp/
├── gmail_mcp_server/          # Primary: MCP server
│   ├── server.py              # Main FastMCP server
│   ├── tools/                 # Tool implementations (all logic here)
│   │   ├── auth.py
│   │   ├── gmail.py
│   │   └── ...
│   ├── storage.py             # Storage backend
│   └── oauth.py               # OAuth flow
│
└── gmail_multi_user/          # Secondary: Thin wrapper
    ├── __init__.py
    └── client.py              # Imports from gmail_mcp_server
```

### 2.2 Pros

| Pro | Explanation |
|-----|-------------|
| MCP-native design | Tools designed for AI interaction from start |
| Natural prompt/resource support | First-class MCP primitives |
| Fast MCP iteration | Changes directly in main code |
| Claude Code focus | Optimized for primary vibe-coding use case |

### 2.3 Cons

| Con | Explanation |
|-----|-------------|
| **Library feels like afterthought** | API shaped by MCP tool constraints |
| **Sync API awkward** | MCP is async; sync wrapper is overhead on overhead |
| **Tool schemas dictate types** | Library types bound to MCP JSON schemas |
| **Harder programmatic testing** | Must mock MCP layer for library tests |
| **Limited adoption** | Non-MCP users see MCP overhead in their stack |

### 2.4 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    gmail-multi-user-mcp                             │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              MCP Server (gmail_mcp_server/)                 │  │
│   │                                                              │  │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │  │
│   │   │    Tools    │  │  Resources  │  │      Prompts        │ │  │
│   │   │             │  │             │  │                     │ │  │
│   │   │ ┌─────────┐ │  │             │  │                     │ │  │
│   │   │ │OAuth    │ │  │             │  │                     │ │  │
│   │   │ │Gmail    │ │  │             │  │                     │ │  │
│   │   │ │Storage  │ │  │             │  │                     │ │  │
│   │   │ └─────────┘ │  │             │  │                     │ │  │
│   │   │  All logic  │  │             │  │                     │ │  │
│   │   │  lives here │  │             │  │                     │ │  │
│   │   └─────────────┘  └─────────────┘  └─────────────────────┘ │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                │                                    │
│                                │ Import & wrap                      │
│                                ▼                                    │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              Library (gmail_multi_user/)                     │  │
│   │                                                              │  │
│   │   class GmailClient:                                         │  │
│   │       def search(self, ...):                                 │  │
│   │           return mcp_server.tools.gmail_search(...)          │  │
│   │                                                              │  │
│   │   # Awkward: Library imports from MCP server                 │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Approach B: Library-First

### 3.1 Description

Build the core library as the primary artifact. MCP server is a thin wrapper (~200 lines) that exposes library methods as MCP tools.

```
gmail-multi-user-mcp/
├── gmail_multi_user/          # Primary: Core library
│   ├── __init__.py            # Public exports
│   ├── client.py              # GmailClient, AsyncGmailClient
│   ├── config.py              # Configuration loading
│   ├── oauth/                 # OAuth flow
│   ├── storage/               # Storage backends
│   ├── gmail/                 # Gmail API wrapper
│   └── tokens/                # Token management
│
└── gmail_mcp_server/          # Secondary: Thin wrapper
    ├── __init__.py
    ├── server.py              # ~200 lines: imports library, exposes tools
    └── cli.py
```

### 3.2 Pros

| Pro | Explanation |
|-----|-------------|
| **Clean library API** | Designed for Python best practices |
| **Easy programmatic testing** | Test library directly, no MCP mocking |
| **Broad adoption** | Works for non-MCP users (majority of production) |
| **Natural sync/async** | Library designed for both; MCP calls async |
| **Faster direct usage** | No MCP overhead for library users |
| **Type-safe** | Python types independent of JSON schemas |

### 3.3 Cons

| Con | Explanation |
|-----|-------------|
| MCP is derivative | MCP tools must map to library methods |
| Two sets of documentation | Library API + MCP tools |
| MCP-specific features need planning | Prompts, resources need thought |

### 3.4 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    gmail-multi-user-mcp                             │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              Core Library (gmail_multi_user/)               │  │
│   │                                                              │  │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│   │   │ GmailClient  │  │ AsyncGmail   │  │   Config        │  │  │
│   │   │ (Sync API)   │  │ Client       │  │   Loader        │  │  │
│   │   │              │  │ (Async API)  │  │                 │  │  │
│   │   └──────────────┘  └──────────────┘  └──────────────────┘  │  │
│   │                                                              │  │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│   │   │    OAuth     │  │    Token     │  │    Gmail API    │  │  │
│   │   │   Manager    │  │   Manager    │  │    Client       │  │  │
│   │   └──────────────┘  └──────────────┘  └──────────────────┘  │  │
│   │                                                              │  │
│   │   ┌────────────────────────────────────────────────────────┐ │  │
│   │   │              Storage Backend (Abstract)                │ │  │
│   │   │         SQLite        │        Supabase               │ │  │
│   │   └────────────────────────────────────────────────────────┘ │  │
│   │                                                              │  │
│   │   THIS IS WHERE ALL THE VALUE LIVES                          │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                │                                    │
│                                │ Import & wrap (thin layer)         │
│                                ▼                                    │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              MCP Server (gmail_mcp_server/)                  │  │
│   │              ~200 lines of code                              │  │
│   │                                                              │  │
│   │   from gmail_multi_user import AsyncGmailClient              │  │
│   │   client = AsyncGmailClient()                                │  │
│   │                                                              │  │
│   │   @mcp.tool()                                                │  │
│   │   async def gmail_search(connection_id, query, ...):         │  │
│   │       return await client.search(connection_id, query, ...)  │  │
│   │                                                              │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Approach C: Separate Packages

### 4.1 Description

Publish two independent packages: a Python library and an MCP server. They share no code.

```
# Two separate repositories/packages

gmail-multi-user/              # Package 1: Pure Python library
├── gmail_multi_user/
│   ├── client.py
│   ├── oauth.py
│   └── ...
└── pyproject.toml

gmail-multi-user-mcp-server/   # Package 2: MCP server (depends on package 1)
├── gmail_mcp_server/
│   ├── server.py
│   └── ...
└── pyproject.toml             # dependency: gmail-multi-user
```

### 4.2 Pros

| Pro | Explanation |
|-----|-------------|
| Clear separation | Library users don't install MCP deps |
| Independent versioning | Can release library without MCP changes |
| Smaller install size | Library package is minimal |

### 4.3 Cons

| Con | Explanation |
|-----|-------------|
| **Two repos to maintain** | Double the issues, PRs, releases |
| **Version coordination** | Must keep compatible versions |
| **Confusing for users** | Which package do I install? |
| **Duplicated docs** | Separate READMEs, guides |
| **Testing complexity** | Integration tests span packages |

### 4.4 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Package 1: gmail-multi-user                      │
│                                                                     │
│   Pure Python library                                               │
│   No MCP dependencies                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ pip dependency
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│               Package 2: gmail-multi-user-mcp-server                │
│                                                                     │
│   MCP server that depends on gmail-multi-user                       │
│   Separate package, separate repo                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Problems:
- Two packages to install for full functionality
- Two repos to maintain
- Version mismatches possible
- Confusing naming
```

---

## 5. Comparison Matrix

| Criterion | A: MCP-First | B: Library-First | C: Separate Packages |
|-----------|--------------|------------------|----------------------|
| **Library API quality** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **MCP experience** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Code reuse** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Maintenance burden** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Testing simplicity** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **User confusion** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Adoption breadth** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Performance (library)** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### Scoring Explanation

- **Library API quality**: How clean is the Python library API?
- **MCP experience**: How natural is the MCP server interface?
- **Code reuse**: How much code is shared vs duplicated?
- **Maintenance burden**: How much effort to maintain long-term?
- **Testing simplicity**: How easy to test comprehensively?
- **User confusion**: How clear is which package to use?
- **Adoption breadth**: How many different use cases supported?
- **Performance**: Overhead for direct library usage?

---

## 6. Recommendation

### 6.1 Decision: Approach B (Library-First)

**Approach B: Library-First** is the recommended implementation approach.

### 6.2 Rationale

1. **80% of production users will use the library directly**
   - Python backend developers don't need MCP
   - Library-first ensures best experience for majority

2. **Clean API design**
   - Library can follow Python best practices
   - Not constrained by MCP JSON schemas

3. **Simple testing**
   - Unit test library methods directly
   - MCP server tests are integration tests

4. **MCP overhead is minimal**
   - ~200 lines to wrap library as MCP tools
   - Easy to add MCP-specific features

5. **Single package simplicity**
   - One package to install
   - One repo to maintain
   - Clear documentation

### 6.3 Implementation Notes

```python
# The MCP server is intentionally thin:

# gmail_mcp_server/server.py
from fastmcp import FastMCP
from gmail_multi_user import AsyncGmailClient

mcp = FastMCP("gmail-multi-user-mcp")
client = AsyncGmailClient()  # Single instance, reuses config

@mcp.tool()
async def gmail_search(
    connection_id: str,
    query: str,
    max_results: int = 10,
    include_body: bool = False,
) -> dict:
    """Search emails using Gmail query syntax."""
    result = await client.search(
        connection_id=connection_id,
        query=query,
        max_results=max_results,
        include_body=include_body,
    )
    return result.to_dict()

# ... ~20 more tools, all following this pattern
```

### 6.4 When to Reconsider

Re-evaluate this decision if:
- MCP becomes the dominant way developers use Gmail integration (unlikely)
- Library and MCP server need significantly different architectures
- Performance requirements favor MCP-native implementation
