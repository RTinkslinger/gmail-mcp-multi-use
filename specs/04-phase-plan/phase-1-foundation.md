# Phase 1: Project Foundation

**Duration:** Week 1
**Dependencies:** None

---

## Objectives

1. Set up project repository and tooling
2. Implement configuration system
3. Create SQLite storage backend
4. Build encryption utilities
5. Establish test infrastructure

---

## Deliverables

- [ ] Repository with proper structure
- [ ] `pip install .` works
- [ ] Configuration loading from env/file/home
- [ ] SQLite storage backend functional
- [ ] Fernet encryption for tokens
- [ ] 90%+ test coverage for phase code

---

## Task Breakdown

### 1.1 Repository Setup

```
□ Create GitHub repository
□ Initialize pyproject.toml with all dependencies
□ Set up directory structure per repository-structure.md
□ Create .gitignore (Python, IDE, secrets)
□ Add LICENSE (MIT)
□ Create README.md skeleton
□ Set up pre-commit hooks (black, isort, ruff)
```

**Testing:** `pip install -e .` succeeds

### 1.2 Configuration System

```
□ Create gmail_multi_user/config.py
  □ Config dataclass with all fields
  □ ConfigLoader.load() method
  □ Environment variable mapping (GMAIL_MCP_*)
  □ File discovery (local → home)
  □ YAML parsing with pydantic validation
□ Create gmail_config.yaml.example
□ Handle missing/invalid config with clear errors
```

**Testing:**
- Config loads from env vars only
- Config loads from local file
- Config loads from home directory
- Env vars override file values
- Invalid config raises ConfigError with message

### 1.3 Type Definitions

```
□ Create gmail_multi_user/types.py
  □ User dataclass
  □ Connection dataclass
  □ OAuthState dataclass
  □ AuthUrlResult dataclass
  □ CallbackResult dataclass
  □ ConnectionStatus dataclass
□ Create gmail_multi_user/exceptions.py
  □ GmailMCPError base class
  □ ConfigError
  □ AuthError
  □ TokenError
  □ ConnectionError
  □ GmailAPIError
  □ RateLimitError
```

**Testing:** Types serialize/deserialize correctly

### 1.4 Storage Backend Interface

```
□ Create gmail_multi_user/storage/base.py
  □ StorageBackend Protocol/ABC
  □ All method signatures with docstrings
□ Create gmail_multi_user/storage/factory.py
  □ StorageFactory.create(config) method
```

**Testing:** Factory raises error for unknown type

### 1.5 SQLite Backend

```
□ Create gmail_multi_user/storage/sqlite.py
  □ SQLiteBackend class implementing StorageBackend
  □ initialize() - create tables
  □ close() - close connection
  □ get_or_create_user()
  □ get_user_by_external_id()
  □ list_users()
  □ create_connection()
  □ get_connection()
  □ list_connections()
  □ update_connection_tokens()
  □ deactivate_connection()
  □ delete_connection()
  □ create_oauth_state()
  □ get_oauth_state()
  □ delete_oauth_state()
  □ cleanup_expired_states()
□ Create migrations/sqlite/001_initial.sql
```

**Testing:**
- CRUD operations for users
- CRUD operations for connections
- OAuth state creation and validation
- Expired state cleanup
- :memory: mode works

### 1.6 Encryption Utilities

```
□ Create gmail_multi_user/tokens/encryption.py
  □ TokenEncryption class
  □ __init__(key: str) - accept hex or base64 key
  □ encrypt(plaintext: str) -> str
  □ decrypt(ciphertext: str) -> str
  □ validate_key() method
  □ generate_key() class method
```

**Testing:**
- Encrypt/decrypt round-trip
- Invalid key raises error
- Tampered ciphertext raises error
- Key generation produces valid keys

### 1.7 Test Infrastructure

```
□ Create tests/conftest.py
  □ Fixture: temp config file
  □ Fixture: in-memory SQLite
  □ Fixture: encryption key
  □ Fixture: mock Gmail API responses
□ Create tests/unit/test_config.py
□ Create tests/unit/test_storage_sqlite.py
□ Create tests/unit/test_encryption.py
□ Set up pytest configuration
□ Set up coverage reporting
```

**Testing:** `pytest --cov` runs successfully

### 1.8 CI Setup

```
□ Create .github/workflows/test.yml
  □ Run on push and PR
  □ Python version matrix (3.10, 3.11, 3.12)
  □ Install dependencies
  □ Run pytest with coverage
  □ Upload coverage to Codecov
□ Create .github/workflows/lint.yml
  □ Run black check
  □ Run isort check
  □ Run ruff
  □ Run mypy
```

**Testing:** CI passes on main branch

---

## Definition of Done

- [ ] All tasks checked off
- [ ] `pip install -e .` works
- [ ] `pytest` passes with 90%+ coverage
- [ ] CI pipeline green
- [ ] Code follows style guide (black, isort, ruff)
- [ ] Type hints complete (mypy passes)

---

## Risks

| Risk | Mitigation |
|------|------------|
| Pydantic v2 migration issues | Pin version, test thoroughly |
| SQLite async compatibility | Use aiosqlite correctly |
| Key format confusion | Document both hex and base64 |
