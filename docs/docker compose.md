# Running with Docker Compose

This guide explains how to run PDF Extract with OCR using Docker Compose, which is the recommended approach for deploying the full application stack.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your system
- Basic knowledge of Docker and Docker Compose

## Quick Start

<div class="annotate" markdown>

1. Clone the repository or download the docker-compose.yml file
2. Create a `.env` file in the same directory (1) (see [Environment Variables](#environment-variables) below)
3. Run the application:

</div>

1. This is optional! If no .env file is provided, the default values will be used.

```bash
docker-compose up -d
```

This will start all required services and make the API available at [`http://localhost:8080`](http://localhost:8080).

## Environment Variables

Create a `.env` file in the same directory as your docker-compose.yml with the following environment variables:

```yaml
# API configuration
API_PORT=8080                         # Port for the API service
UPLOADS_DIR=./uploads                 # Directory to store uploaded PDFs

# Database configuration
POSTGRES_USER=ocruser                 # PostgreSQL username
POSTGRES_PASSWORD=ocrpass             # PostgreSQL password
POSTGRES_DB=ocr                       # PostgreSQL database name
DATABASE_URL=postgresql://ocruser:ocrpass@db:5432/ocr

# Celery configuration
CELERY_BROKER_URL=redis://redis:6379/0
```

## Services Overview

The docker-compose.yml file defines four services:

### API Service

The API service exposes the Flask web server that provides the REST API and web interface for uploading PDFs. It's available at `http://localhost:8080` by default.

```yaml
api:
  image: kjanat/pdf-extract-with-ocr:latest
  container_name: pdf-extract-api
  ports:
    - "${API_PORT:-8080}:80"
  env_file:
    - .env
  volumes:
    - ${UPLOADS_DIR:-./uploads}:/app/uploads
  # ...
```

### Worker Service

The worker service processes PDF files asynchronously using Celery. It performs the actual text extraction from PDFs.

```yaml
worker:
  image: kjanat/pdf-extract-with-ocr:latest
  container_name: pdf-extract-celery-worker
  env_file:
    - .env
  volumes:
    - ${UPLOADS_DIR:-./uploads}:/app/uploads
  command: python -m celery -A celery_worker.celery worker --loglevel=info
  # ...
```

### Redis Service

Redis is used as a message broker for Celery tasks.

```yaml
redis:
  image: redis:latest
  container_name: pdf-extract-redis
  # ...
```

### Database Service

PostgreSQL database for storing extraction results and job history.

```yaml
db:
  image: postgres:latest
  container_name: pdf-extract-postgres-db
  volumes:
    - postgres_data:/var/lib/postgresql/data
  env_file:
    - .env
  # ...
```

## Architecture Support

The Docker images are built for multiple architectures:

- linux/amd64 (x86_64)
- linux/arm64 (aarch64)
- linux/arm/v7 (armv7)

Docker will automatically pull the correct image for your system architecture.

## Usage After Deployment

Once the services are up and running:

1. Access the web interface at [`http://localhost:8080`](http://localhost:8080)
2. Use the API endpoint for programmatic access:

```bash
curl -X POST -F file=@path/to/your/file.pdf http://localhost:8080/upload
```

## Management Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f api

# Stop all services
docker-compose down

# Stop services and remove volumes
docker-compose down -v

# Update the images
docker-compose pull
docker-compose up -d --build
```

## Troubleshooting

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify that all services are running: `docker-compose ps`
3. Make sure your `.env` file has the correct configuration
4. Check if ports are already in use on your host system
5. Ensure the uploads directory has the correct permissions

For more information about the application, refer to the [GitHub repository](https://github.com/kjanat/pdf-extract-with-ocr).
