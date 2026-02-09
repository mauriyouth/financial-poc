# Local Infrastructure Stack

Docker Compose configuration for local development services.

## Services

- **PostgreSQL** (port 5432) - Main database
- **MinIO** (ports 9000, 9001) - S3-compatible object storage
- **OpenSearch** (ports 9200, 9600) - Search engine
- **OpenSearch Dashboards** (port 5601) - Search UI
- **Redis** (port 6379) - Queue for async document parsing

## Usage

From backend directory:
```bash
make local-stack    # Start all services
```

Directly:
```bash
cd infra/local-stack
docker-compose up -d
```

## Access

- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- OpenSearch Dashboards: http://localhost:5601
- PostgreSQL: localhost:5432 (user/password)
- Redis: localhost:6379
