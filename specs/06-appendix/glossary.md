# Glossary

This glossary defines key terms and concepts used throughout the `gmail-multi-user-mcp` specification.

---

## A

### Access Token
A short-lived credential (typically 1 hour) issued by Google OAuth that allows API access on behalf of a user. Stored encrypted in the database.

### API (Application Programming Interface)
A set of protocols and tools for building software applications. In this context, refers to both the Gmail API and the library's Python API.

### Async/Await
Python's syntax for asynchronous programming. The `AsyncGmailClient` uses async/await for non-blocking I/O operations.

### Authorization Code
A temporary code returned by Google after user consent, exchanged for access and refresh tokens. Valid for a few minutes.

---

## B

### Backend (Storage)
The underlying database system for storing user data. Options include SQLite (development) and Supabase (production).

### Base64url
A URL-safe variant of Base64 encoding used for OAuth tokens and MIME message bodies. Uses `-` and `_` instead of `+` and `/`.

---

## C

### Callback URI
The URL where Google redirects users after OAuth authorization. The MCP server captures the authorization code from this callback.

### Client ID / Client Secret
Credentials from Google Cloud Console that identify your application. Required for OAuth flows.

### Code Challenge
The SHA256 hash of the code verifier, sent in the authorization request as part of PKCE.

### Code Verifier
A random string (43-128 characters) generated for PKCE. Stored temporarily and used during token exchange.

### Connection
A stored relationship between a user and their Gmail account, including encrypted tokens and metadata. One user can have multiple connections.

### CSRF (Cross-Site Request Forgery)
A security attack where unauthorized commands are transmitted from a trusted user. OAuth state parameter prevents CSRF.

---

## D

### Draft
An unsent email stored in Gmail's Drafts folder. Can be created, updated, and sent via the API.

---

## E

### Encryption Key
A 32-byte Fernet key used to encrypt tokens before storage. Generated during setup and stored securely.

### External User ID
An identifier from your application (e.g., your app's user ID) that maps to users in the gmail-multi-user-mcp system.

---

## F

### FastMCP
A Python framework for building MCP servers. Provides decorators for defining tools, resources, and prompts.

### Fernet
A symmetric encryption scheme from the `cryptography` library. Uses AES-128-CBC with HMAC for authentication.

---

## G

### Gmail API
Google's REST API for programmatic access to Gmail. Provides operations for messages, threads, labels, drafts, and settings.

### Gmail Query Syntax
A search language for filtering Gmail messages (e.g., `is:unread from:sender@example.com newer_than:7d`).

---

## H

### HTTP Transport
MCP transport layer using HTTP POST requests. Used for remote/hosted MCP servers.

---

## I

### IdP (Identity Provider)
A service that manages user identities. Google OAuth acts as the IdP for Gmail authentication.

---

## J

### JSON-RPC 2.0
A remote procedure call protocol using JSON. MCP uses JSON-RPC for communication between clients and servers.

---

## L

### Label
Gmail's organizational primitive. Messages can have multiple labels. Includes system labels (INBOX, SENT) and user-defined labels.

### Library-First Architecture
Design approach where core functionality exists in a standalone library, with the MCP server as a thin wrapper.

---

## M

### MCP (Model Context Protocol)
A protocol for AI assistants to interact with external tools and data sources. Defines tools, resources, and prompts.

### MIME (Multipurpose Internet Mail Extensions)
Standard for formatting email messages, including headers, body parts, and attachments.

### Migration
A database schema change applied incrementally. Migrations track applied changes to safely update production databases.

### Multi-User
Support for multiple end-users, each with their own Gmail connections, managed through a single MCP server instance.

---

## O

### OAuth 2.0
An authorization framework that enables applications to obtain limited access to user accounts. Used by Google for Gmail API access.

### OAuth State
A random string included in the authorization URL and callback. Prevents CSRF attacks by validating the callback originated from a legitimate request.

---

## P

### PKCE (Proof Key for Code Exchange)
An OAuth extension that prevents authorization code interception. Requires code_verifier and code_challenge.

### Prompt (MCP)
A pre-defined conversation template that guides the AI through a specific workflow.

---

## R

### Rate Limit
Maximum number of API requests allowed per time period. Gmail API has per-user and per-project limits.

### Refresh Token
A long-lived credential used to obtain new access tokens without user interaction. Stored encrypted.

### Resource (MCP)
A data source that the AI can read through the MCP protocol. Identified by URIs.

### RLS (Row-Level Security)
Database feature that restricts which rows users can access. Used in Supabase for multi-tenant isolation.

---

## S

### Sandbox Mode
Testing mode that simulates Gmail API responses without requiring real Google credentials.

### Scope
Permission levels requested during OAuth. Examples: `gmail.readonly`, `gmail.send`, `gmail.modify`.

### State Parameter
See OAuth State.

### stdio Transport
MCP transport using standard input/output streams. Default for Claude Desktop integration.

### Supabase
An open-source Firebase alternative providing PostgreSQL database with REST API. Used as production storage backend.

### Sync/Async
Programming paradigms. Sync (synchronous) blocks until completion; async (asynchronous) allows concurrent operations.

---

## T

### Thread
A Gmail conversation containing one or more messages. Messages in a thread share a thread_id.

### Token (Access/Refresh)
See Access Token and Refresh Token.

### Token Expiration
Access tokens expire after ~1 hour. Token manager automatically refreshes before expiration.

### Tool (MCP)
A function that the AI can invoke through the MCP protocol. Has defined inputs, outputs, and descriptions.

### Transport
The communication layer for MCP. Options include stdio, HTTP, and SSE.

### TTL (Time To Live)
Duration before data expires. OAuth states have a 10-minute TTL.

---

## U

### URI Template
A pattern for constructing URIs with variable parts. Example: `gmail://{connection_id}/labels`.

### User
An entity in the gmail-multi-user-mcp system, identified by external_user_id. Has zero or more Gmail connections.

---

## V

### Verifier
See Code Verifier.

---

## W

### Webhook
HTTP callback triggered by events. Not currently used but could enable real-time Gmail notifications.

---

## Symbol Reference

| Symbol | Meaning |
|--------|---------|
| `→` | Returns / yields |
| `□` | Task checkbox (unchecked) |
| `☑` | Task checkbox (checked) |
| `∅` | Empty / None |
| `≥` | Greater than or equal |
| `P95` | 95th percentile |

---

## Acronyms

| Acronym | Full Form |
|---------|-----------|
| API | Application Programming Interface |
| CLI | Command-Line Interface |
| CORS | Cross-Origin Resource Sharing |
| CRUD | Create, Read, Update, Delete |
| CSRF | Cross-Site Request Forgery |
| E2E | End-to-End |
| GDPR | General Data Protection Regulation |
| HTTP | Hypertext Transfer Protocol |
| HTTPS | HTTP Secure |
| ID | Identifier |
| IdP | Identity Provider |
| JSON | JavaScript Object Notation |
| MCP | Model Context Protocol |
| MIME | Multipurpose Internet Mail Extensions |
| OAuth | Open Authorization |
| PKCE | Proof Key for Code Exchange |
| REST | Representational State Transfer |
| RLS | Row-Level Security |
| RPC | Remote Procedure Call |
| SDK | Software Development Kit |
| SQL | Structured Query Language |
| SSE | Server-Sent Events |
| TLS | Transport Layer Security |
| TTL | Time To Live |
| URI | Uniform Resource Identifier |
| URL | Uniform Resource Locator |
| UUID | Universally Unique Identifier |
| YAML | YAML Ain't Markup Language |

---

## Version Numbers

| Component | Current Version |
|-----------|-----------------|
| gmail-multi-user-mcp | 1.0.0 |
| MCP Protocol | 2024-11-05 |
| Gmail API | v1 |
| Python | 3.10+ |
