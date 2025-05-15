# Google Cloud SQL with PostGIS Guide

This guide provides detailed information on setting up and using Google Cloud SQL with PostGIS for geospatial data in your Electric Network API application.

## Table of Contents

1. [Introduction to Cloud SQL with PostGIS](#introduction-to-cloud-sql-with-postgis)
2. [Setting Up Cloud SQL with PostGIS](#setting-up-cloud-sql-with-postgis)
3. [Connecting to Cloud SQL](#connecting-to-cloud-sql)
4. [PostGIS Operations](#postgis-operations)
5. [Performance Optimization](#performance-optimization)
6. [Backup and Recovery](#backup-and-recovery)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Introduction to Cloud SQL with PostGIS

Google Cloud SQL for PostgreSQL with PostGIS provides a fully managed database service with geospatial capabilities. Key benefits include:

- Fully managed PostgreSQL database (no need to manage infrastructure)
- Automatic backups and point-in-time recovery
- High availability configuration options
- Automatic storage increases
- Built-in monitoring and logging
- Support for PostGIS extension for geospatial data

PostGIS adds support for geographic objects to PostgreSQL, allowing you to:
- Store and query location data (points, lines, polygons)
- Perform spatial calculations (distance, area, etc.)
- Create spatial indexes for efficient queries
- Analyze spatial relationships (intersections, contains, etc.)

## Setting Up Cloud SQL with PostGIS

### Creating a Cloud SQL Instance

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

### Creating a Database and User

```bash
# Create database
gcloud sql databases create INKWELL --instance=electric-network-db

# Create user
gcloud sql users create postgres \
  --instance=electric-network-db \
  --password=[SECURE_PASSWORD]
```

### Enabling PostGIS

Connect to your database using Cloud SQL Proxy:

```bash
# Install Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.6.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy

# Start the proxy
./cloud-sql-proxy --port 5432 [PROJECT_ID]:us-central1:electric-network-db
```

In another terminal, connect to the database and enable PostGIS:

```bash
psql -h localhost -U postgres -d INKWELL

# In PostgreSQL shell
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS network;
```

## Connecting to Cloud SQL

### Connection Methods

There are two primary methods to connect to Cloud SQL from Cloud Run:

1. **Cloud SQL Auth Proxy** (recommended for public IP instances):
   - Automatically handles authentication
   - Encrypts connections
   - No need to whitelist IP addresses

   ```python
   # Connection string format
   DATABASE_URL = "postgresql://postgres:PASSWORD@/INKWELL?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME"
   ```

2. **Private IP** (recommended for production):
   - Requires VPC network and connector
   - More secure as database is not exposed to the internet
   - Better performance

   ```python
   # Connection string format
   DATABASE_URL = "postgresql://postgres:PASSWORD@PRIVATE_IP:5432/INKWELL"
   ```

### Connection Pooling

For efficient database connections, implement connection pooling:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)
```

## PostGIS Operations

### Common PostGIS Functions

Here are some common PostGIS functions you might use in your application:

```sql
-- Create a point from longitude and latitude
SELECT ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);

-- Calculate distance between two points (in meters)
SELECT ST_Distance(
    ST_Transform(point1::geometry, 3857),
    ST_Transform(point2::geometry, 3857)
);

-- Find points within a certain distance
SELECT * FROM network.substations
WHERE ST_DWithin(
    ST_Transform(geom::geometry, 3857),
    ST_Transform(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geometry, 3857),
    1000  -- 1000 meters
);

-- Check if a point is within a polygon
SELECT ST_Contains(polygon_geom, point_geom);
```

### Spatial Indexing

For better performance with spatial queries, create spatial indexes:

```sql
CREATE INDEX idx_substations_geom ON network.substations USING GIST (geom);
```

## Performance Optimization

### Query Optimization

1. **Use spatial indexes** for all geometry columns
2. **Use ST_Transform** to convert to a projected coordinate system for accurate distance calculations
3. **Limit the result set** before performing expensive spatial operations
4. **Use ST_DWithin** instead of ST_Distance for radius searches

### Database Configuration

Optimize your Cloud SQL instance for geospatial workloads:

```bash
gcloud sql instances patch electric-network-db \
  --database-flags=shared_buffers=1GB,work_mem=16MB,maintenance_work_mem=128MB,effective_cache_size=3GB
```

## Backup and Recovery

### Automated Backups

Cloud SQL automatically creates daily backups. Configure backup settings:

```bash
gcloud sql instances patch electric-network-db \
  --backup-start-time=23:00 \
  --backup-location=us-central1
```

### Point-in-Time Recovery

Enable point-in-time recovery to restore to any moment within the retention period:

```bash
gcloud sql instances patch electric-network-db --enable-point-in-time-recovery
```

### Manual Backups

Create on-demand backups:

```bash
gcloud sql backups create --instance=electric-network-db
```

## Monitoring and Maintenance

### Monitoring

Set up monitoring for your Cloud SQL instance:

1. Go to the Google Cloud Console > SQL > electric-network-db > Monitoring
2. Create alerts for:
   - High CPU usage
   - High memory usage
   - Disk space running low
   - Connection count approaching limit

### Maintenance

Schedule maintenance windows:

```bash
gcloud sql instances patch electric-network-db \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=2
```

### Scaling

Vertically scale your instance as needed:

```bash
gcloud sql instances patch electric-network-db --tier=db-custom-4-15360
```

Horizontally scale with read replicas for read-heavy workloads:

```bash
gcloud sql instances create electric-network-replica \
  --master-instance-name=electric-network-db \
  --region=us-central1
```
