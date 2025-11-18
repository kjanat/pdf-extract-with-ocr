"""
Input Validation Module

Provides comprehensive validation for file uploads and request parameters.
"""
import os
import magic
import logging
from typing import Optional, Tuple
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/x-pdf',
}
ALLOWED_EXTENSIONS = {'.pdf'}


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


def validate_file_upload(file: FileStorage) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive file upload validation.

    Args:
        file: The uploaded file object

    Returns:
        Tuple of (is_valid, error_message)

    Raises:
        ValidationError: If validation fails
    """
    # Check if file exists
    if not file:
        raise ValidationError("No file provided", "NO_FILE")

    # Check if filename exists
    if not file.filename or file.filename == '':
        raise ValidationError("No filename provided", "NO_FILENAME")

    # Check file extension
    filename = file.filename.lower()
    file_ext = os.path.splitext(filename)[1]

    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Invalid file extension. Only PDF files are allowed. Got: {file_ext}",
            "INVALID_EXTENSION"
        )

    # Check filename for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValidationError(
            "Invalid filename: path traversal detected",
            "INVALID_FILENAME"
        )

    # Read file content to check size and MIME type
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    # Check file size
    if file_size == 0:
        raise ValidationError("File is empty", "EMPTY_FILE")

    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise ValidationError(
            f"File too large: {size_mb:.2f}MB (max: {max_mb}MB)",
            "FILE_TOO_LARGE"
        )

    # Check MIME type using python-magic
    try:
        file_content = file.read(2048)  # Read first 2KB for MIME detection
        file.seek(0)  # Reset to beginning

        mime = magic.from_buffer(file_content, mime=True)

        if mime not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"Invalid file type. Expected PDF, got: {mime}",
                "INVALID_MIME_TYPE"
            )

        # Additional PDF header check
        if not file_content.startswith(b'%PDF'):
            raise ValidationError(
                "File does not appear to be a valid PDF (missing PDF header)",
                "INVALID_PDF_HEADER"
            )

    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        logger.error(f"Error during MIME type detection: {e}", exc_info=True)
        raise ValidationError(
            "Failed to validate file type",
            "MIME_DETECTION_ERROR"
        )

    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues.

    Args:
        filename: The original filename

    Returns:
        Sanitized filename safe for filesystem operations
    """
    # Remove path components
    filename = os.path.basename(filename)

    # Remove or replace dangerous characters
    dangerous_chars = ['..', '/', '\\', '\0', '\n', '\r', '\t']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')

    # Limit filename length (keep extension)
    name, ext = os.path.splitext(filename)
    max_name_length = 200
    if len(name) > max_name_length:
        name = name[:max_name_length]

    return f"{name}{ext}"


def validate_task_id(task_id: str) -> bool:
    """
    Validate task ID format.

    Args:
        task_id: The task ID to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if not task_id:
        raise ValidationError("Task ID is required", "NO_TASK_ID")

    # Check length (UUIDs are 36 chars with hyphens)
    if len(task_id) < 8 or len(task_id) > 128:
        raise ValidationError(
            "Invalid task ID length",
            "INVALID_TASK_ID_LENGTH"
        )

    # Check for SQL injection patterns
    dangerous_patterns = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
    task_id_upper = task_id.upper()
    for pattern in dangerous_patterns:
        if pattern in task_id_upper:
            raise ValidationError(
                "Invalid task ID format",
                "INVALID_TASK_ID_FORMAT"
            )

    return True


def validate_pagination_params(
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Tuple[int, int]:
    """
    Validate and sanitize pagination parameters.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum allowed items per page

    Returns:
        Tuple of (validated_page, validated_per_page)

    Raises:
        ValidationError: If validation fails
    """
    try:
        page = int(page)
        per_page = int(per_page)
    except (TypeError, ValueError):
        raise ValidationError(
            "Pagination parameters must be integers",
            "INVALID_PAGINATION_TYPE"
        )

    if page < 1:
        raise ValidationError(
            "Page number must be >= 1",
            "INVALID_PAGE_NUMBER"
        )

    if per_page < 1:
        raise ValidationError(
            "Items per page must be >= 1",
            "INVALID_PER_PAGE"
        )

    if per_page > max_per_page:
        logger.warning(f"Requested per_page {per_page} exceeds max {max_per_page}, capping")
        per_page = max_per_page

    return page, per_page
