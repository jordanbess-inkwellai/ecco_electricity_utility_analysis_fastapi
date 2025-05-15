# Electric Network API Architecture

This document describes the architecture of the Electric Network API application, including its components, data flow, and deployment architecture.

## System Overview

The Electric Network API is a FastAPI-based application that provides dynamic SQL querying capabilities for electric infrastructure data. It allows users to create custom API endpoints on-the-fly by defining SQL queries, which are then exposed as RESTful API endpoints.

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  API Clients    │────▶│  FastAPI        │────▶│  PostgreSQL     │
│  (Web/Mobile)   │◀────│  Application    │◀────│  with PostGIS   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               │
                               ▼
                        ┌─────────────────┐
                        │                 │
                        │  Dynamic        │
                        │  Endpoint       │
                        │  Registry       │
                        │                 │
                        └─────────────────┘
```

## Component Details

### FastAPI Application

The core of the system is a FastAPI application that provides:

- RESTful API endpoints
- Automatic API documentation (Swagger UI and ReDoc)
- Request validation using Pydantic models
- Dependency injection for database sessions

Key components:

- **main.py**: Application entry point and configuration
- **config.py**: Environment-based configuration
- **database.py**: Database connection management
- **models/**: SQLAlchemy ORM models
- **routers/**: API route definitions

### Dynamic Endpoint Registry

A unique feature of the application is its ability to create dynamic API endpoints at runtime:

1. Users submit SQL queries with a name via the `/api/create-endpoint/` endpoint
2. The application registers a new route at `/api/custom/{name}`
3. When the new endpoint is called, the application executes the SQL query with any provided parameters
4. Results are returned as JSON

This allows for flexible querying of the database without requiring code changes.

### PostgreSQL with PostGIS

The application uses PostgreSQL with the PostGIS extension for storing and querying geospatial data:

- **PostgreSQL**: Relational database for storing electric network data
- **PostGIS**: Extension that adds geospatial capabilities to PostgreSQL
- **GeoAlchemy2**: Python library for working with geospatial data in SQLAlchemy

## Data Flow

1. **API Request**: Client sends a request to a specific endpoint
2. **Request Handling**: FastAPI routes the request to the appropriate handler
3. **Database Session**: A database session is created via dependency injection
4. **Query Execution**: The handler executes the SQL query with parameters from the request
5. **Response Formatting**: Results are formatted as JSON and returned to the client

## Google Cloud Deployment Architecture

When deployed to Google Cloud Platform, the architecture looks like this:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  API Clients    │────▶│  Cloud Run      │────▶│  Cloud SQL      │
│                 │◀────│  (FastAPI App)  │◀────│  (PostgreSQL)   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               │
                               ▼
                        ┌─────────────────┐
                        │                 │
                        │  Secret Manager │
                        │  (Env Vars)     │
                        │                 │
                        └─────────────────┘
```

Components:

- **Cloud Run**: Serverless container platform running the FastAPI application
- **Cloud SQL**: Managed PostgreSQL database with PostGIS extension
- **Secret Manager**: Secure storage for sensitive configuration (database credentials)
- **Cloud Build**: CI/CD pipeline for automated deployment

## Security Considerations

- **Database Connection**: Uses connection pooling and proper connection management
- **SQL Injection**: While the application allows dynamic SQL, it uses parameterized queries to prevent SQL injection
- **Environment Variables**: Sensitive information is stored in environment variables or Secret Manager
- **Authentication**: (To be implemented) API key or OAuth2 authentication for endpoint creation

## Scalability

The architecture is designed to scale horizontally:

- **Cloud Run**: Automatically scales based on traffic
- **Connection Pooling**: Efficient database connection management
- **Stateless Design**: No session state is stored in the application

## Future Enhancements

- Add authentication and authorization
- Implement rate limiting
- Add caching layer for frequently accessed data
- Support for more complex geospatial operations
- Implement WebSocket support for real-time updates
