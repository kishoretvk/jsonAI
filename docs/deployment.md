# JsonAI Production Deployment Guide

This guide covers deploying JsonAI in production environments with Docker, Kubernetes, and cloud platforms.

## Quick Start

### Docker Deployment

1. **Build the Docker image:**
```bash
docker build -t jsonai:latest .
```

2. **Run with Docker Compose:**
```bash
docker-compose up -d
```

3. **Access the API:**
- REST API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Production Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   JsonAI API    │────│   Ollama/LLM    │
│   (nginx/traefik)│    │   (FastAPI)     │    │   Backend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │   Redis Cache   │    │   Prometheus    │
│   (Static)      │    │   (Optional)    │    │   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Environment Configuration

### Environment Variables

Create a `.env` file:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Model Configuration
DEFAULT_MODEL=ollama
OLLAMA_HOST=http://localhost:11434
OPENAI_API_KEY=your_openai_key_here

# Cache Configuration
CACHE_TTL=3600
CACHE_SIZE=1000
REDIS_URL=redis://localhost:6379

# Performance
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security
API_KEY_REQUIRED=false
CORS_ORIGINS=*
```

### Docker Compose Production

```yaml
version: '3.8'

services:
  jsonai-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_WORKERS=4
      - CACHE_TTL=3600
      - MAX_CONCURRENT_REQUESTS=10
    volumes:
      - ./models:/app/models
    restart: unless-stopped
    depends_on:
      - redis
      - ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    environment:
      - OLLAMA_HOST=0.0.0.0

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - jsonai-api
    restart: unless-stopped

volumes:
  ollama_data:
  redis_data:
```

## Kubernetes Deployment

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: jsonai-config
data:
  API_WORKERS: "4"
  CACHE_TTL: "3600"
  MAX_CONCURRENT_REQUESTS: "10"
  LOG_LEVEL: "INFO"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jsonai-api
  labels:
    app: jsonai-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jsonai-api
  template:
    metadata:
      labels:
        app: jsonai-api
    spec:
      containers:
      - name: jsonai-api
        image: jsonai:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: jsonai-config
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: jsonai-service
spec:
  selector:
    app: jsonai-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

## Cloud Platform Deployment

### AWS (ECS/Fargate)

1. **Build and push to ECR:**
```bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
docker build -t jsonai .
docker tag jsonai:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/jsonai:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/jsonai:latest
```

2. **ECS Task Definition:**
```json
{
  "family": "jsonai-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "jsonai-api",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/jsonai:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "API_WORKERS", "value": "4"},
        {"name": "CACHE_TTL", "value": "3600"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/jsonai",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform (Cloud Run)

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: jsonai-api
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/memory: "2Gi"
        run.googleapis.com/cpu: "1000m"
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/jsonai:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_WORKERS
          value: "4"
        - name: CACHE_TTL
          value: "3600"
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### Azure (Container Instances)

```bash
az container create \
  --resource-group jsonai-rg \
  --name jsonai-api \
  --image jsonai:latest \
  --registry-login-server myregistry.azurecr.io \
  --registry-username myregistry \
  --registry-password mypassword \
  --dns-name-label jsonai-api \
  --ports 8000 \
  --memory 2 \
  --cpu 1 \
  --environment-variables \
    API_WORKERS=4 \
    CACHE_TTL=3600
```

## Performance Optimization

### Horizontal Pod Autoscaler (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: jsonai-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: jsonai-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Load Balancing with nginx

```nginx
upstream jsonai_backend {
    least_conn;
    server jsonai-api-1:8000;
    server jsonai-api-2:8000;
    server jsonai-api-3:8000;
}

server {
    listen 80;
    server_name api.jsonai.example.com;

    location / {
        proxy_pass http://jsonai_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}
```

## Monitoring and Observability

### Prometheus Metrics

Add to your deployment:

```yaml
- name: prometheus-exporter
  image: prom/node-exporter:latest
  ports:
  - containerPort: 9100
```

### Health Checks

The API includes comprehensive health checks:

- **Liveness Probe:** `/health` - Basic service health
- **Readiness Probe:** `/health` - Service ready to accept traffic
- **Custom Metrics:** `/stats` - Performance and cache statistics

### Logging Configuration

```python
# In production.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
    format='%(message)s'
)
logging.getLogger().handlers[0].setFormatter(JSONFormatter())
```

## Security Considerations

### API Key Authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/generate")
@limiter.limit("10/minute")
async def generate_json(request: Request, generation_request: GenerationRequest):
    # ... implementation
```

### SSL/TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.jsonai.example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
}
```

## Backup and Disaster Recovery

### Database Backup

```bash
# Redis backup
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb ./backup/redis-$(date +%Y%m%d).rdb

# Model backup
tar -czf models-backup-$(date +%Y%m%d).tar.gz ./models/
```

### Recovery Procedures

1. **Service Recovery:**
```bash
# Restore from backup
kubectl apply -f k8s/
kubectl rollout restart deployment/jsonai-api
```

2. **Data Recovery:**
```bash
# Restore Redis data
docker cp ./backup/redis-latest.rdb redis:/data/dump.rdb
docker restart redis
```

## Troubleshooting

### Common Issues

1. **Out of Memory:**
   - Increase container memory limits
   - Reduce cache sizes
   - Monitor memory usage with `/stats`

2. **Slow Response Times:**
   - Check model loading times
   - Optimize cache settings
   - Scale horizontally

3. **Connection Timeouts:**
   - Increase proxy timeouts
   - Check network connectivity
   - Monitor LLM backend health

### Debug Mode

Enable debug mode for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export API_DEBUG=true
```

Access debug endpoints:
- `/stats` - Performance statistics
- `/health` - Health status
- `/docs` - API documentation

## Cost Optimization

### Resource Management

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

### Spot Instances (AWS)

```yaml
nodeSelector:
  kubernetes.io/lifecycle: spot
tolerations:
- key: "spot"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```

### Auto-scaling Policies

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300
    policies:
    - type: Percent
      value: 50
      periodSeconds: 60
  scaleUp:
    stabilizationWindowSeconds: 60
    policies:
    - type: Percent
      value: 100
      periodSeconds: 15
```
