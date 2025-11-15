"""
PDF Extract with OCR - Main Application

This is the main entry point for the Flask application using the factory pattern.
"""
import os
from factory import create_app
from utils import check_stalled_jobs

# Create the application instance
app = create_app()

# Check for stalled jobs on startup
with app.app_context():
    check_stalled_jobs()

if __name__ == '__main__':
    from waitress import serve
    from settings import IS_DOCKER

    if IS_DOCKER:
        host = os.getenv("FLASK_HOST", "0.0.0.0")
        port = int(os.getenv("FLASK_PORT", 80))
    else:
        host = os.getenv("FLASK_HOST", "127.0.0.1")
        port = int(os.getenv("FLASK_PORT", 8080))

    app.logger.info(f"Starting server on {host}:{port}")
    serve(app, host=host, port=port)
