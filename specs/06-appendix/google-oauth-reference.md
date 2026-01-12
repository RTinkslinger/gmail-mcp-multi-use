# Google OAuth & Gmail API Reference

This appendix provides technical reference information for Google OAuth 2.0 and the Gmail API as used by `gmail-multi-user-mcp`.

---

## OAuth 2.0 Overview

### Authorization Flow

```
┌─────────┐                                      ┌─────────┐
│  User   │                                      │ Google  │
└────┬────┘                                      └────┬────┘
     │                                                │
     │  1. Click "Connect Gmail"                      │
     │ ─────────────────────────────────────────────▶ │
     │                                                │
     │  2. Redirect to Google OAuth                   │
     │ ◀───────────────────────────────────────────── │
     │                                                │
     │  3. User grants permission                     │
     │ ─────────────────────────────────────────────▶ │
     │                                                │
     │  4. Redirect with authorization code           │
     │ ◀───────────────────────────────────────────── │
     │                                                │
     │  5. Exchange code for tokens                   │
     │ ─────────────────────────────────────────────▶ │
     │                                                │
     │  6. Return access + refresh tokens             │
     │ ◀───────────────────────────────────────────── │
     │                                                │
```

### PKCE (Proof Key for Code Exchange)

PKCE prevents authorization code interception attacks.

```
1. Generate code_verifier: 64-character random string
   - Characters: A-Z, a-z, 0-9, -, ., _, ~

2. Generate code_challenge: SHA256(code_verifier) → base64url

3. Include code_challenge in authorization URL

4. Include code_verifier in token exchange request

5. Google verifies: SHA256(code_verifier) == code_challenge
```

**Python Implementation:**
```python
import secrets
import hashlib
import base64

def generate_code_verifier() -> str:
    """Generate a 64-character code verifier."""
    return secrets.token_urlsafe(48)  # 64 chars after base64url

def generate_code_challenge(verifier: str) -> str:
    """Generate SHA256 code challenge from verifier."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
```

---

## Google OAuth Endpoints

### Authorization Endpoint

```
GET https://accounts.google.com/o/oauth2/v2/auth
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `client_id` | Yes | OAuth client ID |
| `redirect_uri` | Yes | Where to send the response |
| `response_type` | Yes | Always `code` |
| `scope` | Yes | Space-separated scopes |
| `state` | Yes | CSRF protection token |
| `code_challenge` | Yes* | PKCE challenge |
| `code_challenge_method` | Yes* | Always `S256` |
| `access_type` | Yes | `offline` for refresh token |
| `prompt` | No | `consent` to force consent screen |

*Required for PKCE

**Example URL:**
```
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=http://localhost:8080/callback&
  response_type=code&
  scope=https://www.googleapis.com/auth/gmail.readonly%20https://www.googleapis.com/auth/gmail.send&
  state=xyz123&
  code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&
  code_challenge_method=S256&
  access_type=offline&
  prompt=consent
```

### Token Endpoint

```
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded
```

**Token Exchange (Authorization Code):**

| Parameter | Value |
|-----------|-------|
| `grant_type` | `authorization_code` |
| `client_id` | OAuth client ID |
| `client_secret` | OAuth client secret |
| `code` | Authorization code from callback |
| `redirect_uri` | Same URI used in auth request |
| `code_verifier` | PKCE verifier |

**Response:**
```json
{
  "access_token": "ya29.a0AVvZ...",
  "expires_in": 3599,
  "refresh_token": "1//0gYT...",
  "scope": "https://www.googleapis.com/auth/gmail.readonly",
  "token_type": "Bearer"
}
```

**Token Refresh:**

| Parameter | Value |
|-----------|-------|
| `grant_type` | `refresh_token` |
| `client_id` | OAuth client ID |
| `client_secret` | OAuth client secret |
| `refresh_token` | Stored refresh token |

**Response:**
```json
{
  "access_token": "ya29.a0AVvZ...",
  "expires_in": 3599,
  "scope": "https://www.googleapis.com/auth/gmail.readonly",
  "token_type": "Bearer"
}
```

### Token Revocation Endpoint

```
POST https://oauth2.googleapis.com/revoke
Content-Type: application/x-www-form-urlencoded

token=ACCESS_OR_REFRESH_TOKEN
```

### User Info Endpoint

```
GET https://www.googleapis.com/oauth2/v2/userinfo
Authorization: Bearer ACCESS_TOKEN
```

**Response:**
```json
{
  "id": "123456789",
  "email": "user@gmail.com",
  "verified_email": true,
  "picture": "https://lh3.googleusercontent.com/..."
}
```

---

## Gmail API Scopes

| Scope | Access Level | Description |
|-------|--------------|-------------|
| `gmail.readonly` | Read-only | Read all messages, labels, settings |
| `gmail.modify` | Read + modify | All of readonly + modify messages/labels |
| `gmail.compose` | Write drafts/send | Create drafts and send messages |
| `gmail.send` | Send only | Send messages on behalf of user |
| `gmail.labels` | Labels only | Create/modify/delete labels |
| `gmail.settings.basic` | Settings | Read/update basic settings |
| `gmail.settings.sharing` | Sharing | Manage auto-forwarding |
| `gmail.metadata` | Metadata only | Read message metadata (not body) |

**Full Scope URIs:**
```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.compose
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.labels
```

**Recommended Scopes for Common Use Cases:**

| Use Case | Scopes |
|----------|--------|
| Read-only email client | `gmail.readonly` |
| Full email client | `gmail.modify`, `gmail.compose` |
| Send-only bot | `gmail.send` |
| Label management | `gmail.labels` |

---

## Gmail API Endpoints

Base URL: `https://gmail.googleapis.com/gmail/v1/users/me`

### Messages

**List/Search Messages:**
```
GET /messages?q={query}&maxResults={n}&pageToken={token}
```

**Get Message:**
```
GET /messages/{id}?format={full|metadata|minimal|raw}
```

**Send Message:**
```
POST /messages/send
Content-Type: application/json

{"raw": "BASE64URL_ENCODED_RFC2822_MESSAGE"}
```

**Modify Labels:**
```
POST /messages/{id}/modify
Content-Type: application/json

{
  "addLabelIds": ["STARRED"],
  "removeLabelIds": ["UNREAD"]
}
```

**Trash/Untrash:**
```
POST /messages/{id}/trash
POST /messages/{id}/untrash
```

**Delete Permanently:**
```
DELETE /messages/{id}
```

### Threads

**Get Thread:**
```
GET /threads/{id}?format={full|metadata|minimal}
```

### Drafts

**Create Draft:**
```
POST /drafts
Content-Type: application/json

{
  "message": {
    "raw": "BASE64URL_ENCODED_RFC2822_MESSAGE"
  }
}
```

**Update Draft:**
```
PUT /drafts/{id}
```

**Send Draft:**
```
POST /drafts/{id}/send
```

**Delete Draft:**
```
DELETE /drafts/{id}
```

### Labels

**List Labels:**
```
GET /labels
```

**Get Label:**
```
GET /labels/{id}
```

### Attachments

**Get Attachment:**
```
GET /messages/{messageId}/attachments/{id}
```

**Response:**
```json
{
  "size": 1024,
  "data": "BASE64URL_ENCODED_DATA"
}
```

---

## Gmail Query Syntax

Gmail supports a rich query language for searching messages.

### Basic Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `from:` | `from:john@example.com` | Sender address |
| `to:` | `to:me` | Recipient address |
| `cc:` | `cc:team@example.com` | CC recipient |
| `bcc:` | `bcc:secret@example.com` | BCC recipient |
| `subject:` | `subject:meeting` | Subject contains |
| `label:` | `label:important` | Has label |
| `has:` | `has:attachment` | Has feature |
| `is:` | `is:unread` | Message state |
| `in:` | `in:inbox` | In folder |

### Date Filters

| Operator | Example | Description |
|----------|---------|-------------|
| `after:` | `after:2024/01/01` | After date |
| `before:` | `before:2024/12/31` | Before date |
| `older_than:` | `older_than:7d` | Older than period |
| `newer_than:` | `newer_than:24h` | Newer than period |

**Time Units:** `d` (days), `m` (months), `y` (years)

### Content Filters

| Operator | Example | Description |
|----------|---------|-------------|
| `"exact phrase"` | `"project update"` | Exact match |
| `OR` | `from:a OR from:b` | Either condition |
| `-` | `-is:unread` | Negation |
| `()` | `(from:a OR from:b) -is:spam` | Grouping |
| `filename:` | `filename:pdf` | Attachment type |
| `larger:` | `larger:10M` | Size filter |
| `smaller:` | `smaller:1M` | Size filter |

### Special Labels

| Label | Description |
|-------|-------------|
| `INBOX` | Inbox folder |
| `SENT` | Sent messages |
| `DRAFT` | Draft messages |
| `SPAM` | Spam folder |
| `TRASH` | Trash folder |
| `UNREAD` | Unread messages |
| `STARRED` | Starred messages |
| `IMPORTANT` | Important messages |
| `CATEGORY_PERSONAL` | Personal category |
| `CATEGORY_SOCIAL` | Social category |
| `CATEGORY_PROMOTIONS` | Promotions category |
| `CATEGORY_UPDATES` | Updates category |
| `CATEGORY_FORUMS` | Forums category |

### Example Queries

```python
# Unread emails from last week
"is:unread newer_than:7d"

# Emails with PDF attachments from specific sender
"from:boss@company.com has:attachment filename:pdf"

# Important emails not in promotions
"is:important -category:promotions"

# Emails mentioning project in subject, last month
"subject:project newer_than:1m"

# Large attachments
"has:attachment larger:5M"
```

---

## Rate Limits

### Gmail API Quotas

| Quota | Limit | Period |
|-------|-------|--------|
| Queries per day | 1,000,000,000 | Daily |
| Queries per 100 seconds per user | 250 | 100 seconds |
| Send emails per day | 2,000 | Daily |

### Handling 429 (Rate Limited)

```python
import time
from httpx import Response

def handle_rate_limit(response: Response) -> int:
    """Extract retry delay from 429 response."""
    # Check Retry-After header
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        return int(retry_after)

    # Default exponential backoff
    return 60  # seconds

async def make_request_with_retry(client, request, max_retries=3):
    """Make request with exponential backoff on rate limit."""
    for attempt in range(max_retries):
        response = await client.send(request)

        if response.status_code == 429:
            delay = handle_rate_limit(response) * (2 ** attempt)
            await asyncio.sleep(delay)
            continue

        return response

    raise RateLimitError("Max retries exceeded")
```

---

## Error Responses

### Common Error Codes

| HTTP Code | Error | Description | Action |
|-----------|-------|-------------|--------|
| 400 | `invalid_grant` | Token expired/revoked | Re-authenticate |
| 401 | `invalid_credentials` | Invalid access token | Refresh token |
| 403 | `forbidden` | Insufficient scope | Request more scopes |
| 404 | `notFound` | Resource not found | Check ID |
| 429 | `rateLimitExceeded` | Too many requests | Backoff and retry |
| 500 | `backendError` | Google server error | Retry |

### Error Response Format

```json
{
  "error": {
    "code": 401,
    "message": "Invalid Credentials",
    "errors": [
      {
        "domain": "global",
        "reason": "authError",
        "message": "Invalid Credentials",
        "locationType": "header",
        "location": "Authorization"
      }
    ],
    "status": "UNAUTHENTICATED"
  }
}
```

---

## MIME Message Format

### Simple Text Message

```
MIME-Version: 1.0
From: sender@gmail.com
To: recipient@example.com
Subject: Test Subject
Content-Type: text/plain; charset="UTF-8"

This is the message body.
```

### Multipart with HTML

```
MIME-Version: 1.0
From: sender@gmail.com
To: recipient@example.com
Subject: Test Subject
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="UTF-8"

Plain text version.

--boundary123
Content-Type: text/html; charset="UTF-8"

<html><body><p>HTML version.</p></body></html>

--boundary123--
```

### With Attachment

```
MIME-Version: 1.0
From: sender@gmail.com
To: recipient@example.com
Subject: Test Subject
Content-Type: multipart/mixed; boundary="boundary456"

--boundary456
Content-Type: text/plain; charset="UTF-8"

Message with attachment.

--boundary456
Content-Type: application/pdf; name="document.pdf"
Content-Disposition: attachment; filename="document.pdf"
Content-Transfer-Encoding: base64

JVBERi0xLjQKJeLjz9MKNCAwIG9iago8PC9GaWx0ZXIvRmxhdGVE...

--boundary456--
```

### Reply Threading Headers

```
From: sender@gmail.com
To: recipient@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id@gmail.com>
References: <original-message-id@gmail.com>
```

---

## Google Cloud Console Setup

### Creating OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Gmail API:
   - APIs & Services → Library
   - Search "Gmail API" → Enable
4. Configure OAuth consent screen:
   - APIs & Services → OAuth consent screen
   - Choose "External" (or "Internal" for Workspace)
   - Add app name, support email, developer email
   - Add scopes: `gmail.readonly`, `gmail.send`, etc.
   - Add test users (for external apps before verification)
5. Create credentials:
   - APIs & Services → Credentials
   - Create Credentials → OAuth client ID
   - Application type: "Web application"
   - Add authorized redirect URIs
   - Download JSON

### OAuth Consent Screen Verification

For production apps accessing more than 100 users:
- Submit for Google verification
- Provide privacy policy URL
- May require security assessment
- Can take several weeks

### Test Users (Before Verification)

- Add specific Gmail addresses as test users
- Only these users can authorize the app
- Limit: 100 test users
