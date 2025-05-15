# Electric Network API

A FastAPI-based service that provides dynamic SQL querying capabilities for electric infrastructure data, using PostGIS/PostgreSQL for spatial functions and operations needed by the Spatial Intelligence Team to understand utilities.

## Features

- Dynamic API endpoint creation based on SQL queries
- Geospatial data support with PostGIS
- RESTful API with automatic documentation

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL with PostGIS extension
- Git

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd ecco_electricity_utility_analysis_fastapi
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example` and update the values:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. Run the application:

```bash
uvicorn app.main:app --reload
```

6. Access the API documentation at http://localhost:8000/docs

### Database Setup

1. Create a PostgreSQL database:

```sql
CREATE DATABASE INKWELL;
```

2. Enable PostGIS extension:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

3. Create the network schema:

```sql
CREATE SCHEMA IF NOT EXISTS network;
```

## Deployment

For detailed deployment instructions to Google Cloud Platform, see [GCP Deployment Guide](docs/gcp_deployment_guide.md).

### Quick Deployment Steps

1. Build the Docker image:

```bash
docker build -t electric-network-api .
```

2. Test the Docker image locally:

```bash
docker run -p 8080:8080 -e PORT=8080 -e DATABASE_URL=postgresql://postgres:password@host.docker.internal:5432/INKWELL electric-network-api
```

3. Deploy to Google Cloud Run:

```bash
# Set up Google Cloud project
gcloud config set project [PROJECT_ID]

# Build and push the image
gcloud builds submit --tag gcr.io/[PROJECT_ID]/electric-network-api

# Deploy to Cloud Run
gcloud run deploy electric-network-api \
  --image gcr.io/[PROJECT_ID]/electric-network-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## API Usage

### Creating a Dynamic Endpoint

Send a POST request to `/api/create-endpoint/` with the following JSON body:

```json
{
  "name": "substations_by_voltage",
  "sql": "SELECT * FROM network.substations WHERE voltage_level_kv > :min_voltage"
}
```

This creates a new endpoint at `/api/custom/substations_by_voltage` that accepts a `min_voltage` query parameter.

### Querying the Dynamic Endpoint

```
GET /api/custom/substations_by_voltage?min_voltage=110
```

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── crud/             # Database operations
│   └── routers/          # API routes
├── docs/                 # Documentation
├── tests/                # Test cases
├── .env.example          # Example environment variables
├── .dockerignore         # Docker ignore file
├── Dockerfile            # Docker configuration
├── cloudbuild.yaml       # Google Cloud Build configuration
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```
