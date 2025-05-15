import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234@localhost:5432/INKWELL")

# Application configuration
APP_NAME = os.getenv("APP_NAME", "Electric Network API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "API for querying electric infrastructure dynamically.")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# API configuration
API_PREFIX = os.getenv("API_PREFIX", "/api")
DOCS_URL = os.getenv("DOCS_URL", "/docs")
REDOC_URL = os.getenv("REDOC_URL", "/redoc")
