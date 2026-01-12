# CI/CD Pipeline

This document defines the complete CI/CD pipeline for the `gmail-multi-user-mcp` project using GitHub Actions.

---

## Pipeline Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Push     │───▶│    Test     │───▶│    Build    │───▶│   Deploy    │
│   Trigger   │    │    Stage    │    │    Stage    │    │    Stage    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                         │                  │                  │
                         ▼                  ▼                  ▼
                   - Lint/Format      - Docker Image     - PyPI (tags)
                   - Unit Tests       - Wheel/Sdist      - GHCR (tags)
                   - Integration                         - GitHub Release
                   - Security Scan
```

---

## Workflow Files

### 1. Main CI Workflow (`ci.yml`)

Runs on every push and pull request.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: '3.11'
  POETRY_VERSION: '1.7.1'

jobs:
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        uses: actions/cache@v3
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Run ruff linter
        run: poetry run ruff check .

      - name: Run ruff formatter check
        run: poetry run ruff format --check .

      - name: Run mypy
        run: poetry run mypy gmail_multi_user gmail_mcp_server

  unit-tests:
    name: Unit Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        uses: actions/cache@v3
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Run unit tests
        run: |
          poetry run pytest tests/unit \
            -v \
            --cov=gmail_multi_user \
            --cov=gmail_mcp_server \
            --cov-report=xml \
            --cov-report=term-missing \
            --junitxml=junit.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        if: matrix.python-version == '3.11'
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-unit

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.python-version }}
          path: junit.xml

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Run integration tests
        run: |
          poetry run pytest tests/integration \
            -v \
            --cov=gmail_multi_user \
            --cov=gmail_mcp_server \
            --cov-report=xml \
            --junitxml=junit-integration.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: integration
          name: codecov-integration

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install security tools
        run: pip install bandit safety pip-audit

      - name: Run bandit
        run: bandit -r gmail_multi_user gmail_mcp_server -ll -ii

      - name: Run safety check
        run: safety check --full-report
        continue-on-error: true

      - name: Run pip-audit
        run: pip-audit
        continue-on-error: true

  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: [lint, unit-tests]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}

      - name: Build package
        run: poetry build

      - name: Verify package
        run: |
          pip install dist/*.whl
          python -c "import gmail_multi_user; print(gmail_multi_user.__version__)"
          gmail-mcp --help

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
```

### 2. E2E Tests Workflow (`e2e.yml`)

Runs on schedule and before releases.

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:
  push:
    tags: ['v*']

jobs:
  e2e-tests:
    name: End-to-End Tests
    runs-on: ubuntu-latest
    environment: e2e-testing
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Run E2E tests
        env:
          GOOGLE_CLIENT_ID: ${{ secrets.GOOGLE_CLIENT_ID }}
          GOOGLE_CLIENT_SECRET: ${{ secrets.GOOGLE_CLIENT_SECRET }}
          GMAIL_TEST_REFRESH_TOKEN: ${{ secrets.GMAIL_TEST_REFRESH_TOKEN }}
          GMAIL_TEST_EMAIL: ${{ secrets.GMAIL_TEST_EMAIL }}
        run: |
          poetry run pytest tests/e2e \
            -v \
            -m e2e \
            --tb=long

      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          channel-id: 'C123456789'
          slack-message: 'E2E tests failed: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}'
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
```

### 3. Release Workflow (`release.yml`)

Triggered by version tags.

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

env:
  PYTHON_VERSION: '3.11'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Run all tests first
  test:
    name: Run Tests
    uses: ./.github/workflows/ci.yml

  # Build and push Docker image
  docker:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.ref_name }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  # Publish to PyPI
  pypi:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    needs: test
    environment: pypi
    permissions:
      id-token: write  # For trusted publishing
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Verify version matches tag
        run: |
          POETRY_VERSION=$(poetry version -s)
          TAG_VERSION=${GITHUB_REF#refs/tags/v}
          if [ "$POETRY_VERSION" != "$TAG_VERSION" ]; then
            echo "Version mismatch: pyproject.toml=$POETRY_VERSION, tag=$TAG_VERSION"
            exit 1
          fi

      - name: Build package
        run: poetry build

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
          skip-existing: true

      - name: Test install from TestPyPI
        run: |
          pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            gmail-multi-user-mcp
          python -c "import gmail_multi_user; print(gmail_multi_user.__version__)"

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

  # Create GitHub Release
  release:
    name: Create GitHub Release
    runs-on: ubuntu-latest
    needs: [docker, pypi]
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Download build artifacts
        uses: actions/download-artifact@v3
        with:
          name: dist
          path: dist/

      - name: Generate changelog
        id: changelog
        uses: orhun/git-cliff-action@v2
        with:
          config: cliff.toml
          args: --latest --strip header

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          body: |
            ## What's Changed
            ${{ steps.changelog.outputs.content }}

            ## Installation

            **PyPI:**
            ```bash
            pip install gmail-multi-user-mcp
            ```

            **Docker:**
            ```bash
            docker pull ghcr.io/${{ github.repository }}:${{ github.ref_name }}
            ```

            ## Documentation
            See the [documentation](https://github.com/${{ github.repository }}#readme) for usage instructions.
          files: |
            dist/*.whl
            dist/*.tar.gz
          generate_release_notes: true
          draft: false
          prerelease: ${{ contains(github.ref, '-') }}
```

### 4. Dependabot Configuration

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    groups:
      python-packages:
        patterns:
          - "*"
    labels:
      - "dependencies"
      - "python"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "github-actions"

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"
```

---

## Secrets Configuration

### Required Secrets

| Secret | Purpose | Where to Get |
|--------|---------|--------------|
| `GOOGLE_CLIENT_ID` | OAuth client ID for E2E tests | Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret | Google Cloud Console |
| `GMAIL_TEST_REFRESH_TOKEN` | Pre-authorized refresh token | OAuth playground |
| `GMAIL_TEST_EMAIL` | Test Gmail address | Your test account |
| `PYPI_API_TOKEN` | PyPI upload token | pypi.org account |
| `SLACK_BOT_TOKEN` | Failure notifications (optional) | Slack app settings |

### Environment Setup

```bash
# Create environments in GitHub repo settings:
# 1. "e2e-testing" - For E2E test secrets
# 2. "pypi" - For PyPI publishing with trusted publishing
```

---

## Pipeline Stages Detail

### Stage 1: Lint & Format

**Tools:**
- `ruff` - Fast Python linter
- `ruff format` - Code formatter
- `mypy` - Static type checking

**Configuration:**

```toml
# pyproject.toml
[tool.ruff]
target-version = "py310"
line-length = 100
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.isort]
known-first-party = ["gmail_multi_user", "gmail_mcp_server"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]
```

### Stage 2: Unit Tests

**Configuration:**

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow tests",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["gmail_multi_user", "gmail_mcp_server"]
branch = true
omit = ["*/tests/*", "*/__main__.py"]

[tool.coverage.report]
fail_under = 90
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

### Stage 3: Integration Tests

**Test Database Setup:**

```yaml
# In workflow
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: gmail_mcp_test
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### Stage 4: Security Scan

**Tools:**
- `bandit` - Python security linter
- `safety` - Dependency vulnerability check
- `pip-audit` - Alternative vulnerability scanner
- `trivy` - Container image scanner

### Stage 5: Build & Release

**Version Management:**

```bash
# Bump version and create tag
poetry version patch  # or minor, major
git add pyproject.toml
git commit -m "Bump version to $(poetry version -s)"
git tag v$(poetry version -s)
git push origin main --tags
```

---

## Branch Protection Rules

### `main` Branch

- Require pull request before merging
- Require status checks:
  - `lint`
  - `unit-tests (3.10)`
  - `unit-tests (3.11)`
  - `unit-tests (3.12)`
  - `integration-tests`
  - `security-scan`
- Require conversation resolution
- Require linear history
- Do not allow force pushes

### `develop` Branch

- Require pull request before merging
- Require status checks:
  - `lint`
  - `unit-tests (3.11)`
- Allow force pushes for maintainers

---

## Monitoring & Notifications

### GitHub Actions Dashboard

Monitor at: `https://github.com/{owner}/{repo}/actions`

### Coverage Reports

- Codecov dashboard: `https://codecov.io/gh/{owner}/{repo}`
- Badge in README:
  ```markdown
  [![codecov](https://codecov.io/gh/{owner}/{repo}/branch/main/graph/badge.svg)](https://codecov.io/gh/{owner}/{repo})
  ```

### Security Alerts

- GitHub Security tab for Dependabot alerts
- Trivy results in Security tab (SARIF upload)

### Failure Notifications

Configure Slack/Discord webhook for:
- E2E test failures
- Release failures
- Security vulnerabilities
