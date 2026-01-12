# Deployment Guide

This guide covers deploying gmail-multi-user-mcp in various environments.

## Local Development

### Quick Setup

```bash
# Create config
gmail-mcp init --database sqlite

# Edit config with your OAuth credentials
vim gmail_config.yaml

# Verify
gmail-mcp health

# Run MCP server
gmail-mcp serve
```

### SQLite Storage

SQLite is ideal for local development:

```yaml
storage:
  type: sqlite
  sqlite:
    path: gmail_mcp.db  # Relative or absolute path
```

The database file is created automatically.

---

## Production with Supabase

### Why Supabase?

- PostgreSQL reliability
- Multi-server access
- Built-in backups
- Row Level Security

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your:
   - Project URL: `https://xxx.supabase.co`
   - Service role key: `eyJhbG...` (from Settings > API)

### Step 2: Run Migrations

In Supabase SQL Editor, run `migrations/supabase/001_initial.sql`:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_user_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Connections table
CREATE TABLE IF NOT EXISTS connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gmail_address VARCHAR(255) NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    scopes TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- OAuth states table
CREATE TABLE IF NOT EXISTS oauth_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state VARCHAR(255) NOT NULL UNIQUE,
    user_id VARCHAR(255) NOT NULL,
    scopes TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    code_verifier VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_connections_user_id ON connections(user_id);
CREATE INDEX IF NOT EXISTS idx_connections_gmail_address ON connections(gmail_address);
CREATE INDEX IF NOT EXISTS idx_oauth_states_state ON oauth_states(state);
CREATE INDEX IF NOT EXISTS idx_oauth_states_expires_at ON oauth_states(expires_at);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER connections_updated_at
    BEFORE UPDATE ON connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Step 3: Configure

```yaml
storage:
  type: supabase
  supabase:
    url: "https://xxx.supabase.co"
    key: "eyJhbG..."  # Service role key
```

Or via environment variables:
```bash
export GMAIL_MCP_STORAGE__TYPE=supabase
export GMAIL_MCP_STORAGE__SUPABASE__URL="https://xxx.supabase.co"
export GMAIL_MCP_STORAGE__SUPABASE__KEY="eyJhbG..."
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY gmail_multi_user/ ./gmail_multi_user/
COPY gmail_mcp_server/ ./gmail_mcp_server/

# Config will be mounted or env vars provided
ENV GMAIL_MCP_CONFIG=/config/gmail_config.yaml

EXPOSE 8000

CMD ["gmail-mcp", "serve", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  gmail-mcp:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config:/config:ro
      - ./data:/data
    environment:
      - GMAIL_MCP_CONFIG=/config/gmail_config.yaml
      - GMAIL_MCP_STORAGE__SQLITE__PATH=/data/gmail_mcp.db
    restart: unless-stopped
```

### Run

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f

# Health check
curl http://localhost:8000/health
```

---

## Kubernetes Deployment

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gmail-mcp-secrets
type: Opaque
stringData:
  encryption-key: "your-encryption-key"
  google-client-id: "your-client-id"
  google-client-secret: "your-client-secret"
  supabase-url: "https://xxx.supabase.co"
  supabase-key: "your-service-role-key"
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gmail-mcp-config
data:
  gmail_config.yaml: |
    google:
      redirect_uri: "https://yourdomain.com/oauth/callback"
      scopes:
        - "https://www.googleapis.com/auth/gmail.readonly"
        - "https://www.googleapis.com/auth/gmail.send"
        - "https://www.googleapis.com/auth/gmail.modify"
        - "https://www.googleapis.com/auth/userinfo.email"
    storage:
      type: supabase
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gmail-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gmail-mcp
  template:
    metadata:
      labels:
        app: gmail-mcp
    spec:
      containers:
      - name: gmail-mcp
        image: your-registry/gmail-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: GMAIL_MCP_ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: gmail-mcp-secrets
              key: encryption-key
        - name: GMAIL_MCP_GOOGLE__CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: gmail-mcp-secrets
              key: google-client-id
        - name: GMAIL_MCP_GOOGLE__CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: gmail-mcp-secrets
              key: google-client-secret
        - name: GMAIL_MCP_STORAGE__SUPABASE__URL
          valueFrom:
            secretKeyRef:
              name: gmail-mcp-secrets
              key: supabase-url
        - name: GMAIL_MCP_STORAGE__SUPABASE__KEY
          valueFrom:
            secretKeyRef:
              name: gmail-mcp-secrets
              key: supabase-key
        volumeMounts:
        - name: config
          mountPath: /config
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: gmail-mcp-config
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gmail-mcp
spec:
  selector:
    app: gmail-mcp
  ports:
  - port: 80
    targetPort: 8000
```

---

## Environment Variables Reference

All configuration can be set via environment variables:

| Setting | Environment Variable |
|---------|---------------------|
| encryption_key | `GMAIL_MCP_ENCRYPTION_KEY` |
| google.client_id | `GMAIL_MCP_GOOGLE__CLIENT_ID` |
| google.client_secret | `GMAIL_MCP_GOOGLE__CLIENT_SECRET` |
| google.redirect_uri | `GMAIL_MCP_GOOGLE__REDIRECT_URI` |
| storage.type | `GMAIL_MCP_STORAGE__TYPE` |
| storage.sqlite.path | `GMAIL_MCP_STORAGE__SQLITE__PATH` |
| storage.supabase.url | `GMAIL_MCP_STORAGE__SUPABASE__URL` |
| storage.supabase.key | `GMAIL_MCP_STORAGE__SUPABASE__KEY` |

Note: Use double underscore (`__`) for nested settings.

---

## Security Checklist

### Secrets Management

- [ ] Never commit `gmail_config.yaml` with real credentials
- [ ] Use environment variables or secret management
- [ ] Rotate encryption key if compromised
- [ ] Use separate credentials per environment

### Network Security

- [ ] Use HTTPS in production
- [ ] Restrict network access to MCP server
- [ ] Use firewall rules appropriately

### Database Security

- [ ] Use Supabase Row Level Security (RLS)
- [ ] Restrict database access
- [ ] Enable SSL for database connections

### OAuth Security

- [ ] Use production OAuth credentials
- [ ] Verify redirect URIs are correct
- [ ] Publish app if needed for external users

---

## Monitoring

### Health Check

```bash
gmail-mcp health
```

Or via HTTP (if using http transport):
```bash
curl http://localhost:8000/health
```

### Logs

Enable debug logging:
```bash
gmail-mcp serve --debug
```

### Metrics (Custom)

Add metrics collection in your application:
```python
# Track connection health
for conn in connections:
    status = await gmail_check_connection(connection_id=conn["id"])
    metrics.gauge("gmail_connection_valid", 1 if status["valid"] else 0)
```

---

## Scaling Considerations

### Horizontal Scaling

With Supabase storage, you can run multiple instances:
- All instances share the same database
- Tokens are centrally managed
- No session affinity required

### Rate Limits

Gmail API has rate limits:
- 250 quota units per user per second
- 1,000,000,000 quota units per day per project

Implement rate limiting in your application layer.

### Connection Pooling

For high-traffic scenarios:
- Supabase handles connection pooling
- Consider caching frequently-accessed data (labels, profile)
