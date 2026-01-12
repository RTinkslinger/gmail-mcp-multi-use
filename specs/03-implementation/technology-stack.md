# Technology Stack

**Version:** 1.0
**Last Updated:** January 12, 2026

---

## Table of Contents

1. [Runtime Requirements](#1-runtime-requirements)
2. [Core Dependencies](#2-core-dependencies)
3. [Development Dependencies](#3-development-dependencies)
4. [External Services](#4-external-services)
5. [Complete pyproject.toml](#5-complete-pyprojecttoml)

---

## 1. Runtime Requirements

### 1.1 Python Version

| Requirement | Version | Rationale |
|-------------|---------|-----------|
| **Minimum** | Python 3.10 | Pattern matching, modern typing (`X | Y`), FastMCP compatibility |
| **Recommended** | Python 3.11+ | Better performance, improved error messages |
| **Tested** | 3.10, 3.11, 3.12 | CI matrix coverage |

### 1.2 Operating Systems

| OS | Support Level | Notes |
|----|---------------|-------|
| Linux | Full | Ubuntu 20.04+, Debian 10+ |
| macOS | Full | 11.0+ (Big Sur), Apple Silicon supported |
| Windows | Full | Windows 10+ |

### 1.3 Architecture

| Architecture | Support |
|--------------|---------|
| x86_64 | Full |
| arm64 | Full (Apple Silicon, AWS Graviton) |

---

## 2. Core Dependencies

### 2.1 HTTP & Async

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | ^0.27.0 | Async HTTP client for Gmail API calls |
| `anyio` | ^4.0.0 | Async compatibility layer |

**Rationale:** httpx is the modern async HTTP client for Python, with full HTTP/2 support and excellent async/await integration.

### 2.2 MCP Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `fastmcp` | ^0.1.0 | MCP server framework |
| `mcp` | ^1.0.0 | MCP protocol types |

**Rationale:** FastMCP is the official Anthropic-recommended framework for building MCP servers in Python.

### 2.3 Google APIs

| Package | Version | Purpose |
|---------|---------|---------|
| `google-api-python-client` | ^2.150.0 | Gmail API client |
| `google-auth` | ^2.35.0 | Google authentication |
| `google-auth-oauthlib` | ^1.2.0 | OAuth 2.0 flows |

**Rationale:** Official Google libraries ensure API compatibility and proper authentication handling.

### 2.4 Database

| Package | Version | Purpose |
|---------|---------|---------|
| `aiosqlite` | ^0.20.0 | Async SQLite for local development |
| `supabase` | ^2.10.0 | Supabase client for production |

**Rationale:** aiosqlite provides async SQLite access for development; Supabase client for production deployments.

### 2.5 Security

| Package | Version | Purpose |
|---------|---------|---------|
| `cryptography` | ^43.0.0 | Fernet encryption for tokens |

**Rationale:** cryptography is the standard Python library for encryption, providing Fernet (AES-128-CBC + HMAC).

### 2.6 Configuration

| Package | Version | Purpose |
|---------|---------|---------|
| `pyyaml` | ^6.0.0 | YAML config file parsing |
| `pydantic` | ^2.9.0 | Configuration validation and types |
| `pydantic-settings` | ^2.6.0 | Environment variable loading |

**Rationale:** Pydantic provides strong typing and validation; PyYAML for config file parsing.

### 2.7 CLI

| Package | Version | Purpose |
|---------|---------|---------|
| `typer` | ^0.12.0 | CLI framework |
| `rich` | ^13.9.0 | Terminal formatting |

**Rationale:** Typer provides modern CLI with auto-completion; Rich for beautiful terminal output.

### 2.8 Utilities

| Package | Version | Purpose |
|---------|---------|---------|
| `email-validator` | ^2.2.0 | Email address validation |

---

## 3. Development Dependencies

### 3.1 Testing

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ^8.3.0 | Test framework |
| `pytest-asyncio` | ^0.24.0 | Async test support |
| `pytest-cov` | ^5.0.0 | Coverage reporting |
| `pytest-mock` | ^3.14.0 | Mocking utilities |
| `respx` | ^0.21.0 | Mock httpx requests |
| `pytest-timeout` | ^2.3.0 | Test timeouts |

### 3.2 Type Checking

| Package | Version | Purpose |
|---------|---------|---------|
| `mypy` | ^1.13.0 | Static type checking |
| `types-PyYAML` | ^6.0.0 | Type stubs for PyYAML |

### 3.3 Formatting & Linting

| Package | Version | Purpose |
|---------|---------|---------|
| `black` | ^24.10.0 | Code formatting |
| `isort` | ^5.13.0 | Import sorting |
| `ruff` | ^0.7.0 | Fast linting |

### 3.4 Documentation

| Package | Version | Purpose |
|---------|---------|---------|
| `mkdocs` | ^1.6.0 | Documentation site |
| `mkdocs-material` | ^9.5.0 | Material theme |
| `mkdocstrings[python]` | ^0.26.0 | API docs from docstrings |

---

## 4. External Services

### 4.1 Google Cloud

| Service | Purpose | Required |
|---------|---------|----------|
| Google Cloud Project | Container for OAuth credentials | Yes |
| OAuth 2.0 Credentials | Client ID and secret | Yes |
| Gmail API | Email operations | Yes (enabled) |

**Cost:** Free (Gmail API has no per-call cost; OAuth is free)

### 4.2 Supabase (Production)

| Service | Purpose | Required |
|---------|---------|----------|
| Supabase Project | Managed PostgreSQL | For production |
| Database | Token storage | Yes |
| Connection Pooling | High-concurrency support | Recommended |

**Cost:**
- Free tier: 500MB database, 50K monthly active users
- Pro tier: $25/month for higher limits

### 4.3 Docker (Optional)

| Service | Purpose | Required |
|---------|---------|----------|
| Docker | Containerization | Optional |
| GitHub Container Registry | Image hosting | For deployment |

---

## 5. Complete pyproject.toml

```toml
[project]
name = "gmail-multi-user-mcp"
version = "1.0.0"
description = "Multi-user Gmail integration library and MCP server"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"},
]
requires-python = ">=3.10"
keywords = [
    "gmail",
    "oauth",
    "mcp",
    "model-context-protocol",
    "ai-agents",
    "email",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Communications :: Email",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Typing :: Typed",
]

dependencies = [
    # HTTP & Async
    "httpx>=0.27.0",
    "anyio>=4.0.0",

    # MCP
    "fastmcp>=0.1.0",

    # Google APIs
    "google-api-python-client>=2.150.0",
    "google-auth>=2.35.0",
    "google-auth-oauthlib>=1.2.0",

    # Database
    "aiosqlite>=0.20.0",
    "supabase>=2.10.0",

    # Security
    "cryptography>=43.0.0",

    # Configuration
    "pyyaml>=6.0.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",

    # CLI
    "typer>=0.12.0",
    "rich>=13.9.0",

    # Utilities
    "email-validator>=2.2.0",
]

[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "pytest-mock>=3.14.0",
    "respx>=0.21.0",
    "pytest-timeout>=2.3.0",

    # Type checking
    "mypy>=1.13.0",
    "types-PyYAML>=6.0.0",

    # Formatting & Linting
    "black>=24.10.0",
    "isort>=5.13.0",
    "ruff>=0.7.0",
]

docs = [
    "mkdocs>=1.6.0",
    "mkdocs-material>=9.5.0",
    "mkdocstrings[python]>=0.26.0",
]

[project.urls]
Homepage = "https://github.com/yourorg/gmail-multi-user-mcp"
Documentation = "https://gmail-multi-user-mcp.readthedocs.io"
Repository = "https://github.com/yourorg/gmail-multi-user-mcp"
Changelog = "https://github.com/yourorg/gmail-multi-user-mcp/blob/main/CHANGELOG.md"

[project.scripts]
gmail-mcp = "gmail_mcp_server.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["gmail_multi_user", "gmail_mcp_server"]

[tool.hatch.build.targets.sdist]
include = [
    "gmail_multi_user/",
    "gmail_mcp_server/",
    "migrations/",
    "templates/",
]

# Black configuration
[tool.black]
line-length = 88
target-version = ["py310", "py311", "py312"]
include = '\.pyi?$'

# isort configuration
[tool.isort]
profile = "black"
line_length = 88
known_first_party = ["gmail_multi_user", "gmail_mcp_server"]

# Ruff configuration
[tool.ruff]
line-length = 88
target-version = "py310"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]

# Mypy configuration
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = [
    "google.*",
    "googleapiclient.*",
    "supabase.*",
]
ignore_missing_imports = true

# Pytest configuration
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "-ra",
]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    "e2e: marks tests as end-to-end tests requiring real Gmail",
]

# Coverage configuration
[tool.coverage.run]
source = ["gmail_multi_user", "gmail_mcp_server"]
branch = true
omit = [
    "*/tests/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
fail_under = 80
```

---

## 6. Dependency Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           gmail-multi-user-mcp                                   │
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                         Core Dependencies                                 │  │
│   │                                                                           │  │
│   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                    │  │
│   │   │   httpx     │   │  fastmcp    │   │  pydantic   │                    │  │
│   │   │   (HTTP)    │   │  (MCP)      │   │  (Config)   │                    │  │
│   │   └─────────────┘   └─────────────┘   └─────────────┘                    │  │
│   │                                                                           │  │
│   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                    │  │
│   │   │  google-*   │   │ aiosqlite   │   │ cryptography│                    │  │
│   │   │ (Gmail API) │   │ supabase    │   │ (Encrypt)   │                    │  │
│   │   └─────────────┘   └─────────────┘   └─────────────┘                    │  │
│   │                                                                           │  │
│   │   ┌─────────────┐   ┌─────────────┐                                      │  │
│   │   │   typer     │   │   pyyaml    │                                      │  │
│   │   │   (CLI)     │   │  (Config)   │                                      │  │
│   │   └─────────────┘   └─────────────┘                                      │  │
│   │                                                                           │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                        External Services                                  │  │
│   │                                                                           │  │
│   │   ┌─────────────────────────┐   ┌─────────────────────────────────────┐  │  │
│   │   │      Google Cloud       │   │         Supabase (optional)          │  │  │
│   │   │   • OAuth 2.0           │   │   • PostgreSQL database             │  │  │
│   │   │   • Gmail API           │   │   • Connection pooling              │  │  │
│   │   └─────────────────────────┘   └─────────────────────────────────────┘  │  │
│   │                                                                           │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```
