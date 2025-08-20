# Docker Setup Guide

This guide provides instructions for running the Course Materials RAG System using Docker.

## Prerequisites

- Docker Engine 20.10+ 
- Docker Compose 2.0+
- An Anthropic API key

## Quick Start

### 1. Environment Setup

Copy the example environment file and add your API key:

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Build and Run

#### Production Mode

```bash
# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at `http://localhost:8000`

#### Development Mode

Development mode includes hot-reloading for code changes:

```bash
# Start with development configuration
docker-compose up

# Or explicitly use both files
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

## Architecture Overview

### Production Setup

- **Multi-stage build**: Reduces final image size (~200MB)
- **Non-root user**: Runs as `appuser` for security
- **Health checks**: Monitors application availability
- **Resource limits**: Memory constraints to prevent runaway processes
- **Volume persistence**: ChromaDB data persists across restarts

### Development Setup

- **Hot-reloading**: Code changes reflect immediately
- **Source mounting**: Local files mounted as read-only volumes
- **Debug mode**: Enhanced logging and error reporting

## File Structure

```
.
├── Dockerfile              # Production multi-stage build
├── Dockerfile.dev          # Development build with tools
├── docker-compose.yml      # Production orchestration
├── docker-compose.override.yml  # Development overrides
├── .dockerignore          # Build exclusions
└── .env.example           # Environment template
```

## Commands Reference

### Building Images

```bash
# Build production image
docker build -t rag-chatbot:latest .

# Build development image
docker build -f Dockerfile.dev -t rag-chatbot:dev .

# Build with docker-compose
docker-compose build

# Force rebuild without cache
docker-compose build --no-cache
```

### Container Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart services
docker-compose restart

# View running containers
docker-compose ps

# Execute commands in container
docker-compose exec rag-backend bash

# View logs
docker-compose logs -f rag-backend
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect ChromaDB volume
docker volume inspect starting-ragchatbot-codebase_chroma_data

# Backup ChromaDB data
docker run --rm -v starting-ragchatbot-codebase_chroma_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/chroma-backup.tar.gz -C /data .

# Restore ChromaDB data
docker run --rm -v starting-ragchatbot-codebase_chroma_data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/chroma-backup.tar.gz -C /data
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `ANTHROPIC_API_KEY`: Required for AI generation
- `APP_PORT`: Application port (default: 8000)
- `CHUNK_SIZE`: Document chunk size (default: 800)
- `MAX_RESULTS`: Maximum search results (default: 5)

### Resource Limits

Adjust in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 2G      # Maximum memory
    reservations:
      memory: 512M    # Minimum guaranteed memory
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs rag-backend

# Verify environment variables
docker-compose config

# Check health status
docker inspect rag-backend --format='{{json .State.Health}}'
```

### Permission issues

```bash
# Fix volume permissions
docker-compose exec rag-backend chown -R appuser:appuser /app/data
```

### Memory issues

```bash
# Check memory usage
docker stats rag-backend

# Increase memory limit in docker-compose.yml
```

### ChromaDB issues

```bash
# Reset ChromaDB
docker-compose down -v
docker-compose up -d
```

## Security Considerations

1. **Non-root user**: Application runs as `appuser`
2. **Read-only mounts**: Source code mounted read-only in development
3. **Network isolation**: Services communicate via internal network
4. **Secret management**: Use Docker secrets for production deployments
5. **Image scanning**: Regularly scan images for vulnerabilities

```bash
# Scan image for vulnerabilities
docker scout cves rag-chatbot:latest
```

## Performance Optimization

### Image Size Optimization

- Multi-stage builds reduce final image from ~1GB to ~200MB
- Only production dependencies included
- Minimal base image (python:3.13-slim)

### Build Cache Optimization

- Dependencies copied before source code
- Least-changing files copied first
- Use BuildKit for enhanced caching:

```bash
DOCKER_BUILDKIT=1 docker build .
```

### Runtime Optimization

- Health checks prevent routing to unhealthy containers
- Resource limits prevent memory leaks
- Logging configuration prevents disk filling

## Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml rag-stack

# Scale service
docker service scale rag-stack_rag-backend=3
```

### Using Kubernetes

Convert docker-compose to Kubernetes manifests:

```bash
# Install kompose
curl -L https://github.com/kubernetes/kompose/releases/download/v1.31.2/kompose-linux-amd64 -o kompose

# Convert
./kompose convert

# Deploy
kubectl apply -f .
```

## Monitoring

### Application Metrics

```bash
# CPU and memory usage
docker stats

# Detailed container info
docker inspect rag-backend

# Application logs
docker-compose logs -f --tail=100 rag-backend
```

### Health Monitoring

The application includes a health check endpoint:

```bash
# Check health
curl http://localhost:8000/api/courses

# Monitor health
watch -n 5 'curl -s http://localhost:8000/api/courses'
```

## Backup and Recovery

### Automated Backups

Create a backup script:

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup ChromaDB
docker run --rm \
  -v starting-ragchatbot-codebase_chroma_data:/data \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf /backup/chroma.tar.gz -C /data .

# Backup environment
cp .env "$BACKUP_DIR/.env"

echo "Backup completed to $BACKUP_DIR"
```

### Restore Process

```bash
# Stop services
docker-compose down

# Restore volume
docker run --rm \
  -v starting-ragchatbot-codebase_chroma_data:/data \
  -v ./backups/20240120_120000:/backup \
  alpine tar xzf /backup/chroma.tar.gz -C /data

# Start services
docker-compose up -d
```