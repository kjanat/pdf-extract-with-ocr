"""
Flask Routes

This module defines all application routes organized into blueprints.
"""
import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from typing import Optional
from io import BytesIO

from db import SessionLocal, OCRJob
from tasks import process_pdf_task
from middleware import require_api_key, optional_api_key
from storage import storage

# Create blueprints
api_bp = Blueprint('api', __name__, url_prefix='/api')
pages_bp = Blueprint('pages', __name__)


# ============================================================================
# PAGE ROUTES
# ============================================================================

@pages_bp.route('/')
def index():
    """Serve the main upload page."""
    return send_from_directory('static', 'index.html')


@pages_bp.route('/jobs')
def jobs_view():
    """Serve the jobs listing page."""
    return send_from_directory('static', 'jobs.html')


# ============================================================================
# HEALTH CHECK ROUTES
# ============================================================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.

    Returns:
        200 if the application is running
    """
    return jsonify({
        "status": "healthy",
        "service": "pdf-extract-with-ocr"
    }), 200


@api_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check endpoint that verifies database connectivity.

    Returns:
        200 if the application is ready to serve requests
        503 if the application is not ready
    """
    try:
        # Test database connection
        with SessionLocal() as session:
            session.execute("SELECT 1")

        return jsonify({
            "status": "ready",
            "database": "connected"
        }), 200
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {e}")
        return jsonify({
            "status": "not ready",
            "database": "disconnected",
            "error": str(e)
        }), 503


# ============================================================================
# PDF UPLOAD ROUTE
# ============================================================================

@pages_bp.route('/upload', methods=['POST'])
@optional_api_key
def upload_pdf():
    """
    Upload and process a PDF file.

    Rate limited to 10 uploads per minute.
    Maximum file size: 50MB (configured in factory.py)

    Note: Currently saves to local filesystem for processing.
    TODO: Integrate with storage backend for S3/MinIO support.
    """
    # Get limiter from app extensions
    limiter = current_app.extensions.get('limiter')
    if limiter:
        limiter.check()  # This will raise 429 if limit exceeded

    try:
        current_app.logger.info("Received a file upload request")
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "No selected file"}), 400

        # Validate file extension
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        # Validate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer

        max_size = current_app.config.get('MAX_FILE_SIZE', 50 * 1024 * 1024)
        if file_size > max_size:
            return jsonify({
                "error": f"File too large. Maximum size is {max_size // (1024 * 1024)}MB"
            }), 413

        if file_size == 0:
            return jsonify({"error": "File is empty"}), 400

        sanitized_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}.{sanitized_filename.split('.')[-1]}"
        temp_path = os.path.join("uploads", unique_filename)
        os.makedirs("uploads", exist_ok=True)

        try:
            file.save(temp_path)
        except Exception as e:
            current_app.logger.error(f"Failed to save file: {e}", exc_info=True)
            return jsonify({"error": "Failed to save file. Please try again."}), 500

        task = process_pdf_task.delay(temp_path)

        with SessionLocal() as session:
            job = OCRJob(
                id=task.id,
                filename=file.filename,
                status="PENDING",
                created_at=datetime.now(timezone.utc)
            )
            session.add(job)
            session.commit()

        return jsonify({
            "status": "processing",
            "task_id": task.id,
            "filename": file.filename
        })
    except Exception as e:
        current_app.logger.error(f"Error in upload endpoint: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while processing your upload. Please try again."}), 500


# ============================================================================
# JOB MANAGEMENT ROUTES
# ============================================================================

@api_bp.route('/jobs', methods=['GET'])
@optional_api_key
def get_jobs():
    """
    Get a list of recent OCR jobs.

    Returns:
        JSON array of jobs, ordered by creation date (most recent first)
    """
    with SessionLocal() as session:
        jobs = session.query(OCRJob).order_by(OCRJob.created_at.desc()).limit(20).all()

    return jsonify([
        {
            "id": job.id,
            "filename": job.filename,
            "status": job.status,
            "method": job.method,
            "duration_ms": job.duration_ms,
            "created_at": job.created_at.isoformat(),
            "page_count": job.page_count,
            "file_size_kb": job.file_size_kb,
            "error_message": job.error_message
        } for job in jobs
    ])


@api_bp.route('/result/<task_id>', methods=['GET'])
@optional_api_key
def get_result(task_id: str):
    """
    Get the result of a completed OCR job.

    Args:
        task_id: The unique job identifier

    Returns:
        JSON object with job details and extracted text
        404 if job not found
    """
    with SessionLocal() as session:
        job = session.query(OCRJob).filter(OCRJob.id == task_id).first()

    if not job:
        response = jsonify({"error": "Job not found", "state": "FAILED"})
        response.status_code = 404
        return response

    return jsonify({
        "id": job.id,
        "filename": job.filename,
        "status": job.status,
        "method": job.method,
        "text": job.result_text,
        "duration_ms": job.duration_ms,
        "created_at": job.created_at.isoformat(),
        "page_count": job.page_count,
        "file_size_kb": job.file_size_kb,
        "error_message": job.error_message
    })


@api_bp.route('/status/<task_id>', methods=['GET'])
@optional_api_key
def check_status(task_id: str):
    """
    Check the status of an OCR job.

    Args:
        task_id: The unique job identifier

    Returns:
        JSON object with job status
        404 if job not found
    """
    with SessionLocal() as session:
        job: Optional[OCRJob] = session.query(OCRJob).filter(OCRJob.id == task_id).first()

    if not job:
        response = jsonify({"error": "Job not found", "state": "FAILED"})
        response.status_code = 404
        return response

    return jsonify({
        "state": job.status,
        "method": job.method,
        "text": job.result_text,
        "duration_ms": job.duration_ms,
        "created_at": job.created_at.isoformat(),
        "error_message": job.error_message
    })
