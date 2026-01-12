# Docker Deployment Guide

This guide covers deploying the Gmail MCP using Docker for both development and production.

## Quick Start

### Run with Docker (Simplest)

```bash
# Pull and run
docker run -d \
  --name gmail-mcp \
  -e GMAIL_MCP_GOOGLE_CLIENT_ID="your-client-id" \
  -e GMAIL_MCP_GOOGLE_CLIENT_SECRET="your-client-secret" \
  -e GMAIL_MCP_ENCRYPTION_KEY="your-encryption-key" \
  -v gmail_data:/app/data \
  ghcr.io/yourorg/gmail-multi-user-mcp:latest
```

### Run with Docker Compose (Recommended)

1. Create a `.env` file:
```bash
# .env
GMAIL_MCP_GOOGLE_CLIENT_ID=your-client-id
GMAIL_MCP_GOOGLE_CLIENT_SECRET=your-client-secret
GMAIL_MCP_ENCRYPTION_KEY=your-32-byte-base64-key
GMAIL_MCP_LOG_LEVEL=INFO
```

2. Run:
```bash
docker-compose up -d
```

## Development Setup

### Build Locally

```bash
# Clone the repo
git clone https://github.com/yourorg/gmail-multi-user-mcp
cd gmail-multi-user-mcp

# Build the image
docker build -t gmail-mcp:local .

# Run
docker run -d \
  --name gmail-mcp \
  -e GMAIL_MCP_GOOGLE_CLIENT_ID="..." \
  -e GMAIL_MCP_GOOGLE_CLIENT_SECRET="..." \
  -e GMAIL_MCP_ENCRYPTION_KEY="..." \
  gmail-mcp:local
```

### Using Docker Compose for Development

```bash
# Start services
docker-compose up

# View logs
docker-compose logs -f gmail-mcp

# Stop
docker-compose down
```

### Development with Hot Reload

For active development, mount your source code:

```bash
docker run -it \
  --name gmail-mcp-dev \
  -v $(pwd)/gmail_multi_user:/app/gmail_multi_user:ro \
  -v $(pwd)/gmail_mcp_server:/app/gmail_mcp_server:ro \
  -e GMAIL_MCP_GOOGLE_CLIENT_ID="..." \
  -e GMAIL_MCP_GOOGLE_CLIENT_SECRET="..." \
  -e GMAIL_MCP_ENCRYPTION_KEY="..." \
  gmail-mcp:local \
  gmail-mcp serve --reload
```

## Production Setup

### Using Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Variables for Production

Create a secure `.env` file (or use secrets manager):

```bash
# Required
GMAIL_MCP_GOOGLE_CLIENT_ID=your-production-client-id
GMAIL_MCP_GOOGLE_CLIENT_SECRET=your-production-secret
GMAIL_MCP_ENCRYPTION_KEY=production-encryption-key

# Storage (Supabase for production)
GMAIL_MCP_STORAGE_TYPE=supabase
GMAIL_MCP_STORAGE_SUPABASE_URL=https://xxx.supabase.co
GMAIL_MCP_STORAGE_SUPABASE_KEY=your-service-role-key

# Logging
GMAIL_MCP_LOG_LEVEL=WARNING
GMAIL_MCP_LOG_FORMAT=json

# OAuth redirect
GMAIL_MCP_GOOGLE_REDIRECT_URI=https://your-domain.com/oauth/callback
```

### With HTTP Transport (REST API)

To expose the MCP as an HTTP API:

```bash
docker-compose --profile http up -d
```

This starts the server on port 8080.

## Deployment Configurations

### Basic (SQLite, Single Server)

Good for: Small deployments, < 100 users

```yaml
# docker-compose.yml
services:
  gmail-mcp:
    image: ghcr.io/yourorg/gmail-multi-user-mcp:latest
    environment:
      - GMAIL_MCP_STORAGE_TYPE=sqlite
      - GMAIL_MCP_STORAGE_SQLITE_PATH=/app/data/gmail.db
    volumes:
      - gmail_data:/app/data
```

### Production (Supabase, Multiple Servers)

Good for: Scaling, > 100 users

```yaml
# docker-compose.prod.yml
services:
  gmail-mcp:
    image: ghcr.io/yourorg/gmail-multi-user-mcp:latest
    deploy:
      replicas: 3
    environment:
      - GMAIL_MCP_STORAGE_TYPE=supabase
      - GMAIL_MCP_STORAGE_SUPABASE_URL=${SUPABASE_URL}
      - GMAIL_MCP_STORAGE_SUPABASE_KEY=${SUPABASE_KEY}
```

## Kubernetes Deployment

### Basic Deployment

```yaml
# k8s/deployment.yaml
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
        image: ghcr.io/yourorg/gmail-multi-user-mcp:latest
        ports:
        - containerPort: 8080
        env:
        - name: GMAIL_MCP_GOOGLE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: gmail-mcp-secrets
              key: client-id
        - name: GMAIL_MCP_GOOGLE_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: gmail-mcp-secrets
              key: client-secret
        - name: GMAIL_MCP_ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: gmail-mcp-secrets
              key: encryption-key
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
        livenessProbe:
          exec:
            command: ["gmail-mcp", "health"]
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          exec:
            command: ["gmail-mcp", "health"]
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: gmail-mcp-secrets
type: Opaque
stringData:
  client-id: "your-client-id"
  client-secret: "your-client-secret"
  encryption-key: "your-encryption-key"
```

### Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: gmail-mcp
spec:
  selector:
    app: gmail-mcp
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

## Health Checks

### Docker Health Check

The container includes a health check:

```bash
# Check health
docker inspect --format='{{.State.Health.Status}}' gmail-mcp

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' gmail-mcp
```

### Manual Health Check

```bash
# Inside container
docker exec gmail-mcp gmail-mcp health

# HTTP endpoint (if using HTTP transport)
curl http://localhost:8080/health
```

## Logging

### View Logs

```bash
# All logs
docker logs gmail-mcp

# Follow logs
docker logs -f gmail-mcp

# Last 100 lines
docker logs --tail 100 gmail-mcp
```

### Log Format

Default is JSON for easy parsing:

```json
{"timestamp": "2024-01-15T10:30:00Z", "level": "INFO", "message": "Search completed", "user_id": "user_123", "results": 10}
```

### Log Aggregation

For production, send logs to your aggregation service:

```yaml
# docker-compose.yml
services:
  gmail-mcp:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Or use a logging driver like `fluentd`, `gelf`, or `awslogs`.

## Volumes and Persistence

### SQLite Data

```yaml
volumes:
  gmail_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/on/host/gmail_data
```

### Backup

```bash
# Backup SQLite database
docker cp gmail-mcp:/app/data/gmail.db ./backup/gmail.db

# Restore
docker cp ./backup/gmail.db gmail-mcp:/app/data/gmail.db
```

## Security Considerations

### Non-Root User

The container runs as non-root user `gmailmcp` (UID 1000).

### Read-Only Filesystem

For extra security, mount the filesystem as read-only:

```yaml
services:
  gmail-mcp:
    read_only: true
    tmpfs:
      - /tmp
    volumes:
      - gmail_data:/app/data
```

### Network Isolation

```yaml
services:
  gmail-mcp:
    networks:
      - internal
    # Don't expose ports unless needed
    
networks:
  internal:
    internal: true
```

### Secrets Management

Never put secrets in docker-compose files. Use:

1. **Environment files** (`.env`) - for development
2. **Docker secrets** - for Swarm
3. **External secrets manager** - for production (Vault, AWS Secrets Manager)

```yaml
services:
  gmail-mcp:
    secrets:
      - gmail_client_secret
      - gmail_encryption_key

secrets:
  gmail_client_secret:
    external: true
  gmail_encryption_key:
    external: true
```

## Troubleshooting Docker Issues

### Container Won't Start

```bash
# Check logs
docker logs gmail-mcp

# Common causes:
# 1. Missing environment variables
# 2. Port already in use
# 3. Volume permission issues
```

### Permission Denied

```bash
# Fix volume permissions
sudo chown -R 1000:1000 /path/to/gmail_data
```

### Can't Connect to Server

```bash
# Check container is running
docker ps

# Check port mapping
docker port gmail-mcp

# Test from inside container
docker exec gmail-mcp curl -s http://localhost:8080/health
```

### Out of Memory

```yaml
# Increase memory limit
services:
  gmail-mcp:
    deploy:
      resources:
        limits:
          memory: 1G
```

## Next Steps

- [Production Agent Setup](03-production-agent-setup.md)
- [Troubleshooting](05-troubleshooting.md)
