# Developer Guide

This guide provides detailed information for developers working on the Electric Network API project.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Adding New Features](#adding-new-features)
4. [Database Management](#database-management)
5. [Testing](#testing)
6. [Code Style and Standards](#code-style-and-standards)
7. [Common Development Tasks](#common-development-tasks)

## Development Environment Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 13+ with PostGIS extension
- Git

### Local Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd ecco_electricity_utility_analysis_fastapi
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install development dependencies:

```bash
pip install -r requirements-dev.txt  # If available
```

5. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your local configuration
```

6. Run the application:

```bash
uvicorn app.main:app --reload
```

### Docker Development Environment

For a containerized development environment:

```bash
# Build the development image
docker build -t electric-network-api-dev -f Dockerfile.dev .

# Run the container with local volume mounting
docker run -p 8000:8000 -v $(pwd):/app electric-network-api-dev
```

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection
│   ├── models/           # SQLAlchemy models
│   │   └── elec_models.py # Electric network models
│   ├── schemas/          # Pydantic schemas
│   │   └── elec_schemas.py # Data validation schemas
│   ├── crud/             # Database operations
│   │   └── elec_crud.py  # CRUD operations for electric models
│   └── routers/          # API routes
│       ├── dynamic_router.py # Dynamic endpoint creation
│       └── elec_router.py    # Electric network endpoints
├── docs/                 # Documentation
├── tests/                # Test cases
├── .env.example          # Example environment variables
├── .dockerignore         # Docker ignore file
├── Dockerfile            # Production Docker configuration
├── cloudbuild.yaml       # Google Cloud Build configuration
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## Adding New Features

### Adding a New Model

1. Create a new model in `app/models/`:

```python
# app/models/new_model.py
from sqlalchemy import Column, Integer, String, ForeignKey
from geoalchemy2 import Geometry
from app.database import Base

class NewModel(Base):
    __tablename__ = 'new_table'
    __table_args__ = {'schema': 'network'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    geom = Column(Geometry('POINT', 4326), nullable=False)
```

2. Create a Pydantic schema in `app/schemas/`:

```python
# app/schemas/new_schema.py
from pydantic import BaseModel
from typing import Optional

class NewModelBase(BaseModel):
    name: str
    
class NewModelCreate(NewModelBase):
    # Fields required for creation
    pass
    
class NewModelResponse(NewModelBase):
    id: int
    
    class Config:
        orm_mode = True
```

3. Add CRUD operations in `app/crud/`:

```python
# app/crud/new_crud.py
from sqlalchemy.orm import Session
from app.models.new_model import NewModel
from app.schemas.new_schema import NewModelCreate

def create_item(db: Session, item: NewModelCreate):
    db_item = NewModel(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

4. Create a router in `app/routers/`:

```python
# app/routers/new_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.new_schema import NewModelCreate, NewModelResponse
from app.crud.new_crud import create_item

router = APIRouter()

@router.post("/items/", response_model=NewModelResponse)
def add_item(item: NewModelCreate, db: Session = Depends(get_db)):
    return create_item(db, item)
```

5. Include the router in `app/main.py`:

```python
from app.routers import new_router

app.include_router(new_router.router, prefix="/api/new", tags=["New Items"])
```

### Adding a Dynamic Endpoint

To add a new dynamic endpoint at runtime:

```bash
curl -X POST "http://localhost:8000/api/create-endpoint/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new_endpoint",
    "sql": "SELECT * FROM network.new_table WHERE name LIKE :name_pattern"
  }'
```

## Database Management

### Database Migrations

For database migrations, we recommend using Alembic:

1. Initialize Alembic:

```bash
alembic init alembic
```

2. Configure `alembic.ini` and `alembic/env.py` to use your database.

3. Create a migration:

```bash
alembic revision --autogenerate -m "Add new table"
```

4. Apply migrations:

```bash
alembic upgrade head
```

### Working with Geospatial Data

Example of creating a point geometry:

```python
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

# Create a point with longitude and latitude
point = Point(longitude, latitude)
geom = from_shape(point, srid=4326)
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=app tests/
```

### Writing Tests

Example test for an API endpoint:

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Electric Network API is running"}
```

## Code Style and Standards

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Document functions and classes with docstrings
- Use meaningful variable and function names

### Linting and Formatting

```bash
# Run flake8 for linting
flake8 app tests

# Run black for code formatting
black app tests
```

## Common Development Tasks

### Adding a New Dependency

1. Add the dependency to `requirements.txt`
2. Install it in your virtual environment:

```bash
pip install -r requirements.txt
```

### Debugging

1. Use FastAPI's built-in debug mode:

```bash
uvicorn app.main:app --reload --debug
```

2. For more detailed debugging, use Python's debugger:

```python
import debugpy
debugpy.listen(("0.0.0.0", 5678))
debugpy.wait_for_client()  # Optional: wait for the debugger to attach
```

### Performance Profiling

```bash
python -m cProfile -o profile.prof app/main.py
```

Analyze the results:

```bash
python -m pstats profile.prof
```

Or use a visualization tool like SnakeViz:

```bash
pip install snakeviz
snakeviz profile.prof
```
