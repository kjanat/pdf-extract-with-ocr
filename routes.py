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
from sqlalchemy import desc

from db import SessionLocal, OCRJob
from tasks import process_pdf_task
from middleware import require_api_key, optional_api_key
from storage import storage
from validators import (
    validate_file_upload,
    sanitize_filename,
    validate_task_id,
    validate_pagination_params,
    ValidationError
)
from metrics import get_metrics

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
            "error": "An internal error has occurred."
        }), 503


@api_bp.route('/metrics', methods=['GET'])
@optional_api_key
def metrics_endpoint():
    """
    Get application metrics.

    Returns:
        200 with metrics data
    """
    try:
        metrics_data = get_metrics()
        return jsonify(metrics_data), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching metrics: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to fetch metrics",
            "code": "METRICS_ERROR"
        }), 500


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
        current_app.logger.info("Received file upload request")

        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                "error": "No file uploaded",
                "code": "NO_FILE"
            }), 400

        file = request.files['file']

        # Comprehensive file validation
        try:
            validate_file_upload(file)
        except ValidationError as e:
            current_app.logger.warning(f"File validation failed: {e.message}")
            return jsonify({
                "error": e.message,
                "code": e.code
            }), 400

        # Sanitize and generate unique filename
        sanitized = sanitize_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}.pdf"
        temp_path = os.path.join("uploads", unique_filename)
        os.makedirs("uploads", exist_ok=True)

        # Save file
        try:
            file.save(temp_path)
            current_app.logger.info(f"File saved: {unique_filename} (original: {file.filename})")
        except Exception as e:
            current_app.logger.error(f"Failed to save file: {e}", exc_info=True)
            return jsonify({
                "error": "Failed to save file. Please try again.",
                "code": "SAVE_ERROR"
            }), 500

        # Queue processing task
        task = process_pdf_task.delay(temp_path)

        # Create database record
        with SessionLocal() as session:
            job = OCRJob(
                id=task.id,
                filename=file.filename,
                status="PENDING",
                created_at=datetime.now(timezone.utc)
            )
            session.add(job)
            session.commit()

        current_app.logger.info(f"Job created: {task.id} for file: {file.filename}")

        return jsonify({
            "status": "processing",
            "task_id": task.id,
            "filename": file.filename
        })

    except ValidationError as e:
        # Validation errors are already handled above
        return jsonify({
            "error": e.message,
            "code": e.code
        }), 400

    except Exception as e:
        current_app.logger.error(f"Unexpected error in upload endpoint: {e}", exc_info=True)
        return jsonify({
            "error": "An unexpected error occurred. Please try again.",
            "code": "INTERNAL_ERROR"
        }), 500


# ============================================================================
# JOB MANAGEMENT ROUTES
# ============================================================================

@api_bp.route('/jobs', methods=['GET'])
@optional_api_key
def get_jobs():
    """
    Get a paginated list of OCR jobs.

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)
        status (str): Filter by status (optional)

    Returns:
        JSON object with jobs array and pagination metadata
    """
    try:
        # Get and validate pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', None, type=str)

        try:
            page, per_page = validate_pagination_params(page, per_page)
        except ValidationError as e:
            return jsonify({
                "error": e.message,
                "code": e.code
            }), 400

        with SessionLocal() as session:
            # Base query
            query = session.query(OCRJob).order_by(desc(OCRJob.created_at))

            # Apply status filter if provided
            if status_filter:
                valid_statuses = ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']
                if status_filter.upper() in valid_statuses:
                    query = query.filter(OCRJob.status == status_filter.upper())
                else:
                    return jsonify({
                        "error": f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}",
                        "code": "INVALID_STATUS_FILTER"
                    }), 400

            # Get total count
            total = query.count()

            # Apply pagination
            offset = (page - 1) * per_page
            jobs = query.offset(offset).limit(per_page).all()

            # Calculate pagination metadata
            total_pages = (total + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1

            return jsonify({
                "jobs": [
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
                ],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            })

    except Exception as e:
        current_app.logger.error(f"Error in get_jobs endpoint: {e}", exc_info=True)
        return jsonify({
            "error": "An error occurred while fetching jobs",
            "code": "INTERNAL_ERROR"
        }), 500


@api_bp.route('/result/<task_id>', methods=['GET'])
@optional_api_key
def get_result(task_id: str):
    """
    Get the result of a completed OCR job.

    Args:
        task_id: The unique job identifier

    Returns:
        JSON object with job details and extracted text
        400 if task_id is invalid
        404 if job not found
    """
    try:
        # Validate task_id format
        try:
            validate_task_id(task_id)
        except ValidationError as e:
            return jsonify({
                "error": e.message,
                "code": e.code
            }), 400

        with SessionLocal() as session:
            job = session.query(OCRJob).filter(OCRJob.id == task_id).first()

        if not job:
            return jsonify({
                "error": "Job not found",
                "code": "JOB_NOT_FOUND"
            }), 404

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

    except Exception as e:
        current_app.logger.error(f"Error in get_result endpoint: {e}", exc_info=True)
        return jsonify({
            "error": "An error occurred while fetching job result",
            "code": "INTERNAL_ERROR"
        }), 500


@api_bp.route('/status/<task_id>', methods=['GET'])
@optional_api_key
def check_status(task_id: str):
    """
    Check the status of an OCR job.

    Args:
        task_id: The unique job identifier

    Returns:
        JSON object with job status
        400 if task_id is invalid
        404 if job not found
    """
    try:
        # Validate task_id format
        try:
            validate_task_id(task_id)
        except ValidationError as e:
            return jsonify({
                "error": e.message,
                "code": e.code
            }), 400

        with SessionLocal() as session:
            job: Optional[OCRJob] = session.query(OCRJob).filter(OCRJob.id == task_id).first()

        if not job:
            return jsonify({
                "error": "Job not found",
                "code": "JOB_NOT_FOUND"
            }), 404

        return jsonify({
            "state": job.status,
            "method": job.method,
            "text": job.result_text,
            "duration_ms": job.duration_ms,
            "created_at": job.created_at.isoformat(),
            "error_message": job.error_message
        })

    except Exception as e:
        current_app.logger.error(f"Error in check_status endpoint: {e}", exc_info=True)
        return jsonify({
            "error": "An error occurred while checking job status",
            "code": "INTERNAL_ERROR"
        }), 500
