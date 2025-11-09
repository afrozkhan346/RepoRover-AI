# Cloud Run Deployment Guide

Complete guide to deploy RepoRoverAI microservices to Google Cloud Run.

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed locally
- Project created in Google Cloud Console

## Initial Setup

### 1. Configure gcloud

```bash
# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 2. Setup Firestore

```bash
# Create Firestore database (Native mode)
gcloud firestore databases create --region=us-central1

# Note: Choose a region close to your Cloud Run deployment region
```

### 3. Create Artifact Registry (optional, for caching images)

```bash
gcloud artifacts repositories create reporover-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="RepoRoverAI Docker images"
```

## Service Deployment

### Deploy Data Service (First)

```bash
cd services/data-service

gcloud run deploy data-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID \
  --max-instances 10 \
  --min-instances 0 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60s \
  --concurrency 80

# Save the service URL
export DATA_SERVICE_URL=$(gcloud run services describe data-service \
  --region us-central1 --format 'value(status.url)')

echo "Data Service URL: $DATA_SERVICE_URL"
```

### Deploy AI Service

```bash
cd services/ai-service

gcloud run deploy ai-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=YOUR_GEMINI_KEY \
  --max-instances 10 \
  --min-instances 0 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 120s \
  --concurrency 80

export AI_SERVICE_URL=$(gcloud run services describe ai-service \
  --region us-central1 --format 'value(status.url)')

echo "AI Service URL: $AI_SERVICE_URL"
```

### Deploy Analyze Service

```bash
cd services/analyze-service

gcloud run deploy analyze-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GITHUB_TOKEN=YOUR_GITHUB_TOKEN,AI_SERVICE_URL=$AI_SERVICE_URL \
  --max-instances 10 \
  --min-instances 0 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 120s \
  --concurrency 80

export ANALYZE_SERVICE_URL=$(gcloud run services describe analyze-service \
  --region us-central1 --format 'value(status.url)')

echo "Analyze Service URL: $ANALYZE_SERVICE_URL"
```

### Deploy Auth Service

```bash
cd services/auth-service

# Generate a secure secret
export BETTER_AUTH_SECRET=$(openssl rand -base64 32)

gcloud run deploy auth-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars BETTER_AUTH_SECRET=$BETTER_AUTH_SECRET,DATA_SERVICE_URL=$DATA_SERVICE_URL \
  --max-instances 10 \
  --min-instances 0 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60s \
  --concurrency 80

export AUTH_SERVICE_URL=$(gcloud run services describe auth-service \
  --region us-central1 --format 'value(status.url)')

echo "Auth Service URL: $AUTH_SERVICE_URL"
```

### Deploy Frontend Service

```bash
cd ../.. # Back to repo root

gcloud run deploy frontend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars \
    AI_SERVICE_URL=$AI_SERVICE_URL,\
    ANALYZE_SERVICE_URL=$ANALYZE_SERVICE_URL,\
    DATA_SERVICE_URL=$DATA_SERVICE_URL,\
    AUTH_SERVICE_URL=$AUTH_SERVICE_URL,\
    NEXT_PUBLIC_AI_SERVICE_URL=$AI_SERVICE_URL,\
    NEXT_PUBLIC_ANALYZE_SERVICE_URL=$ANALYZE_SERVICE_URL,\
    NEXT_PUBLIC_DATA_SERVICE_URL=$DATA_SERVICE_URL,\
    NEXT_PUBLIC_AUTH_SERVICE_URL=$AUTH_SERVICE_URL \
  --max-instances 10 \
  --min-instances 1 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300s \
  --concurrency 80

export FRONTEND_URL=$(gcloud run services describe frontend \
  --region us-central1 --format 'value(status.url)')

echo "Frontend URL: $FRONTEND_URL"
```

## Verify Deployment

### Health Checks

```bash
# Check each service
curl $DATA_SERVICE_URL/health
curl $AI_SERVICE_URL/health
curl $ANALYZE_SERVICE_URL/health
curl $AUTH_SERVICE_URL/health
curl $FRONTEND_URL/
```

### Test Endpoints

```bash
# Test AI service
curl -X POST $AI_SERVICE_URL/api/explain-code \
  -H "Content-Type: application/json" \
  -d '{"code":"const x = 5;","language":"javascript"}'

# Test Auth service
curl -X POST $AUTH_SERVICE_URL/api/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'

# Test Data service
curl $DATA_SERVICE_URL/api/lessons
```

## Update Environment Variables

To update env vars after deployment:

```bash
gcloud run services update SERVICE_NAME \
  --region us-central1 \
  --set-env-vars KEY=VALUE
```

## View Logs

```bash
# View logs for a service
gcloud run services logs read SERVICE_NAME --region us-central1 --limit 50

# Stream logs
gcloud run services logs tail SERVICE_NAME --region us-central1
```

## Cost Optimization

### Set Min Instances to 0 (Except Frontend)

```bash
gcloud run services update SERVICE_NAME \
  --region us-central1 \
  --min-instances 0
```

### Enable Request-based Scaling

```bash
gcloud run services update SERVICE_NAME \
  --region us-central1 \
  --max-instances 10 \
  --concurrency 80
```

## Security Best Practices

### 0. Avoid service account keys (use Workload Identity)

On Cloud Run, prefer attaching a service account to the service and granting it minimal IAM roles (e.g., Firestore User). Avoid distributing or mounting service account JSON keys in production.

Local development options:
- Use the Firestore emulator (recommended locally)
- Or authenticate locally with Application Default Credentials:
  - gcloud auth login
  - gcloud auth application-default login

Production on Cloud Run:
- Do not set GOOGLE_APPLICATION_CREDENTIALS
- Attach an IAM service account to each Cloud Run service
- Grant least-privilege roles; tokens are fetched via the metadata server automatically

### 1. Use Secret Manager for Sensitive Data

```bash
# Create secrets
echo -n "YOUR_GEMINI_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "YOUR_GITHUB_TOKEN" | gcloud secrets create github-token --data-file=-
echo -n "$BETTER_AUTH_SECRET" | gcloud secrets create auth-secret --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Update service to use secrets
gcloud run services update ai-service \
  --region us-central1 \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest
```

### 2. Enable VPC Connector (for private services)

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create reporover-connector \
  --region us-central1 \
  --range 10.8.0.0/28

# Use connector in service
gcloud run services update SERVICE_NAME \
  --region us-central1 \
  --vpc-connector reporover-connector
```

### 3. Restrict Service-to-Service Communication

```bash
# Update service to require authentication
gcloud run services update SERVICE_NAME \
  --region us-central1 \
  --no-allow-unauthenticated

# Grant invoker role to calling service
gcloud run services add-iam-policy-binding SERVICE_NAME \
  --region us-central1 \
  --member="serviceAccount:CALLING_SERVICE_SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

## Monitoring & Alerts

### Setup Cloud Monitoring

```bash
# Create uptime check
gcloud monitoring uptime-checks create https check-frontend \
  --resource-type=uptime-url \
  --resource-labels=host=$FRONTEND_URL

# Create alert policy
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=60s
```

## Rollback

```bash
# List revisions
gcloud run revisions list --service SERVICE_NAME --region us-central1

# Rollback to previous revision
gcloud run services update-traffic SERVICE_NAME \
  --region us-central1 \
  --to-revisions REVISION_NAME=100
```

## Cleanup

```bash
# Delete all services
gcloud run services delete frontend --region us-central1 --quiet
gcloud run services delete ai-service --region us-central1 --quiet
gcloud run services delete analyze-service --region us-central1 --quiet
gcloud run services delete data-service --region us-central1 --quiet
gcloud run services delete auth-service --region us-central1 --quiet

# Delete Firestore data (optional)
# Note: Use Firebase Console for this - cannot be done via CLI easily
```

## Troubleshooting

### Service Won't Start

```bash
# Check build logs
gcloud builds list --limit 5

# Check service logs
gcloud run services logs read SERVICE_NAME --region us-central1 --limit 100
```

### High Cold Start Times

- Increase min-instances to 1
- Reduce Docker image size
- Use startup CPU boost

### Out of Memory

- Increase memory limit: `--memory 1Gi`
- Check for memory leaks in logs

### 502/504 Errors

- Increase timeout: `--timeout 300s`
- Check service-to-service connectivity
- Verify environment variables are set correctly
