# Multi-stage Dockerfile for gmail-multi-user-mcp
# Stage 1: Build
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install pip and build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy only the files needed for installation
COPY pyproject.toml README.md ./
COPY gmail_multi_user/ ./gmail_multi_user/
COPY gmail_mcp_server/ ./gmail_mcp_server/

# Build the wheel
RUN pip wheel --no-deps --wheel-dir /app/wheels .

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd -r gmailmcp && useradd -r -g gmailmcp gmailmcp

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels

# Install the package and dependencies
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Create directories for config and data
RUN mkdir -p /app/config /app/data && \
    chown -R gmailmcp:gmailmcp /app

# Switch to non-root user
USER gmailmcp

# Environment variables
ENV GMAIL_MCP_STORAGE_TYPE=sqlite \
    GMAIL_MCP_STORAGE_SQLITE_PATH=/app/data/gmail_mcp.db \
    GMAIL_MCP_LOG_LEVEL=INFO \
    GMAIL_MCP_LOG_FORMAT=json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD gmail-mcp health || exit 1

# Expose MCP HTTP port (optional, for HTTP transport)
EXPOSE 8080

# Default command - run MCP server with stdio transport
ENTRYPOINT ["gmail-mcp"]
CMD ["serve"]
