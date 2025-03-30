# Running from Source

This guide explains how to install and run PDF Extract with OCR directly on your host system without containers.

## Prerequisites

Before installing, ensure you have the following requirements:

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

### System Dependencies

Install the required system dependencies based on your operating system:

=== ":fontawesome-brands-linux: Linux (Debian/Ubuntu)"

    ```sh
    sudo apt-get install -y \
        tesseract-ocr \
        redis-server \
        sqlite3
    ```

=== ":fontawesome-brands-windows: Windows"

    ```powershell
    # Using winget (run as Administrator)
    'tesseract-ocr.tesseract', 'SQLite.SQLite' | 
        % { winget install --id=$_ }
    ```

    For Redis, you can either:

    - Install using [Redis Windows](https://github.com/tporadowski/redis/releases)
    - Use the Windows Subsystem for Linux (WSL)
    - Skip Redis by using a SQLite-based task queue

=== ":fontawesome-brands-apple: macOS"

    ```sh
    # Using Homebrew
    brew install \
        tesseract \
        redis \
        sqlite
    ```

## Installation Steps

1. Clone the repository (or download the source code):

    ```sh
    git clone https://github.com/kjanat/pdf-extract-with-ocr.git
    cd pdf-extract-with-ocr
    ```

2. Create a virtual environment and activate it:

    === ":fontawesome-brands-linux: Linux (Debian/Ubuntu)"

        ```sh
        # Create virtual environment
        python3 -m venv venv

        # Activate virtual environment
        source venv/bin/activate
        ```

    === ":fontawesome-brands-windows: Windows"

        ```pwsh
        # Create virtual environment
        python -m venv venv

        # Activate on Windows
        .\venv\Scripts\Activate.ps1
        ```

    === ":fontawesome-brands-apple: macOS"

        ```sh
        # Create virtual environment
        python3 -m venv venv

        # Activate virtual environment
        source venv/bin/activate
        ```

3. Install the required Python dependencies:

    ```sh
    pip install -U -r requirements.txt
    ```

## Configuration

1. Create a `.env` file by copying the example file:

    ```sh
    cp .env.example .env
    ```

2. Edit the `.env` file to set your configuration options:

    ```yaml title=".env"
    # API configuration
    API_PORT=8080
    UPLOADS_DIR=./uploads

    # Database configuration (choose SQLite or PostgreSQL)
    # For SQLite:
    DATABASE_URL=sqlite:///local.db
    # For PostgreSQL:
    # DATABASE_URL=postgresql://user:password@localhost:5432/ocr

    # Celery configuration
    CELERY_BROKER_URL=redis://localhost:6379/0
    ```

## Running the Application

### Option 1: Run the Flask application only

For simple usage where background processing isn't needed:

=== ":fontawesome-brands-linux: Linux (Debian/Ubuntu)"

    ```sh
    # Activate the virtual environment (if not already activated)
    source venv/bin/activate

    # Set the port (optional, defaults to 5000)
    export FLASK_RUN_PORT=8080

    # Run the application
    python app.py
    # Or alternatively:
    # flask run
    ```

=== ":fontawesome-brands-windows: Windows"

    ```pwsh
    # Activate the virtual environment (if not already activated)
    .\venv\Scripts\Activate.ps1

    # Set the port (optional, defaults to 5000)
    $env:FLASK_RUN_PORT=8080

    # Run the application
    python app.py
    # Or alternatively:
    # flask run
    ```

=== ":fontawesome-brands-apple: macOS"

    ```sh
    # Activate the virtual environment (if not already activated)
    source venv/bin/activate
    
    # Set the port (optional, defaults to 5000)
    export FLASK_RUN_PORT=8080
    
    # Run the application
    python app.py
    # Or alternatively:
    # flask run
    ```

### Option 2: Run with background processing (recommended)

For optimal performance with background task processing:

1. Start Redis (if not already running):

    ```sh
    # On Linux/macOS
    redis-server

    # On Windows (if installed as a service)
    # It may already be running as a service
    ```

2. Start the Celery worker in a separate terminal:

    ```sh
    # Make sure your virtual environment is activated
    celery -A celery_worker.celery worker --loglevel=info
    ```

3. Start the Flask application:

    ```sh
    python app.py
    ```

## Accessing the Application

Once running, you can access:

- Web interface: http://localhost:8080 (or the port you configured)
- API endpoint: http://localhost:8080/upload

## Troubleshooting

### Common Issues

1. **Tesseract not found**: Ensure Tesseract is installed and in your PATH
2. **Redis connection errors**: Verify Redis is running (`redis-cli ping` should return PONG)
3. **Database errors**: Check your database configuration in `.env`

### Logs

Check the application logs for more detailed error information:

```sh
# Application logs are printed to the console
# Celery worker logs are in the worker terminal
```

For more help, refer to the [GitHub repository](https://github.com/kjanat/pdf-extract-with-ocr) or open an issue.
