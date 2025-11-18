<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD041 -->

<div align="center">

# PDF Extract with OCR

</div>

<div align="center" style="padding: 2vh 10vw 1vh 10vw; display: flex; flex-basis: auto; flex-wrap: wrap; flex-shrink: 1; flex-flow: row wrap; float: inline-flex; justify-content: space-around; justify-items: center;">

[![Commits](https://img.shields.io/github/commit-activity/m/kjanat/pdf-extract-with-ocr/master?style=for-the-badge)][GitHub Commits]
[![GitHub last commit](https://img.shields.io/github/last-commit/kjanat/pdf-extract-with-ocr/master?style=for-the-badge&label=Last%20commit)][GitHub Monthly]
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/kjanat/pdf-extract-with-ocr/docker.yml?style=for-the-badge)][Build Status]
[![Docker Pulls](https://img.shields.io/docker/pulls/kjanat/pdf-extract-with-ocr?style=for-the-badge)][Docker]
[![Docker Image Size](https://img.shields.io/docker/image-size/kjanat/pdf-extract-with-ocr?style=for-the-badge&sort=date)][Docker]
[![Docker Image Version](https://img.shields.io/docker/v/kjanat/pdf-extract-with-ocr?style=for-the-badge&label=Version&sort=date)][Docker]
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fpdf-extract-with-ocr.kjanat.com%2F&up_message=Live&down_message=Down&style=for-the-badge&logo=materialformkdocs&logoColor=white&label=Documentation)][Documentation]
![GitHub License](https://img.shields.io/github/license/kjanat/pdf-extract-with-ocr?style=for-the-badge&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMjEgMTY2IiBzaGFwZS1yZW5kZXJpbmc9ImNyaXNwRWRnZXMiIGZpbGw9IiNmZmYiPjxwYXRoIGQ9Ik0wIDBoMzV2MTY2SDB6bTU3IDBoMzV2MTEzSDU3em01NyAwaDM1djE2NmgtMzV6bTU3IDBoMzV2MzNoLTM1em01OCA1M2gzNXYxMTNoLTM1em0wLTUzaDkydjMzaC05MnpNMTcxIDUzaDM1djExM2gtMzV6Ii8%2BPC9zdmc%2B)

</div>

This project is a Flask-based web application that extracts text from PDF files. It determines whether the PDF contains selectable text or is a scanned document, using [`PyMuPDF`][pymupdf] for direct text extraction and [`Tesseract OCR`][tesseract] for scanned images.

## Features

### Core Features
- Extracts text from PDFs with selectable text using [`PyMuPDF`][pymupdf]
- Detects scanned PDFs and applies OCR with [`Tesseract`][tesseract]
- Automatic Tesseract installation check and language data download
- Returns extracted text in a structured JSON format
- Provides processing time and extraction method details
- Intelligent result caching based on file hash to avoid reprocessing

### API & Documentation
- **Interactive API Documentation**: Swagger/OpenAPI documentation at `/docs`
- **RESTful API**: Well-structured endpoints for uploads, job status, and results
- **Health Checks**: Liveness (`/api/health`) and readiness (`/api/ready`) endpoints
- **API Key Authentication**: Optional API key protection for all endpoints

### Performance & Scalability
- **Asynchronous Processing**: Celery-based task queue for background PDF processing
- **Rate Limiting**: Configurable rate limits to prevent abuse
- **Result Caching**: File hash-based caching to avoid redundant processing
- **Connection Pooling**: Optimized database connections with SQLAlchemy pooling
- **Database Indexes**: Optimized queries for fast job lookups

### Infrastructure
- **Object Storage**: Pluggable storage backend supporting local filesystem and S3/MinIO
- **Monitoring**: Celery Flower dashboard for task monitoring (port 5555)
- **Production Ready**: WSGI server (Waitress), comprehensive error handling
- **Docker Support**: Multi-architecture images (amd64, arm64, armv7)
- **Application Factory**: Modular, testable architecture following Flask best practices

## Installation

1. Clone the repository:

   ``` sh
   git clone https://github.com/kjanat/pdf-extract-with-ocr.git
   cd pdf-extract-with-ocr
   ```

2. Create a virtual environment and activate it:

   ``` sh
   python -m venv venv

   # On macOS/Linux
   source venv/bin/activate

   # On Windows
   venv\Scripts\activate
   ```

3. Install the required dependencies:

   ``` sh
   pip install -U -r requirements.txt
   ```

4. Install Tesseract OCR:

   - On Windows, use winget:

     ``` powershell
     'tesseract-ocr.tesseract', 'SQLite.SQLite' | 
         % { winget install --id=$_ }
     ```

   - On macOS, use Homebrew:

     ``` sh
     brew install \
         tesseract \
         redis \
         sqlite
     ```

   - On Linux, use your package manager:

     ``` sh
     sudo apt-get install -y \
         tesseract-ocr \
         redis-server \
         sqlite3
     ```

## Usage

1. Run the Flask application:

   ``` sh
   python app.py
   ```

2. Open your browser and navigate to `http://127.0.0.1:5000` to access the web interface and upload a pdf, or upload a PDF file through the `/upload` endpoint:

   ``` sh
   curl -X POST -F file=@path/to/your/file.pdf http://127.0.0.1:5000/upload
   ```

3. The API will return a JSON response with the extracted text, status, method used, and processing duration.

## Docker Usage

### Using Docker Compose

The easiest way to run the full stack is with Docker Compose:

1. Download the  file:

   ``` sh
   wget https://raw.githubusercontent.com/kjanat/pdf-extract-with-ocr/docker/docker-compose.yml
   ```

2. Adjust the `docker-compose.yml` file if necessary. You can change the ports or other configurations as needed.

   ``` yaml
   services:
     api:
       image: kjanat/pdf-extract-with-ocr:latest
       ports:
         - "8080:80"
       environment:
         - IS_DOCKER_CONTAINER=true
         - CELERY_BROKER_URL=redis://redis:6379/0
         - DATABASE_URL=postgresql://ocruser:ocrpass@db:5432/ocr
     worker:
       image: kjanat/pdf-extract-with-ocr:latest
       command: celery -A main.celery worker --loglevel=info
     redis:
       image: redis:latest
     db:
       image: postgres:latest
       environment:
         POSTGRES_USER: user
         POSTGRES_PASSWORD: password
         POSTGRES_DB: pdf_extract_db
   ```

3. Start the services:

   ``` sh
   docker-compose up
   ```

This starts four services:

- The Flask API server on port `8080`
- A Celery worker for processing PDFs
- A Redis instance for the message queue
- A PostgreSQL database for storing results

### Running the Docker Image Directly

You can also run just the API container:

```sh
docker run -p 8080:80 -e IS_DOCKER_CONTAINER=true kjanat/pdf-extract-with-ocr:latest-full
```

### Supported Architectures

The Docker images are built for multiple architectures:

- linux/amd64 (x86_64)
- linux/arm64 (aarch64)
- linux/arm/v7 (armv7)

Docker will automatically pull the correct image for your system architecture.

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following configuration options:

#### Database Configuration
```bash
DATABASE_URL=postgresql://ocruser:ocrpass@localhost:5432/ocr
POSTGRES_USER=ocruser
POSTGRES_PASSWORD=ocrpass
POSTGRES_DB=ocr
```

#### Celery Configuration
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
```

#### API Configuration
```bash
# Optional API key for authentication
API_KEY=your-secret-api-key-here

# CORS settings
ALLOWED_ORIGINS=*

# Rate limiting
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1
```

#### Object Storage (Optional)
```bash
# Set to 'true' to use S3/MinIO instead of local filesystem
USE_S3=false

# S3/MinIO configuration (required if USE_S3=true)
S3_BUCKET=pdf-extract-uploads
S3_ENDPOINT=https://s3.amazonaws.com
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

#### Application Settings
```bash
# Docker mode detection
IS_DOCKER_CONTAINER=false

# Ports
API_PORT=8080
FLOWER_PORT=5555

# File storage
UPLOADS_DIR=./uploads
```

### API Authentication

When `API_KEY` is set in your environment, all API endpoints will require authentication:

```bash
# Upload a PDF with authentication
curl -X POST \
  -H "X-API-Key: your-secret-api-key-here" \
  -F file=@document.pdf \
  http://localhost:8080/upload

# Check job status with authentication
curl -H "X-API-Key: your-secret-api-key-here" \
  http://localhost:8080/api/status/task-id
```

### API Endpoints

#### Interactive Documentation
- **Swagger UI**: `http://localhost:8080/docs` - Interactive API documentation and testing

#### Health Checks
- **Liveness**: `GET /api/health` - Basic health check
- **Readiness**: `GET /api/ready` - Database connectivity check

#### PDF Processing
- **Upload**: `POST /upload` - Upload a PDF file for processing
- **Status**: `GET /api/status/{task_id}` - Check processing status
- **Result**: `GET /api/result/{task_id}` - Get extraction results
- **Jobs List**: `GET /api/jobs` - List recent jobs

#### Monitoring
- **Flower Dashboard**: `http://localhost:5555` - Celery task monitoring

## Example Response

``` json
{
   "body": "Extracted text from the PDF here...",
   "status": "success",
   "method": "tesseract",
   "filename": "example.pdf",
   "datetime": "2025-03-21T12:34:56.789012+00:00",
   "duration (ms)": 12.3
}
```

## License

Licensed under MIT License, see [LICENSE](LICENSE)

<!-- [GitHub License]: #license "Not licensed" -->

[GitHub Commits]: https://github.com/kjanat/pdf-extract-with-ocr/commits
[GitHub Monthly]: https://github.com/kjanat/pdf-extract-with-ocr/pulse/monthly
[Docker]: https://hub.docker.com/r/kjanat/pdf-extract-with-ocr
[Build Status]: https://github.com/kjanat/pdf-extract-with-ocr/actions/workflows/docker.yml
[Documentation]: https://pdf-extract-with-ocr.kjanat.com/
[tesseract]: https://github.com/tesseract-ocr/tesseract
[pymupdf]: https://github.com/pymupdf/PyMuPDF
