# Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 10GB+ disk space

## Quick Start with Docker Compose

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd coding-agent

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
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
# API Health Check
curl http://localhost:8000/api/v1/health

# Memgraph Lab UI
open http://localhost:3000

# Jaeger Tracing UI
open http://localhost:16686

# Flower (Celery Monitoring)
open http://localhost:5555

# RabbitMQ Management
open http://localhost:15672  # guest/guest
```

### 4. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Service URLs

| Service      | URL                        | Purpose              |
| ------------ | -------------------------- | -------------------- |
| API          | http://localhost:8000      | REST API & WebSocket |
| API Docs     | http://localhost:8000/docs | Swagger UI           |
| Memgraph Lab | http://localhost:3000      | Knowledge Graph UI   |
| Jaeger       | http://localhost:16686     | Distributed Tracing  |
| Flower       | http://localhost:5555      | Celery Monitoring    |
| RabbitMQ     | http://localhost:15672     | Message Broker UI    |

## Production Deployment

### Kubernetes Deployment

#### 1. Create Namespace

```bash
kubectl create namespace coding-agent
```

#### 2. Create Secrets

```bash
kubectl create secret generic coding-agent-secrets \
  --from-literal=jwt-secret=<your-secret> \
  --from-literal=openai-api-key=<your-key> \
  -n coding-agent
```

#### 3. Deploy Services

```bash
kubectl apply -f kubernetes/ -n coding-agent
```

#### 4. Check Status

```bash
kubectl get pods -n coding-agent
kubectl get services -n coding-agent
```

### Cloud Platforms

#### AWS ECS

```bash
# Build and push image
docker build -t coding-agent:latest .
docker tag coding-agent:latest <ecr-repo>:latest
docker push <ecr-repo>:latest

# Deploy with ECS CLI
ecs-cli compose --file docker-compose.yml up
```

#### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/<project-id>/coding-agent
gcloud run deploy coding-agent \
  --image gcr.io/<project-id>/coding-agent \
  --platform managed \
  --region us-central1
```

#### Azure Container Instances

```bash
# Create resource group
az group create --name coding-agent-rg --location eastus

# Deploy container
az container create \
  --resource-group coding-agent-rg \
  --name coding-agent \
  --image <acr-repo>/coding-agent:latest \
  --ports 8000
```

## Environment Variables

### Required

```bash
# LLM Provider (at least one)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...

# JWT Secret
JWT_SECRET_KEY=<strong-random-key>
```

### Optional

```bash
# Memgraph
MEMGRAPH_HOST=localhost
MEMGRAPH_PORT=7687

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Jaeger
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
```

## Scaling

### Horizontal Scaling

```bash
# Scale Celery workers
docker-compose up -d --scale celery-worker=4

# Kubernetes
kubectl scale deployment celery-worker --replicas=4 -n coding-agent
```

### Auto-scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Monitoring

### Prometheus Setup

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "coding-agent"
    static_configs:
      - targets: ["api:8000"]
```

### Grafana Dashboard

Import dashboard from `monitoring/grafana-dashboard.json`

## Backup & Recovery

### Database Backup

```bash
# Backup SQLite database
docker-compose exec api tar -czf /tmp/backup.tar.gz /app/data/conversations.db

# Copy to host
docker cp coding-agent-api:/tmp/backup.tar.gz ./backup.tar.gz
```

### Memgraph Backup

```bash
# Create snapshot
docker-compose exec memgraph mgconsole -e "CREATE SNAPSHOT;"

# Copy snapshot
docker cp coding-agent-memgraph:/var/lib/memgraph/snapshots ./memgraph-backup/
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Check health
docker-compose ps
```

### Connection Issues

```bash
# Test connectivity
docker-compose exec api ping memgraph
docker-compose exec api ping redis
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Scale workers
docker-compose up -d --scale celery-worker=4
```

## Security Checklist

- [ ] Change default JWT secret
- [ ] Use strong passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up VPC/network isolation
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Secrets management (Vault)
- [ ] API rate limiting
- [ ] Input validation

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Clean Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

## Support

For issues and questions:

- Check logs: `docker-compose logs -f`
- Review documentation: `/docs`
- Check health: `curl http://localhost:8000/api/v1/health`
