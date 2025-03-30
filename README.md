<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD041 -->

<div align="center">

# PDF Extract with OCR

</div>

<div align="center" style="padding: 2vh 10vw 1vh 10vw; display: flex; flex-basis: auto; flex-wrap: wrap; flex-shrink: 1; flex-flow: row wrap; float: inline-flex; justify-content: space-around; justify-items: center;">

[![Commits](https://img.shields.io/github/commit-activity/m/kjanat/pdf-extract-with-ocr?label=commits&style=for-the-badge)][GitHub Commits]
[![GitHub last commit](https://img.shields.io/github/last-commit/kjanat/pdf-extract-with-ocr?style=for-the-badge&display_timestamp=committer)][GitHub Monthly]
[![Docker Pulls](https://img.shields.io/docker/pulls/kjanat/pdf-extract-with-ocr?style=for-the-badge)][Docker]
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/kjanat/pdf-extract-with-ocr/docker-publish.yml?style=for-the-badge)][Build Status]

</div>

This project is a Flask-based web application that extracts text from PDF files. It determines whether the PDF contains selectable text or is a scanned document, using  for direct text extraction and  for scanned images.

## Features

- Extracts text from PDFs with selectable text using
- Detects scanned PDFs and applies OCR with
- Automatic Tesseract installation check and language data download
- Returns extracted text in a structured JSON format
- Provides processing time and extraction method details

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

© 2025 Kaj Kowalski. All Rights Reserved.

This software and associated documentation files are proprietary. Private use is permitted without restrictions. For commercial use, distribution, or modification, prior written approval from the owner is required.

<!-- [GitHub License]: #license "Not licensed" -->

[GitHub Commits]: https://github.com/kjanat/pdf-extract-with-ocr/commits
[GitHub Monthly]: https://github.com/kjanat/pdf-extract-with-ocr/pulse/monthly
[Docker]: https://hub.docker.com/r/kjanat/pdf-extract-with-ocr
[Build Status]: https://github.com/kjanat/pdf-extract-with-ocr/actions/workflows/ci.yml
