# Testing Strategy

## Overview

This document defines the comprehensive testing strategy for `gmail-multi-user-mcp`. Our approach follows the testing pyramid, emphasizing unit tests as the foundation with integration and end-to-end tests providing confidence in system behavior.

---

## Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ← Few, expensive, high confidence
                    │  Tests  │
                    └────┬────┘
                         │
                 ┌───────┴───────┐
                 │  Integration  │  ← More, moderate cost
                 │    Tests      │
                 └───────┬───────┘
                         │
         ┌───────────────┴───────────────┐
         │         Unit Tests            │  ← Many, cheap, fast
         │                               │
         └───────────────────────────────┘
```

**Target Distribution:**
- Unit Tests: 70% of test count
- Integration Tests: 25% of test count
- E2E Tests: 5% of test count

**Coverage Targets:**
- Overall: ≥90%
- Core library (`gmail_multi_user/`): ≥95%
- MCP server (`gmail_mcp_server/`): ≥85%

---

## Test Categories

### 1. Unit Tests

**Purpose:** Test individual functions and classes in isolation.

**Characteristics:**
- Fast execution (<1 second per test)
- No external dependencies (database, network)
- Use mocks for dependencies
- Run on every commit

**Location:** `tests/unit/`

**Scope:**
| Module | Test File |
|--------|-----------|
| `config/loader.py` | `test_config_loader.py` |
| `config/encryption.py` | `test_encryption.py` |
| `storage/sqlite.py` | `test_storage_sqlite.py` |
| `storage/supabase.py` | `test_storage_supabase.py` |
| `oauth/state.py` | `test_oauth_state.py` |
| `oauth/pkce.py` | `test_pkce.py` |
| `oauth/manager.py` | `test_oauth_manager.py` |
| `oauth/google.py` | `test_google_oauth.py` |
| `tokens/manager.py` | `test_token_manager.py` |
| `gmail/client.py` | `test_gmail_client.py` |
| `gmail/parser.py` | `test_mime_parser.py` |
| `gmail/composer.py` | `test_message_composer.py` |
| `service.py` | `test_service.py` |
| `client.py` | `test_client.py` |

**Mocking Strategy:**
```python
# Mock external HTTP calls
@pytest.fixture
def mock_httpx():
    with respx.mock:
        yield respx

# Mock storage backend
@pytest.fixture
def mock_storage():
    return Mock(spec=StorageBackend)

# Mock time for token expiration tests
@pytest.fixture
def frozen_time():
    with freeze_time("2024-01-15 10:00:00"):
        yield
```

### 2. Integration Tests

**Purpose:** Test interactions between components and external systems.

**Characteristics:**
- Moderate execution time (seconds to minutes)
- May use real database (SQLite in-memory)
- May use mocked external services
- Run on PR and main branch

**Location:** `tests/integration/`

**Scope:**
| Test Suite | Description |
|------------|-------------|
| `test_storage_sqlite.py` | Full CRUD against SQLite |
| `test_storage_supabase.py` | Full CRUD against Supabase (CI only) |
| `test_oauth_flow.py` | Complete OAuth flow with mocked Google |
| `test_token_lifecycle.py` | Token refresh and expiration |
| `test_gmail_operations.py` | Gmail API operations with mocked responses |
| `test_mcp_tools.py` | All MCP tools via protocol |
| `test_mcp_resources.py` | All MCP resources |
| `test_cli.py` | CLI commands |

**Integration Test Setup:**
```python
@pytest.fixture
async def test_client():
    """Create a test client with in-memory SQLite."""
    config = Config(
        storage=StorageConfig(backend="sqlite", sqlite_path=":memory:"),
        encryption_key=Fernet.generate_key().decode(),
        google_oauth=GoogleOAuthConfig(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )
    )
    client = AsyncGmailClient(config)
    await client.initialize()
    yield client
    await client.close()
```

### 3. End-to-End Tests

**Purpose:** Validate complete user workflows against real services.

**Characteristics:**
- Slow execution (minutes)
- Uses real Gmail API with test account
- Run on schedule and before releases
- May be flaky due to network

**Location:** `tests/e2e/`

**Scope:**
| Test Suite | Description |
|------------|-------------|
| `test_full_flow.py` | OAuth → Search → Read → Send |
| `test_multi_user.py` | Multiple users and connections |
| `test_error_recovery.py` | Token expiration and refresh |

**E2E Test Account:**
- Dedicated Gmail account for testing
- Credentials stored in GitHub Secrets
- Test emails cleaned up after runs

**E2E Test Structure:**
```python
@pytest.mark.e2e
@pytest.mark.skipif(not os.getenv("GMAIL_TEST_REFRESH_TOKEN"),
                    reason="E2E credentials not available")
async def test_full_email_workflow():
    """Test complete email workflow against real Gmail."""
    client = AsyncGmailClient.from_env()

    # Search for messages
    results = await client.search("user_123", "test_conn", "newer_than:1d")
    assert results.messages is not None

    # Get a message if available
    if results.messages:
        msg = await client.get_message("user_123", "test_conn",
                                       results.messages[0].id)
        assert msg.subject is not None
```

### 4. Security Tests

**Purpose:** Validate security controls and prevent vulnerabilities.

**Location:** `tests/security/`

**Scope:**
| Test Suite | Description |
|------------|-------------|
| `test_encryption.py` | Token encryption roundtrip |
| `test_oauth_security.py` | State validation, PKCE |
| `test_injection.py` | SQL injection, query injection |
| `test_auth_bypass.py` | Unauthorized access attempts |

### 5. Performance Tests

**Purpose:** Ensure acceptable performance under load.

**Location:** `tests/performance/`

**Scope:**
| Test Suite | Description |
|------------|-------------|
| `test_token_validation.py` | Token check latency |
| `test_concurrent_access.py` | Multiple simultaneous operations |
| `test_storage_performance.py` | Database query performance |

---

## Mocking Strategy

### Gmail API Mocking

Use `respx` for HTTP mocking with realistic responses:

```python
# tests/mocks/gmail_responses.py

SAMPLE_MESSAGE = {
    "id": "msg_123",
    "threadId": "thread_456",
    "labelIds": ["INBOX", "UNREAD"],
    "snippet": "This is a test message...",
    "payload": {
        "headers": [
            {"name": "From", "value": "sender@example.com"},
            {"name": "To", "value": "recipient@example.com"},
            {"name": "Subject", "value": "Test Subject"},
            {"name": "Date", "value": "Mon, 15 Jan 2024 10:00:00 -0000"},
        ],
        "body": {
            "data": base64.urlsafe_b64encode(b"Test body").decode()
        }
    }
}

SAMPLE_SEARCH_RESPONSE = {
    "messages": [
        {"id": "msg_123", "threadId": "thread_456"},
        {"id": "msg_124", "threadId": "thread_457"},
    ],
    "resultSizeEstimate": 2
}
```

### Google OAuth Mocking

```python
# tests/mocks/google_oauth.py

@pytest.fixture
def mock_google_oauth(respx_mock):
    # Token exchange
    respx_mock.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        })
    )

    # User info
    respx_mock.get("https://www.googleapis.com/oauth2/v2/userinfo").mock(
        return_value=httpx.Response(200, json={
            "email": "test@gmail.com"
        })
    )
```

### Storage Mocking

```python
# tests/mocks/storage.py

class MockStorageBackend(StorageBackend):
    """In-memory storage for testing."""

    def __init__(self):
        self.users: dict[str, User] = {}
        self.connections: dict[str, Connection] = {}
        self.oauth_states: dict[str, OAuthState] = {}

    async def get_or_create_user(self, external_user_id: str, email: str | None) -> User:
        if external_user_id not in self.users:
            self.users[external_user_id] = User(
                id=str(uuid4()),
                external_user_id=external_user_id,
                email=email,
                created_at=datetime.utcnow()
            )
        return self.users[external_user_id]

    # ... implement other methods
```

---

## Test Fixtures

### Shared Fixtures

```python
# tests/conftest.py

import pytest
from gmail_multi_user.config import Config
from gmail_multi_user.storage.sqlite import SQLiteBackend

@pytest.fixture
def config():
    """Default test configuration."""
    return Config(
        storage=StorageConfig(backend="sqlite", sqlite_path=":memory:"),
        encryption_key=Fernet.generate_key().decode(),
        google_oauth=GoogleOAuthConfig(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )
    )

@pytest.fixture
async def storage(config):
    """Initialized SQLite storage."""
    backend = SQLiteBackend(config.storage.sqlite_path)
    await backend.initialize()
    yield backend
    await backend.close()

@pytest.fixture
def encryption_key():
    """Test encryption key."""
    return Fernet.generate_key().decode()

@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id="user_uuid_123",
        external_user_id="ext_user_001",
        email="test@example.com",
        created_at=datetime(2024, 1, 15, 10, 0, 0)
    )

@pytest.fixture
def sample_connection(sample_user, encryption_key):
    """Sample connection for testing."""
    fernet = Fernet(encryption_key.encode())
    return Connection(
        id="conn_uuid_456",
        user_id=sample_user.id,
        gmail_address="test@gmail.com",
        encrypted_access_token=fernet.encrypt(b"access_token").decode(),
        encrypted_refresh_token=fernet.encrypt(b"refresh_token").decode(),
        token_expires_at=datetime.utcnow() + timedelta(hours=1),
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        is_active=True,
        created_at=datetime(2024, 1, 15, 10, 0, 0)
    )
```

---

## Test Data Management

### Factories

Use factory pattern for test data:

```python
# tests/factories.py

from factory import Factory, Faker, LazyAttribute
from gmail_multi_user.models import User, Connection

class UserFactory(Factory):
    class Meta:
        model = User

    id = Faker("uuid4")
    external_user_id = Faker("uuid4")
    email = Faker("email")
    created_at = Faker("date_time_this_year")

class ConnectionFactory(Factory):
    class Meta:
        model = Connection

    id = Faker("uuid4")
    user_id = Faker("uuid4")
    gmail_address = Faker("email", domain="gmail.com")
    is_active = True
```

### Sample Email Data

```python
# tests/data/sample_emails.py

PLAIN_TEXT_EMAIL = {
    "id": "plain_001",
    "raw": "...",  # Base64 encoded MIME
    "expected_body": "This is a plain text email.",
    "expected_subject": "Plain Text Test",
}

HTML_EMAIL = {
    "id": "html_001",
    "raw": "...",
    "expected_body_text": "This is the text version.",
    "expected_body_html": "<p>This is the <b>HTML</b> version.</p>",
}

MULTIPART_WITH_ATTACHMENT = {
    "id": "attach_001",
    "raw": "...",
    "expected_attachments": [
        {"filename": "test.pdf", "mime_type": "application/pdf", "size": 1024}
    ]
}
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Run unit tests
        run: poetry run pytest tests/unit -v --cov=gmail_multi_user --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Run integration tests
        run: poetry run pytest tests/integration -v

  e2e-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Run E2E tests
        env:
          GMAIL_TEST_REFRESH_TOKEN: ${{ secrets.GMAIL_TEST_REFRESH_TOKEN }}
          GOOGLE_CLIENT_ID: ${{ secrets.GOOGLE_CLIENT_ID }}
          GOOGLE_CLIENT_SECRET: ${{ secrets.GOOGLE_CLIENT_SECRET }}
        run: poetry run pytest tests/e2e -v -m e2e

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install poetry bandit safety
          poetry install
      - name: Run bandit
        run: bandit -r gmail_multi_user gmail_mcp_server -ll
      - name: Run safety check
        run: safety check
```

### Test Execution Commands

```bash
# Run all tests
poetry run pytest

# Run unit tests only
poetry run pytest tests/unit

# Run with coverage
poetry run pytest --cov=gmail_multi_user --cov=gmail_mcp_server --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_oauth_manager.py -v

# Run tests matching pattern
poetry run pytest -k "test_token" -v

# Run E2E tests (requires credentials)
poetry run pytest tests/e2e -v -m e2e

# Run with parallel execution
poetry run pytest -n auto
```

---

## Quality Gates

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: poetry run pytest tests/unit -x -q
        language: system
        pass_filenames: false
        always_run: true
```

### Coverage Requirements

| Module | Minimum Coverage |
|--------|------------------|
| `gmail_multi_user/config/` | 95% |
| `gmail_multi_user/storage/` | 90% |
| `gmail_multi_user/oauth/` | 95% |
| `gmail_multi_user/tokens/` | 95% |
| `gmail_multi_user/gmail/` | 90% |
| `gmail_multi_user/service.py` | 95% |
| `gmail_multi_user/client.py` | 90% |
| `gmail_mcp_server/` | 85% |

### Test Quality Metrics

- All tests must pass
- No flaky tests (consistent results)
- Test execution time < 5 minutes for unit tests
- Integration tests < 10 minutes
- E2E tests < 30 minutes
