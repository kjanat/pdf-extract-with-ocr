# Running with Docker

This guide explains how to run PDF Extract with OCR using Docker directly without Docker Compose. This approach is simpler but provides fewer features than the full stack deployment.

## Prerequisites

- [Docker][Docker Install] installed on your system
- Basic knowledge of Docker commands

## Quick Start

Run the container with the following command:

=== ":material-bash: Bash"

    ```bash
    docker run -d -p 8080:80 -e IS_DOCKER_CONTAINER=true kjanat/pdf-extract-with-ocr:latest
    ```

=== ":material-powershell: PowerShell"

    ```pwsh
    docker run -d -p '8080:80' -e 'IS_DOCKER_CONTAINER=true' kjanat/pdf-extract-with-ocr:latest
    ```

This will start the API service and make it available at [http://localhost:8080](http://localhost:8080).

## Environment Variables

You can configure the container using environment variables:

=== ":material-bash: Bash"

    ```bash
    docker run -d \
        -p 8080:80 \
        -e IS_DOCKER_CONTAINER=true \
        -e DATABASE_URL=sqlite:///local.db \
        kjanat/pdf-extract-with-ocr:latest
    ```

=== ":material-powershell: PowerShell"

    ```pwsh
    docker run -d `
        -p '8080:80' `
        -e 'IS_DOCKER_CONTAINER=true' `
        -e 'DATABASE_URL=sqlite:///local.db' `
        kjanat/pdf-extract-with-ocr:latest
    ```

Important environment variables:

| Variable              | Description                | Default              |
| --------------------- | -------------------------- | -------------------- |
| `IS_DOCKER_CONTAINER` | Required for Docker mode   | `true`               |
| `DATABASE_URL`        | Database connection string | `sqlite:///local.db` |

## Persistent Storage

To persist uploads and the database, mount volumes:

=== ":material-bash: Bash"

    ```bash
    docker run -d \
        -p 8080:80 \
        -e IS_DOCKER_CONTAINER=true \
        -v ./uploads:/app/uploads \
        -v ./data:/app/data \
        kjanat/pdf-extract-with-ocr:latest
    ```

=== ":material-powershell: PowerShell"

    ```pwsh
    docker run -d `
        -p '8080:80' `
        -e 'IS_DOCKER_CONTAINER=true' `
        -v './uploads:/app/uploads' `
        -v './data:/app/data' `
        kjanat/pdf-extract-with-ocr:latest
    ```

## Limitations

When running the Docker image directly (compared to Docker Compose):

- No separate worker for background processing
- No Redis for message queuing
- Limited scalability
- Using SQLite instead of PostgreSQL by default

For production use, the Docker Compose setup is recommended.

## Architecture Support

The Docker images are built for multiple architectures:

- `linux/amd64` (x86_64)
- `linux/arm64` (aarch64)
- `linux/arm/v7` (armv7)

Docker will automatically pull the correct image for your system architecture.

## Troubleshooting

If you encounter issues:

1. Check the container logs: `docker logs <container-id>`
2. Verify that the container is running: `docker ps`
3. Ensure port `8080` is not already in use on your host
4. Check if volumes have correct permissions

For more information, refer to the [GitHub repository][Repository].
