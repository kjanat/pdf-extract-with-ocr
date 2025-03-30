# Installation

PDF Extract with OCR offers multiple installation options to fit your needs:

## Installation Options

### 1. Docker Compose (Recommended)

The easiest way to run the full stack with all required services (API, worker, Redis, database).

- **Advantages**: Single command setup, includes all dependencies
- **Requirements**: `Docker` and `Docker Compose`
- Detailed [Docker Compose Instructions](docker-compose.md)

### 2. Docker Image

Run just the API container directly.

- **Advantages**: Simplified deployment, multi-architecture support
- **Requirements**: Docker
- **Supported architectures**: `linux/amd64`, `linux/arm64`<!-- , `linux/arm/v7` -->
- Detailed [Docker Instructions](docker.md)

### 3. From Source

Install and run directly on your host system.

- **Advantages**: Full control over installation, no containers
- **Requirements**: Python 3.8+, Tesseract OCR, SQLite/PostgreSQL, Redis
- Detailed [Source Installation Instructions](source.md)

## System Requirements

### Minimum Requirements

- 2GB RAM
- 500MB disk space
- Internet connection (for initial setup)

### Recommended Requirements

- 4GB RAM
- 1GB disk space
- Multi-core CPU

## Prerequisites

Depending on your installation method, you'll need:

- **Docker Compose**: Docker Engine and Docker Compose
- **Source Installation**:
    - Python 3.8 or higher
    - Tesseract OCR
    - SQLite or PostgreSQL
    - Redis (for task queuing)
