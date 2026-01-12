# Phase 8: Testing, Docker & Release

**Duration:** Week 8
**Dependencies:** Phase 7 (Polish)

---

## Objectives

1. Achieve 90%+ test coverage
2. Complete end-to-end testing
3. Build and publish Docker image
4. Publish to PyPI
5. Create release artifacts

---

## Deliverables

- [ ] 90%+ test coverage
- [ ] E2E tests with real Gmail
- [ ] Docker image on ghcr.io
- [ ] Package on PyPI
- [ ] GitHub release with artifacts
- [ ] v1.0.0 announcement

---

## Task Breakdown

### 8.1 Unit Test Completion

```
□ Audit test coverage
  □ Run coverage report
  □ Identify gaps
  □ Prioritize by risk
□ Complete missing unit tests
  □ gmail_multi_user/config/ - 90%+
  □ gmail_multi_user/storage/ - 90%+
  □ gmail_multi_user/oauth/ - 90%+
  □ gmail_multi_user/tokens/ - 90%+
  □ gmail_multi_user/gmail/ - 90%+
  □ gmail_multi_user/service.py - 90%+
  □ gmail_multi_user/client.py - 90%+
  □ gmail_mcp_server/ - 90%+
□ Add edge case tests
  □ Null/empty inputs
  □ Unicode handling
  □ Large payloads
  □ Concurrent access
```

**Testing:**
- Coverage report shows 90%+
- All critical paths covered
- Edge cases handled

### 8.2 Integration Tests

```
□ Create tests/integration/test_storage_sqlite.py
  □ Full CRUD operations
  □ Concurrent access
  □ Migration testing
□ Create tests/integration/test_storage_supabase.py
  □ Full CRUD operations
  □ Connection pooling
  □ RLS enforcement
□ Create tests/integration/test_oauth_flow.py
  □ Complete OAuth flow (mocked Google)
  □ Token refresh flow
  □ Error recovery
□ Create tests/integration/test_mcp_server.py
  □ All tools via MCP protocol
  □ All resources
  □ Error handling
```

**Testing:**
- Integration tests pass in CI
- No flaky tests
- Clean teardown

### 8.3 End-to-End Tests

```
□ Set up test Gmail account
  □ Create dedicated test account
  □ Configure OAuth credentials
  □ Store credentials in GitHub Secrets
□ Create tests/e2e/test_full_flow.py
  □ OAuth connection (real Google)
  □ Search messages
  □ Get message
  □ Get thread
  □ Send message (to self)
  □ Create/send draft
  □ Label operations
  □ Archive/trash
□ Create tests/e2e/test_multi_user.py
  □ Multiple users
  □ Multiple connections per user
  □ Connection switching
□ Add E2E to CI
  □ Run on schedule (daily)
  □ Run on release tags
  □ Skip on PR (unless labeled)
```

**Testing:**
- E2E tests pass against real Gmail
- Tests are idempotent
- No test data accumulation

### 8.4 Security Testing

```
□ Create tests/security/test_encryption.py
  □ Encryption/decryption roundtrip
  □ Key rotation (manual)
  □ Tampered data detection
□ Create tests/security/test_oauth.py
  □ State validation
  □ PKCE verification
  □ Token handling
□ Create tests/security/test_injection.py
  □ SQL injection attempts
  □ Query injection
  □ Path traversal
□ Run security scan
  □ bandit for Python
  □ safety for dependencies
  □ trivy for Docker image
```

**Testing:**
- No security issues found
- All encryption tests pass
- Dependency audit clean

### 8.5 Docker Image

```
□ Create Dockerfile
  □ Multi-stage build
  □ Python 3.11 base
  □ Non-root user
  □ Health check
  □ Minimal image size
□ Create docker-compose.yml
  □ MCP server service
  □ Supabase (optional)
  □ Volume mounts
  □ Environment configuration
□ Create .dockerignore
□ Build and test locally
  □ Image builds successfully
  □ Server starts
  □ Health check passes
□ Set up GitHub Actions for Docker
  □ Build on push to main
  □ Push to ghcr.io
  □ Tag with version and latest
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry export -o requirements.txt
COPY . .
RUN pip wheel -w /wheels -r requirements.txt .

FROM python:3.11-slim
RUN useradd -m appuser
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install /wheels/*.whl && rm -rf /wheels
USER appuser
EXPOSE 8000
HEALTHCHECK CMD python -c "import gmail_multi_user; print('ok')"
ENTRYPOINT ["gmail-mcp"]
CMD ["serve", "--transport", "http", "--host", "0.0.0.0"]
```

**Testing:**
- Image builds successfully
- Image size < 200MB
- Container runs without root
- Health check works

### 8.6 PyPI Release

```
□ Prepare package metadata
  □ Update pyproject.toml
  □ Version set to 1.0.0
  □ All classifiers correct
  □ License specified
  □ URLs (repo, docs, issues)
□ Create release workflow
  □ Build sdist and wheel
  □ Test installation
  □ Upload to TestPyPI first
  □ Upload to PyPI on release
□ Test installation
  □ pip install gmail-multi-user-mcp
  □ Import works
  □ CLI works
  □ MCP server starts
```

**Package Structure:**
```
gmail-multi-user-mcp/
├── gmail_multi_user/      # Core library
├── gmail_mcp_server/      # MCP server
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

**Testing:**
- Package installs cleanly
- All dependencies resolved
- CLI entry points work

### 8.7 GitHub Release

```
□ Create release checklist
  □ All tests pass
  □ Coverage > 90%
  □ Documentation updated
  □ CHANGELOG updated
  □ Version bumped
□ Create release assets
  □ Source tarball
  □ Wheel file
  □ Docker image reference
  □ Documentation PDF (optional)
□ Write release notes
  □ Features
  □ Breaking changes
  □ Migration guide
  □ Acknowledgments
□ Create GitHub release
  □ Tag v1.0.0
  □ Release notes
  □ Attach assets
```

**Testing:**
- Release workflow completes
- Assets downloadable
- Docker image tagged correctly

### 8.8 Announcement & Launch

```
□ Create announcement content
  □ Project description
  □ Key features
  □ Quick start example
  □ Links to docs
□ Prepare demo
  □ Local docker-compose demo
  □ Recording/GIF of usage
□ Submit to directories
  □ MCP server directory
  □ Awesome MCP list (if exists)
□ Monitor post-launch
  □ GitHub issues
  □ PyPI download stats
  □ Docker pull stats
```

---

## CI/CD Pipeline Summary

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest --cov=gmail_multi_user --cov=gmail_mcp_server
      - run: poetry run coverage report --fail-under=90

  build-docker:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.ref_name }}
            ghcr.io/${{ github.repository }}:latest

  publish-pypi:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install poetry
      - run: poetry build
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}

  create-release:
    needs: [build-docker, publish-pypi]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

---

## Definition of Done

- [ ] All tasks checked off
- [ ] Test coverage ≥ 90%
- [ ] E2E tests pass against real Gmail
- [ ] Security tests pass
- [ ] Docker image published to ghcr.io
- [ ] Package published to PyPI
- [ ] GitHub release created with v1.0.0
- [ ] Documentation live and accurate

---

## Risks

| Risk | Mitigation |
|------|------------|
| E2E test flakiness | Retry logic, dedicated test account |
| PyPI name conflict | Check name availability early |
| Docker build fails in CI | Test locally first, cache layers |
| Post-launch bugs | Monitor issues, quick patch release process |

---

## Post-Release

After v1.0.0 release:

1. **Monitor**
   - GitHub issues for bugs
   - Community questions
   - Usage patterns

2. **Quick fixes**
   - Patch releases for critical bugs
   - Documentation updates

3. **v1.1 Planning**
   - Gather feature requests
   - Prioritize roadmap
   - Community contributions
