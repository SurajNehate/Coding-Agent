# Production Setup Guide

## Overview

This guide will help you set up the production-ready AI coding agent with:

- **PostgreSQL** for conversation memory
- **Neo4j** for knowledge graph
- **Milvus** for vector embeddings (RAG)
- **FastAPI** for API gateway
- **Celery** for async tasks
- **Jaeger** for distributed tracing

---

## Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.11+
- **uv** or **pip** for package management
- 8GB+ RAM
- 20GB+ disk space

---

## Quick Start (Docker)

### 1. Clone and Configure

```bash
cd c:\WorkSpace\POC\AI\coding-agent

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
notepad .env
```

**Required environment variables:**

```bash
OPENAI_API_KEY=sk-...  # or GOOGLE_API_KEY or ANTHROPIC_API_KEY
NEO4J_PASSWORD=password  # Change this!
JWT_SECRET_KEY=your-strong-random-secret-key  # Change this!
```

### 2. Start All Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Verify Services

```bash
# API Health
curl http://localhost:8000/api/v1/health

# Check individual services
docker-compose ps
```

**Service URLs:**
| Service | URL | Purpose |
|---------|-----|---------|
| API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Neo4j Browser | http://localhost:7474 | Knowledge Graph UI |
| Jaeger | http://localhost:16686 | Distributed Tracing |
| Flower | http://localhost:5555 | Celery Monitoring |

---

## Local Development Setup

### 1. Install Dependencies

Using **uv** (recommended):

```bash
# Install uv if not already installed
pip install uv

# Install dependencies
uv pip install -r requirements.txt
```

Using **pip**:

```bash
pip install -r requirements.txt
```

### 2. Start Infrastructure Services

```bash
# Start only databases (not the app)
docker-compose up -d postgres neo4j milvus etcd minio redis jaeger
```

### 3. Initialize Databases

```bash
# PostgreSQL will auto-create tables on first run
# Neo4j is ready to use
# Milvus will auto-create collections
```

### 4. Run the Agent

```bash
# CLI mode
python -m src.cli run "Analyze this codebase" --provider openai

# API mode
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Celery worker
celery -A src.tasks.celery_app worker --loglevel=info
```

---

## Configuration

### Environment Variables

**Core LLM:**

```bash
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...
DEFAULT_LLM_PROVIDER=openai  # or google, anthropic
```

**PostgreSQL:**

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/coding_agent
```

**Neo4j:**

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password  # CHANGE THIS!
```

**Milvus:**

```bash
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

**Celery:**

```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**API Security:**

```bash
JWT_SECRET_KEY=your-strong-random-secret-key  # CHANGE THIS!
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Tracing:**

```bash
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
```

---

## Usage Examples

### 1. CLI Usage

```bash
# Run a task
python -m src.cli run "Find all TODO comments in the code"

# With specific provider
python -m src.cli run "Refactor this function" --provider google

# With RAG disabled
python -m src.cli run "Explain this code" --use-rag false

# List sessions
python -m src.cli list-sessions --user-id myuser

# Initialize RAG
python -m src.cli init-rag --docs-dir ./docs

# View metrics
python -m src.cli metrics
```

### 2. API Usage

**Get Token:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=admin&password=admin"
```

**Submit Task:**

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze code quality",
    "user_id": "john",
    "provider": "openai"
  }'
```

**Build Knowledge Graph:**

```bash
curl -X POST http://localhost:8000/api/v1/graph/build \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"project_path": "."}'
```

**Query Knowledge Graph:**

```bash
curl -X POST http://localhost:8000/api/v1/graph/query \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query_type": "usages",
    "target": "main"
  }'
```

### 3. Python API

```python
from src.middleware.knowledge_graph import knowledge_graph
from src.middleware.rag import rag_system
from src.middleware.memory import memory_manager

# Build knowledge graph
stats = knowledge_graph.build_graph_from_directory(".")
print(f"Analyzed {stats['files']} files")

# Find function usages
usages = knowledge_graph.find_function_usages("process_data")
for usage in usages:
    print(f"{usage['caller']} calls {usage['callee']}")

# Add documents to RAG
docs = rag_system.load_documents_from_directory("./docs")
rag_system.add_documents(docs)

# Search RAG
results = rag_system.search("How to deploy?", k=3)
for doc in results:
    print(doc.page_content)

# Create session
session = memory_manager.create_session("session-123", "user-1")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER / CLIENT                         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI API Gateway (Port 8000)             │
│  • JWT Authentication                                    │
│  • REST + WebSocket                                      │
└───────────┬───────────────────────────┬─────────────────┘
            │                           │
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────────┐
│  Celery + Redis       │   │  Data Layer               │
│  • Async Tasks        │   │  • PostgreSQL (Memory)    │
│  • Background Jobs    │   │  • Neo4j (Knowledge)      │
│  • Flower UI          │   │  • Milvus (Vectors)       │
└───────────┬───────────┘   └───────────┬───────────────┘
            │                           │
            └───────────┬───────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  Agent Execution                         │
│  • LLM Processing                                        │
│  • Tool Execution                                        │
│  • Knowledge Graph Queries                               │
│  • RAG Context Enhancement                               │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Observability (Jaeger + Langfuse)           │
└─────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>

# Rebuild
docker-compose up -d --build
```

### Connection Errors

**PostgreSQL:**

```bash
# Test connection
docker-compose exec postgres psql -U postgres -d coding_agent -c "SELECT 1"
```

**Neo4j:**

```bash
# Test connection
docker-compose exec neo4j cypher-shell -u neo4j -p password "RETURN 1"
```

**Milvus:**

```bash
# Check health
curl http://localhost:9091/healthz
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or with uv
uv pip install -r requirements.txt --reinstall
```

### Memory Issues

```bash
# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > 8GB+

# Or reduce worker concurrency
# In docker-compose.yml: --concurrency=2
```

---

## Production Deployment

### 1. Update Secrets

```bash
# Generate strong secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env
JWT_SECRET_KEY=<generated-secret>
NEO4J_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>
```

### 2. Configure Scaling

```bash
# Scale Celery workers
docker-compose up -d --scale celery-worker=4
```

### 3. Enable HTTPS

Use a reverse proxy (nginx, Traefik) with SSL certificates.

### 4. Backup Strategy

```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U postgres coding_agent > backup.sql

# Neo4j backup
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j.dump

# Milvus backup
# Use Milvus backup tool or volume snapshots
```

---

## Monitoring

### Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/api/v1/metrics

# Celery tasks
open http://localhost:5555
```

### Tracing

```bash
# Jaeger UI
open http://localhost:16686

# Langfuse (if configured)
open https://cloud.langfuse.com
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Follow logs
docker-compose logs -f --tail=100 api
```

---

## Stopping Services

```bash
# Stop all
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Stop specific service
docker-compose stop api
```

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure .env
3. ✅ Start services
4. ✅ Verify health
5. 📊 Build knowledge graph
6. 📚 Initialize RAG with docs
7. 🧪 Test API endpoints
8. 🚀 Deploy to production

---

## Support

- **Documentation**: See `docs/` directory
- **API Reference**: http://localhost:8000/docs
- **Issues**: Check logs with `docker-compose logs`
- **Health Check**: `curl http://localhost:8000/api/v1/health`

**You're all set! 🎉**
