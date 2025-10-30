# Production Deployment Guide

Complete guide for deploying the Customer Service Chatbot to production environments.

## Pre-Deployment Checklist

### Security
- [ ] API keys stored in secure secrets manager
- [ ] API authentication enabled (`REQUIRE_API_KEY=true`)
- [ ] CORS configured for production domains
- [ ] HTTPS/TLS configured
- [ ] Rate limiting enabled with Redis
- [ ] Input validation and sanitization
- [ ] Logging configured (no sensitive data logged)

### Performance
- [ ] Vector store optimized (consider Pinecone/Weaviate)
- [ ] Database connection pooling configured
- [ ] Caching implemented (Redis)
- [ ] Load testing completed
- [ ] Auto-scaling rules defined
- [ ] CDN configured for static assets

### Monitoring
- [ ] Health check endpoints tested
- [ ] Logging aggregation setup (CloudWatch/DataDog)
- [ ] Error tracking (Sentry)
- [ ] Metrics collection (Prometheus)
- [ ] Alerting configured
- [ ] API usage monitoring

### Reliability
- [ ] Backup strategy defined
- [ ] Disaster recovery plan
- [ ] Database backups automated
- [ ] Zero-downtime deployment tested
- [ ] Rollback procedure documented

## AWS Deployment

### Option 1: AWS ECS (Fargate)

**Prerequisites:**
- AWS CLI installed and configured
- Docker images pushed to ECR

**Steps:**

1. **Create ECR Repository:**
```bash
aws ecr create-repository --repository-name chatbot-api
aws ecr create-repository --repository-name chatbot-ui
```

2. **Build and Push Docker Images:**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push API
docker build -t chatbot-api .
docker tag chatbot-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/chatbot-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/chatbot-api:latest
```

3. **Create Task Definition:**
```json
{
  "family": "chatbot-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "chatbot-api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/chatbot-api:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "API_HOST", "value": "0.0.0.0"},
        {"name": "API_PORT", "value": "8000"}
      ],
      "secrets": [
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ]
    }
  ]
}
```

4. **Create ECS Service:**
```bash
aws ecs create-service \
  --cluster chatbot-cluster \
  --service-name chatbot-api \
  --task-definition chatbot-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=chatbot-api,containerPort=8000"
```

### Option 2: AWS Lambda (Serverless)

**Using Mangum for FastAPI:**

```python
# lambda_handler.py
from mangum import Mangum
from main import app

handler = Mangum(app)
```

**Deploy with AWS SAM:**
```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  ChatbotFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_handler.handler
      Runtime: python3.11
      Timeout: 30
      MemorySize: 1024
      Environment:
        Variables:
          OPENAI_API_KEY: !Sub '{{resolve:secretsmanager:chatbot-secrets:SecretString:openai_key}}'
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

```bash
sam build
sam deploy --guided
```

### Option 3: AWS Elastic Beanstalk

```bash
# Initialize
eb init -p docker chatbot-api

# Create environment
eb create production

# Deploy updates
eb deploy
```

## Google Cloud Platform (GCP)

### Cloud Run Deployment

**1. Build Container:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/chatbot-api
```

**2. Deploy to Cloud Run:**
```bash
gcloud run deploy chatbot-api \
  --image gcr.io/PROJECT_ID/chatbot-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars COMPANY_NAME="Your Company" \
  --set-secrets OPENAI_API_KEY=chatbot-openai-key:latest \
  --min-instances 1 \
  --max-instances 10 \
  --memory 1Gi \
  --cpu 1
```

**3. Setup Custom Domain:**
```bash
gcloud run domain-mappings create \
  --service chatbot-api \
  --domain api.yourdomain.com \
  --region us-central1
```

### GKE (Kubernetes) Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatbot-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatbot-api
  template:
    metadata:
      labels:
        app: chatbot-api
    spec:
      containers:
      - name: chatbot-api
        image: gcr.io/PROJECT_ID/chatbot-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: chatbot-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: chatbot-api-service
spec:
  type: LoadBalancer
  selector:
    app: chatbot-api
  ports:
  - port: 80
    targetPort: 8000
```

## Azure Deployment

### Azure Container Apps

**1. Create Container Registry:**
```bash
az acr create --resource-group chatbot-rg \
  --name chatbotregistry --sku Basic
```

**2. Build and Push:**
```bash
az acr build --registry chatbotregistry \
  --image chatbot-api:latest .
```

**3. Deploy Container App:**
```bash
az containerapp create \
  --name chatbot-api \
  --resource-group chatbot-rg \
  --image chatbotregistry.azurecr.io/chatbot-api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 0.5 --memory 1.0Gi \
  --secrets openai-key=$OPENAI_API_KEY \
  --env-vars \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    OPENAI_API_KEY=secretref:openai-key
```

## DigitalOcean App Platform

**app.yaml:**
```yaml
name: chatbot-api
services:
- name: api
  github:
    repo: your-username/chatbot
    branch: main
    deploy_on_push: true
  dockerfile_path: Dockerfile
  health_check:
    http_path: /health
  http_port: 8000
  instance_count: 2
  instance_size_slug: basic-xs
  routes:
  - path: /
  envs:
  - key: OPENAI_API_KEY
    scope: RUN_TIME
    type: SECRET
  - key: COMPANY_NAME
    value: "Your Company"
```

```bash
doctl apps create --spec app.yaml
```

## Heroku Deployment

**1. Create app:**
```bash
heroku create chatbot-api
```

**2. Set environment variables:**
```bash
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set COMPANY_NAME="Your Company"
```

**3. Deploy:**
```bash
git push heroku main
```

**4. Scale:**
```bash
heroku ps:scale web=2
```

## Nginx Reverse Proxy Configuration

**nginx.conf:**
```nginx
upstream chatbot_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://chatbot_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Environment Variables Management

### AWS Secrets Manager
```bash
# Store secret
aws secretsmanager create-secret \
  --name chatbot/openai-key \
  --secret-string "sk-..."

# Retrieve in application
import boto3
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='chatbot/openai-key')
```

### GCP Secret Manager
```bash
# Create secret
echo -n "sk-..." | gcloud secrets create openai-key --data-file=-

# Access in Cloud Run
gcloud run deploy chatbot-api \
  --set-secrets OPENAI_API_KEY=openai-key:latest
```

### Azure Key Vault
```bash
# Create secret
az keyvault secret set \
  --vault-name chatbot-vault \
  --name openai-key \
  --value "sk-..."
```

## Database Setup (Production)

### PostgreSQL for Conversation History

**Using RDS (AWS):**
```bash
aws rds create-db-instance \
  --db-instance-identifier chatbot-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password SecurePassword123 \
  --allocated-storage 20
```

**Connection String:**
```env
DATABASE_URL=postgresql://admin:SecurePassword123@chatbot-db.xxx.us-east-1.rds.amazonaws.com:5432/chatbot
```

### Redis for Sessions & Caching

**Using ElastiCache (AWS):**
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id chatbot-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

## Monitoring & Logging

### CloudWatch (AWS)

**Log Group Setup:**
```bash
aws logs create-log-group --log-group-name /aws/chatbot/api
```

**Custom Metrics:**
```python
import boto3

cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='Chatbot',
    MetricData=[{
        'MetricName': 'ChatMessages',
        'Value': 1.0,
        'Unit': 'Count'
    }]
)
```

### Prometheus + Grafana

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'chatbot'
    static_configs:
      - targets: ['chatbot-api:8000']
```

## CI/CD Pipeline

### GitHub Actions

**.github/workflows/deploy.yml:**
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
      
      - name: Build and push
        run: |
          docker build -t chatbot-api .
          docker tag chatbot-api:latest $ECR_REGISTRY/chatbot-api:latest
          docker push $ECR_REGISTRY/chatbot-api:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster chatbot --service chatbot-api --force-new-deployment
```

## Performance Optimization

### 1. Managed Vector Store
Use Pinecone instead of local Chroma:
```python
from langchain_pinecone import PineconeVectorStore

vectorstore = PineconeVectorStore.from_documents(
    documents,
    embeddings,
    index_name="chatbot-kb"
)
```

### 2. Response Caching
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_response(message: str, session_id: str):
    cache_key = hashlib.md5(f"{message}{session_id}".encode()).hexdigest()
    # Check cache first
    # Return cached response or generate new one
```

### 3. Connection Pooling
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

## Cost Optimization

### Tips to Reduce Costs:
1. Use cheaper models (gpt-3.5-turbo, claude-haiku)
2. Implement aggressive response caching
3. Set lower max_tokens limits
4. Use auto-scaling with min replicas = 0
5. Implement token counting and budgets
6. Archive old conversations
7. Use spot/preemptible instances

### Budget Alerts (AWS):
```bash
aws budgets create-budget \
  --account-id 123456789 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

## Troubleshooting Production Issues

### Common Issues:

**High Latency:**
- Check vector store performance
- Optimize database queries
- Enable caching
- Scale horizontally

**Out of Memory:**
- Increase container memory
- Clear old sessions
- Implement memory limits

**API Rate Limits:**
- Implement exponential backoff
- Use multiple API keys with load balancing
- Cache common responses

**Failed Health Checks:**
- Check application logs
- Verify dependencies (DB, Redis)
- Check network connectivity
- Review timeout settings

## Support & Maintenance

### Regular Tasks:
- [ ] Monitor API usage and costs
- [ ] Review and update knowledge base monthly
- [ ] Check error logs weekly
- [ ] Update dependencies quarterly
- [ ] Review security alerts
- [ ] Backup database daily
- [ ] Test disaster recovery quarterly

---

**Remember:** Always test in staging before deploying to production! 🚀
