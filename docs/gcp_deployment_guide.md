# Deploying Electric Network API to Google Cloud Platform

This guide provides detailed instructions for deploying the Electric Network API application to Google Cloud Platform (GCP). The application is a FastAPI-based service that provides dynamic SQL querying capabilities for electric infrastructure data.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Setting Up Google Cloud Project](#setting-up-google-cloud-project)
4. [Database Setup with Cloud SQL](#database-setup-with-cloud-sql)
5. [Containerizing the Application](#containerizing-the-application)
6. [Deploying with Cloud Run](#deploying-with-cloud-run)
7. [Environment Configuration](#environment-configuration)
8. [Continuous Deployment](#continuous-deployment)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Cost Optimization](#cost-optimization)

## Prerequisites

Before you begin, ensure you have the following:

- Google Cloud Platform account
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
- [Docker](https://docs.docker.com/get-docker/) installed locally
- Git repository with your application code

## Deployment Options

Google Cloud Platform offers several options for deploying FastAPI applications:

1. **Cloud Run** (Recommended): Serverless container platform that automatically scales based on traffic.
2. **Google Kubernetes Engine (GKE)**: Managed Kubernetes service for container orchestration.
3. **App Engine**: Platform-as-a-Service (PaaS) for applications.
4. **Compute Engine**: Virtual machines for more control over the infrastructure.

This guide focuses on Cloud Run as it provides the best balance of simplicity, scalability, and cost-effectiveness for FastAPI applications.

## Setting Up Google Cloud Project

1. Create a new Google Cloud project or select an existing one:

```bash
# Create a new project
gcloud projects create [PROJECT_ID] --name="Electric Network API"

# Set the project as the default
gcloud config set project [PROJECT_ID]
```

2. Enable the required APIs:

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## Database Setup with Cloud SQL

The application uses PostgreSQL with PostGIS extensions for geospatial data. Google Cloud SQL provides a fully managed database service that supports PostGIS.

### Creating a Cloud SQL PostgreSQL Instance with PostGIS

1. Create a PostgreSQL instance with PostGIS:

```bash
gcloud sql instances create electric-network-db \
  --database-version=POSTGRES_14 \
  --tier=db-custom-2-8192 \
  --region=us-central1 \
  --availability-type=REGIONAL \
  --storage-type=SSD \
  --storage-size=20 \
  --root-password=[SECURE_ROOT_PASSWORD]
```

This creates a PostgreSQL 14 instance with:
- 2 vCPUs and 8GB RAM
- Regional availability for high availability
- SSD storage for better performance
- 20GB initial storage (automatically scales up as needed)

2. Create a database:

```bash
gcloud sql databases create INKWELL --instance=electric-network-db
```

3. Create a user for your application:

```bash
gcloud sql users create postgres \
  --instance=electric-network-db \
  --password=[SECURE_PASSWORD]
```

### Enabling PostGIS Extension

Cloud SQL for PostgreSQL supports PostGIS, but you need to enable it:

1. Connect to your database using Cloud SQL Proxy:

```bash
# Install Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.6.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy

# Start the proxy
./cloud-sql-proxy --port 5432 [PROJECT_ID]:us-central1:electric-network-db
```

2. In another terminal, connect to the database:

```bash
psql -h localhost -U postgres -d INKWELL
```

3. Enable the PostGIS extension:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

4. Create the `network` schema:

```sql
CREATE SCHEMA IF NOT EXISTS network;
```

5. Verify PostGIS is installed:

```sql
SELECT PostGIS_version();
```

### Setting Up Private IP (Recommended for Production)

For better security and performance in production:

1. Create a VPC network if you don't have one:

```bash
gcloud compute networks create electric-network-vpc --subnet-mode=auto
```

2. Configure private IP for your Cloud SQL instance:

```bash
gcloud sql instances patch electric-network-db \
  --network=electric-network-vpc \
  --no-assign-ip
```

3. Create a VPC connector for Cloud Run to access the private Cloud SQL instance:

```bash
gcloud compute networks vpc-access connectors create electric-network-connector \
  --region=us-central1 \
  --network=electric-network-vpc \
  --range=10.8.0.0/28
```

## Containerizing the Application

1. Create a `Dockerfile` in your project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2 and geoalchemy2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
```

2. Create a `.dockerignore` file:

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
.env
.venv
venv/
ENV/
.git
.gitignore
```

3. Build and test the Docker image locally:

```bash
docker build -t electric-network-api .
docker run -p 8080:8080 -e PORT=8080 -e DATABASE_URL=postgresql://postgres:1234@host.docker.internal:5432/INKWELL electric-network-api
```

## Deploying with Cloud Run

1. Update the application to use environment variables for configuration:

Create a file `app/config.py`:

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234@localhost:5432/INKWELL")
```

Update `app/database.py` to use this configuration:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

2. Build and push the Docker image to Google Container Registry:

```bash
# Build the image
gcloud builds submit --tag gcr.io/[PROJECT_ID]/electric-network-api

# Or use Docker to build and push
docker build -t gcr.io/[PROJECT_ID]/electric-network-api .
docker push gcr.io/[PROJECT_ID]/electric-network-api
```

3. Deploy to Cloud Run with Cloud SQL connection:

```bash
# For public IP connection
gcloud run deploy electric-network-api \
  --image gcr.io/[PROJECT_ID]/electric-network-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://postgres:[PASSWORD]@/INKWELL?host=/cloudsql/[PROJECT_ID]:us-central1:electric-network-db \
  --add-cloudsql-instances [PROJECT_ID]:us-central1:electric-network-db

# For private IP connection (if you set up private IP)
gcloud run deploy electric-network-api \
  --image gcr.io/[PROJECT_ID]/electric-network-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --vpc-connector electric-network-connector \
  --set-env-vars DATABASE_URL=postgresql://postgres:[PASSWORD]@[PRIVATE_IP]:5432/INKWELL
```

The `/cloudsql/[PROJECT_ID]:us-central1:electric-network-db` syntax is a special format that Cloud Run uses to connect to Cloud SQL via the Cloud SQL Auth Proxy, which is automatically integrated with Cloud Run when you use the `--add-cloudsql-instances` flag.

## Environment Configuration

For secure management of environment variables:

1. Store sensitive information in Secret Manager:

```bash
# For Cloud SQL Auth Proxy connection (public IP with secure tunnel)
echo -n "postgresql://postgres:[PASSWORD]@/INKWELL?host=/cloudsql/[PROJECT_ID]:us-central1:electric-network-db" | \
  gcloud secrets create database-url --data-file=-

# OR for private IP connection
echo -n "postgresql://postgres:[PASSWORD]@[PRIVATE_IP]:5432/INKWELL" | \
  gcloud secrets create database-url --data-file=-

# Grant access to the Cloud Run service
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:service-[PROJECT_NUMBER]@serverless-robot-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Note: You'll need to replace `[PROJECT_NUMBER]` with your actual Google Cloud project number, which is different from the project ID. You can find it in the Google Cloud Console or by running:

```bash
gcloud projects describe [PROJECT_ID] --format="value(projectNumber)"
```

2. Update the Cloud Run deployment to use the secret:

```bash
# For Cloud SQL Auth Proxy connection
gcloud run deploy electric-network-api \
  --image gcr.io/[PROJECT_ID]/electric-network-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances [PROJECT_ID]:us-central1:electric-network-db \
  --set-secrets DATABASE_URL=database-url:latest

# For private IP connection
gcloud run deploy electric-network-api \
  --image gcr.io/[PROJECT_ID]/electric-network-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --vpc-connector electric-network-connector \
  --set-secrets DATABASE_URL=database-url:latest
```

Using Secret Manager is more secure than setting environment variables directly, as it:
- Encrypts sensitive data at rest
- Provides version control for secrets
- Offers fine-grained access control
- Integrates with Cloud Audit Logging

## Continuous Deployment

Set up continuous deployment using Cloud Build:

1. Create a `cloudbuild.yaml` file:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/electric-network-api:$COMMIT_SHA', '.']

  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/electric-network-api:$COMMIT_SHA']

  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'electric-network-api'
      - '--image'
      - 'gcr.io/$PROJECT_ID/electric-network-api:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      # Use this for Cloud SQL Auth Proxy connection
      - '--add-cloudsql-instances'
      - '$PROJECT_ID:us-central1:electric-network-db'
      # OR use this for private IP connection (uncomment and remove the above two lines)
      # - '--vpc-connector'
      # - 'electric-network-connector'
      - '--set-secrets'
      - 'DATABASE_URL=database-url:latest'

images:
  - 'gcr.io/$PROJECT_ID/electric-network-api:$COMMIT_SHA'
```

2. Set up a trigger in Cloud Build to automatically build and deploy when changes are pushed to your repository.

## Monitoring and Logging

1. Set up monitoring for your Cloud Run service:
   - Go to the Cloud Run service in the Google Cloud Console
   - Click on the "Metrics" tab to view performance metrics

2. View logs:
   - Go to the Cloud Run service
   - Click on the "Logs" tab to view application logs

3. Set up alerts:
   - Go to Cloud Monitoring
   - Create alerts for metrics like error rates, latency, and instance count

## Cost Optimization

Cloud Run charges based on the resources used when the service is handling requests. To optimize costs:

1. Configure concurrency appropriately:
   ```bash
   gcloud run services update electric-network-api --concurrency=80
   ```

2. Set memory limits based on your application's needs:
   ```bash
   gcloud run services update electric-network-api --memory=512Mi
   ```

3. Set CPU allocation:
   ```bash
   gcloud run services update electric-network-api --cpu=1
   ```

4. Configure minimum and maximum instances:
   ```bash
   gcloud run services update electric-network-api --min-instances=0 --max-instances=10
   ```

By setting min-instances to 0, your service can scale to zero when not in use, saving costs.
