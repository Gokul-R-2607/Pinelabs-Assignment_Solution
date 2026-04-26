# Pine Labs Payment Reconciliation - Deployment Guide

**Version:** 2.0.0  
**Last Updated:** April 26, 2026  
**Status:** Production-Ready

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment Options](#cloud-deployment-options)
4. [Production Configuration](#production-configuration)
5. [Monitoring & Logging](#monitoring--logging)
6. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites

```bash
# Check Python version
python3 --version  # Must be 3.9+

# Check pip version
pip3 --version

# Verify git is installed
git --version
```

### Step 1: Clone Repository

```bash
git clone https://github.com/pinelabs/payment-reconciliation.git
cd payment-reconciliation
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Generated requirements.txt:**
```
fastapi==0.104.1
sqlalchemy==2.0.23
pydantic==2.5.0
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
psycopg2-binary==2.9.9  # For PostgreSQL
```

### Step 4: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env for your local setup
cat .env
```

**Sample .env (Development):**
```bash
# Core Settings
ENV=development
DEBUG=True
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=sqlite:///./pinelabs_dev.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_FORMAT=json
```

### Step 5: Initialize Database

```bash
# Create database and tables
python3 -m app.models

# Or using direct SQLAlchemy
python3 << 'EOF'
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
print("✓ Database initialized successfully")
EOF
```

### Step 6: Load Sample Data

```bash
# Generate 10,000 sample events across 5 merchants
python3 -m app.scripts.generate_sample_data --merchants 5 --events 10000

# Or custom configuration
python3 -m app.scripts.generate_sample_data \
  --merchants 10 \
  --events 50000 \
  --date-range "2026-01-01:2026-04-26"
```

### Step 7: Start Development Server

```bash
# Basic start
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# With auto-reload (recommended for development)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# With detailed logging
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

**Verify Installation:**
```bash
# In another terminal
curl http://localhost:8000/docs

# Should return Swagger UI HTML
```

---

## Docker Deployment

### Option 1: Docker Single Container

#### Build Docker Image

```bash
docker build -t pinelabs-payment-reconciliation:latest .
```

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Run Container Locally

```bash
docker run -d \
  --name pinelabs-api \
  -p 8000:8000 \
  -e DATABASE_URL="sqlite:///./data/pinelabs.db" \
  -e ENV="development" \
  -v $(pwd)/data:/app/data \
  pinelabs-payment-reconciliation:latest
```

#### Check Logs

```bash
docker logs -f pinelabs-api

# Clear logs
docker logs --tail 100 pinelabs-api
```

#### Stop Container

```bash
docker stop pinelabs-api
docker rm pinelabs-api
```

---

### Option 2: Docker Compose (Multi-Service)

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: pinelabs-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://pinelabs:securepassword123@db:5432/pinelabs_db
      - ENV=production
      - DEBUG=False
      - LOG_LEVEL=INFO
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  db:
    image: postgres:15-alpine
    container_name: pinelabs-db
    environment:
      - POSTGRES_USER=pinelabs
      - POSTGRES_PASSWORD=securepassword123
      - POSTGRES_DB=pinelabs_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pinelabs"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Start All Services

```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Stop and remove volumes (full cleanup)
docker-compose down -v
```

---

## Cloud Deployment Options

### Option 1: Railway.app (Easiest)

#### Prerequisites
- Railway.app account (https://railway.app)
- GitHub repository with code

#### Step 1: Connect Repository

```bash
# Login to Railway
railway login

# Initialize project
railway init

# Link to GitHub (Web UI preferred)
```

#### Step 2: Configure Services

**Via Web UI:**
1. Click "Create New"
2. Select "PostgreSQL"
3. Click "Deploy" on Python service
4. Connect your GitHub repo

#### Step 3: Environment Variables

**In Railway Dashboard:**
```
DATABASE_URL = postgresql://user:pass@host:5432/pinelabs_db
ENV = production
DEBUG = False
LOG_LEVEL = INFO
```

#### Step 4: Deploy

```bash
# Automatic deployment on git push
git push origin main

# Or manual deployment
railway up
```

**Monitor Deployment:**
```
https://railway.app/project/[PROJECT_ID]/deployments
```

---

### Option 2: Render

#### Prerequisites
- Render.com account (https://render.com)
- GitHub repository

#### Step 1: Create Web Service

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Configure:
   - **Name:** pinelabs-payment-reconciliation
   - **Runtime:** Python 3.9
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`

#### Step 2: Add Database

1. Click "New +" → "PostgreSQL"
2. Configure database name: `pinelabs_db`
3. Note the connection string

#### Step 3: Set Environment Variables

**In Render Dashboard:**
```
DATABASE_URL = [from PostgreSQL service]
ENV = production
DEBUG = False
```

#### Step 4: Deploy

```bash
git push origin main
```

**Service URL:** https://pinelabs-payment-reconciliation.onrender.com

---

### Option 3: AWS ECS (Advanced)

#### Prerequisites
- AWS Account
- AWS CLI configured
- Docker image built

#### Step 1: Push to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name pinelabs-payment-reconciliation

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag pinelabs-payment-reconciliation:latest \
  [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/pinelabs-payment-reconciliation:latest

# Push image
docker push [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/pinelabs-payment-reconciliation:latest
```

#### Step 2: Create ECS Task Definition

```bash
# Use provided task-definition.json
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json
```

#### Step 3: Create ECS Service

```bash
aws ecs create-service \
  --cluster production \
  --service-name pinelabs-api \
  --task-definition pinelabs-payment-reconciliation:1 \
  --desired-count 3 \
  --load-balancers targetGroupArn=[ALB_TARGET_GROUP],containerName=api,containerPort=8000
```

---

## Production Configuration

### Environment Variables

**Production .env:**
```bash
# Core
ENV=production
DEBUG=False
LOG_LEVEL=INFO

# Database (RDS PostgreSQL)
DATABASE_URL=postgresql://[USER]:[PASSWORD]@[RDS_ENDPOINT]:5432/pinelabs_prod
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_PRE_PING=True

# Security
SECRET_KEY=[generate-with-secrets.token_urlsafe(32)]
ALLOWED_HOSTS=api.pinelabs.com,api-backup.pinelabs.com

# API
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4

# Logging
LOG_FORMAT=json
LOG_FILE=/var/log/pinelabs/api.log

# Monitoring
SENTRY_DSN=https://[key]@sentry.io/[project-id]
DATADOG_API_KEY=[your-key]

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_PERIOD=60

# Cache
REDIS_URL=redis://[ENDPOINT]:6379/0
CACHE_TTL=300
```

### Database Setup (PostgreSQL)

```sql
-- Create database
CREATE DATABASE pinelabs_prod;

-- Create user
CREATE USER pinelabs_app WITH PASSWORD 'SECURE_PASSWORD_HERE';

-- Grant permissions
GRANT CONNECT ON DATABASE pinelabs_prod TO pinelabs_app;
GRANT CREATE ON DATABASE pinelabs_prod TO pinelabs_app;

-- Connect to database
\c pinelabs_prod

-- Create tables (auto-created by SQLAlchemy)
-- Run migration script

-- Create indexes for performance
CREATE INDEX idx_transaction_merchant_status 
  ON transactions(merchant_id, status);

CREATE INDEX idx_transaction_created_date 
  ON transactions(DATE(created_at), status);

CREATE INDEX idx_event_transaction_timestamp 
  ON events(transaction_id, timestamp);

-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 100;  -- Log queries > 100ms
SELECT pg_reload_conf();
```

### Load Balancer Configuration (nginx)

**nginx.conf:**
```nginx
upstream pinelabs_api {
    least_conn;
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

server {
    listen 80;
    server_name api.pinelabs.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.pinelabs.com;

    # SSL Certificates
    ssl_certificate /etc/nginx/ssl/api.pinelabs.com.crt;
    ssl_certificate_key /etc/nginx/ssl/api.pinelabs.com.key;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req zone=api_limit burst=200;

    # Proxy Configuration
    location / {
        proxy_pass http://pinelabs_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health Check Endpoint
    location /health {
        proxy_pass http://pinelabs_api;
        access_log off;
    }
}
```

---

## Monitoring & Logging

### Application Monitoring

#### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-26T10:00:00Z",
  "database": "connected",
  "version": "2.0.0"
}
```

#### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

**Prometheus Format:**
```
# HELP pinelabs_events_processed_total Total events processed
# TYPE pinelabs_events_processed_total counter
pinelabs_events_processed_total{status="success"} 42857

# HELP pinelabs_api_response_time_seconds API response time
# TYPE pinelabs_api_response_time_seconds histogram
pinelabs_api_response_time_seconds_bucket{le="0.05",endpoint="/events"} 2145
```

### Structured Logging

**Log Output Example:**
```json
{
  "timestamp": "2026-04-26T10:30:45.123Z",
  "level": "INFO",
  "service": "pinelabs-payment-reconciliation",
  "version": "2.0.0",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "endpoint": "POST /events",
  "merchant_id": "merchant_001",
  "transaction_id": "tx-42857",
  "event_id": "evt-0985",
  "duration_ms": 45,
  "status": "created",
  "http_status": 201
}
```

### Log Aggregation (ELK Stack)

```bash
# Push logs to Elasticsearch
pip install python-logstash-async

# Configure in Python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
handler = logging.FileHandler('api.log')
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Monitoring Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Prometheus** | Metrics collection | Scrape `/metrics` endpoint |
| **Grafana** | Metrics visualization | Dashboard for API metrics |
| **ELK Stack** | Log aggregation | Filebeat → Logstash → Elasticsearch |
| **Sentry** | Error tracking | Capture exceptions |
| **DataDog** | APM & Infrastructure | Agent installation |

---

## Troubleshooting

### Database Connection Issues

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Test connection
psql -h localhost -U pinelabs -d pinelabs_db

# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:5432/dbname

# Check firewall
sudo ufw allow 5432
```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
python3 -m uvicorn app.main:app --port 8001
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Verify virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify installation
python3 -c "import fastapi; print(fastapi.__version__)"
```

### Database Migration Issues

**Error:** `Operational Error: CREATE TABLE`

**Solution:**
```bash
# Recreate database from scratch
rm pinelabs_reconciliation.db

# Reinitialize
python3 << 'EOF'
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
EOF
```

### API Not Responding

**Debug Steps:**
```bash
# Check if service is running
curl http://localhost:8000/health

# Check logs
tail -f /var/log/pinelabs/api.log

# Check resource usage
top
df -h
free -h

# Restart service
systemctl restart pinelabs-api
```

---

## Performance Tuning

### Database Connection Pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False
)
```

### Uvicorn Workers

```bash
# For CPU-bound: workers = (2 × CPU_CORES) + 1
# For I/O-bound: workers = CPU_CORES × 4

# Example for 4-core machine (I/O-bound API)
python3 -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 16
```

### Query Optimization

```python
# Use selectinload for relationships
from sqlalchemy.orm import selectinload

transactions = db.query(Transaction).options(
    selectinload(Transaction.events)
).filter(...).all()
```

---

**Document Version:** 2.0.0  
**Last Updated:** April 26, 2026  
**Maintained By:** Pine Labs DevOps Team
