# Welcome!

[![Commits](https://img.shields.io/github/commit-activity/m/kjanat/pdf-extract-with-ocr?label=commits&style=for-the-badge)](https://github.com/kjanat/pdf-extract-with-ocr/commits)
[![GitHub last commit](https://img.shields.io/github/last-commit/kjanat/pdf-extract-with-ocr?style=for-the-badge&display_timestamp=committer)](https://github.com/kjanat/pdf-extract-with-ocr/pulse/monthly)
[![Docker Pulls](https://img.shields.io/docker/pulls/kjanat/pdf-extract-with-ocr?style=for-the-badge)](https://hub.docker.com/r/kjanat/pdf-extract-with-ocr)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/kjanat/pdf-extract-with-ocr/docker-publish.yml?style=for-the-badge)](https://github.com/kjanat/pdf-extract-with-ocr/actions/workflows/docker-publish.yml)

A Flask-based web application that intelligently extracts text from PDF files. It automatically determines whether the PDF contains selectable text or is a scanned document, using [PyMuPDF](https://github.com/pymupdf/PyMuPDF) for direct text extraction and [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for scanned images.

## 🚀 Key Features

- **Smart Text Extraction** - Automatically detects if a PDF has selectable text or needs OCR
- **Multiple Extraction Methods**:
    - Direct text extraction using PyMuPDF for standard PDFs
    - OCR processing with Tesseract for scanned documents
- **Multiple Deployment Options**:
    - Full stack deployment with Docker Compose (recommended)
    - Local installation
    <!-- - Direct Docker image usage -->
- **Multi-architecture Support** - Docker images built for: `amd64`, `arm64`, and `arm/v7`
- **Web Interface and API Access** - Upload PDFs through a browser

## 📦 Installation

=== "Docker Compose"
    The recommended way to run the application is with Docker Compose, which sets up all necessary services (Flask, Redis, PostgreSQL) in a single command.

    <div class="annotate" markdown>

    1. Download the [`docker-compose.yml`][docker-compose.yml] file:

        ```bash
        wget https://raw.githubusercontent.com/kjanat/pdf-extract-with-ocr/docker/docker-compose.yml
        ```

    2. Create a `.env` file optional (1):

        ``` hcl title=".env"
        # API configuration
        API_PORT=8080
        UPLOADS_DIR=./uploads

        # Database configuration
        POSTGRES_USER=ocruser
        POSTGRES_PASSWORD=ocrpass
        POSTGRES_DB=ocr
        DATABASE_URL=postgresql://ocruser:ocrpass@db:5432/ocr

        # Celery configuration
        CELERY_BROKER_URL=redis://redis:6379/0
        ```

    3. Start the services:

        ```bash
        docker-compose up -d
        ```

    4. Open your browser and navigate to http://localhost:8080

    </div>

    1.  Default values will be used if not provided

=== "Clone and Run Locally"
    If you prefer to run the application locally without Docker, you can clone the repository and install the required dependencies.

    **Prerequisites**

    Depending on your system, you may need to install the following dependencies:

    - Python 3.8 or higher
    - pip
    - Tesseract OCR (for OCR processing)
    - SQLite (for local database storage)

    ??? tip "Install Dependencies"

        === ":fontawesome-brands-linux: Linux (Debian/Ubuntu)"

            ``` sh title="Debian/Ubuntu"
            sudo apt-get install -y \
                tesseract-ocr \
                redis-server \
                sqlite3
            ```
        
        === ":fontawesome-brands-windows: Windows"
        
            ``` powershell title="PowerShell (Launch as Administrator)"
            'tesseract-ocr.tesseract', 'SQLite.SQLite' | 
                % { winget install --id=$_ }
            ```
        
        === ":fontawesome-brands-apple: macOS"

            ``` sh title="Homebrew"
            brew install \
                tesseract \
                redis \
                sqlite
            ```

    To run the application locally, you can clone the repository:

    1. Clone the repository:

        ``` bash
        git clone https://github.com/kjanat/pdf-extract-with-ocr.git
        cd pdf-extract-with-ocr
        ```

    2. Install the required dependencies:

        ``` bash
        pip install -r requirements.txt
        ```

    3. Start the flask application on port `8080`:

        ``` bash
        FLASK_RUN_PORT=8080 flask run
        ```

    4. Open your browser and navigate to http://localhost:8080

<!-- === "Direct Docker"

    If you prefer to run the application directly with Docker:

    1. Pull the latest image:

        ```bash
        docker pull kjanat/pdf-extract-with-ocr:api-latest
        ```

    2. Run the container:

        ```bash
        docker run -d -p 8080:8080 kjanat/pdf-extract-with-ocr:api-latest
        ```

    3. Open your browser and navigate to [http://localhost:8080](http://localhost:8080) -->

<!-- === "GitHub Codespaces"

    You can also run the application in GitHub Codespaces:

    1. Click the "Code" button and select "Open with Codespaces".
    2. Once the environment is set up, run the following command:

        ```bash
        docker-compose up -d
        ```

    3. Open your browser and navigate to [http://localhost:8080](http://localhost:8080) -->

## 📚 Documentation

Looking for more detailed information? Check out these guides:

- Running with Docker Compose - Full stack deployment with Docker
- Installation Guide - Installing locally
- API Reference - Using the REST API
- Troubleshooting - Common issues and solutions

## 🛠️ Usage

### 🌐 Web Interface

1. Access the web interface at http://localhost:8080
2. Drag and drop PDF files or click to select files
3. View extracted text in the browser

### 🔗 API

Use the API to extract text programmatically:

``` bash title="Upload PDF"
curl -X POST -F file=@path/to/your/file.pdf http://localhost:8080/upload
```

``` json title="Response example"
{
  "status": "processing",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "filename": "example.pdf"
}
```

To view the result, use the `task_id`:

``` bash title="View result"
curl http://localhost:8080/api/result/a1b2c3d4-e5f6-7890-abcd-1234567890ab
```

``` json title="Response example"
{
  "text": "Extracted text from the PDF here...",
  "status": "success",
  "method": "tesseract",
  "filename": "example.pdf",
  "datetime": "2025-03-21T12:34:56.789012+00:00",
  "duration_ms": 12.3
}
```

The full api documentation is available here: [API Documentation][API].

## 📋 Job History

The application maintains a history of processing jobs, which you can view at http://localhost:8080/jobs.

## 📝 License

© 2025 Kaj Kowalski. All Rights Reserved.

This software and associated documentation files are proprietary. Private use is permitted without restrictions. For commercial use, distribution, or modification, prior written approval from the owner is required.

[API]: api.md "API Documentation"
