"""
Structured Logging Configuration

Provides centralized logging configuration with structured output for better observability.
"""
import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Outputs log records as JSON for easy parsing by log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName',
                'relativeCreated', 'thread', 'threadName', 'exc_info',
                'exc_text', 'stack_info', 'extra_fields'
            ]:
                log_data[key] = value

        return json.dumps(log_data)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to log records.
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log messages."""
        extra = kwargs.get('extra', {})

        # Add context from adapter
        if self.extra:
            extra.update(self.extra)

        kwargs['extra'] = {'extra_fields': extra}
        return msg, kwargs


def configure_logging(
    log_level: str = "INFO",
    use_json: bool = False,
    log_file: str = None
) -> None:
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: If True, use JSON formatter for structured logging
        log_file: Optional log file path
    """
    handlers = {}

    # Console handler
    console_handler = {
        'class': 'logging.StreamHandler',
        'level': log_level,
        'stream': 'ext://sys.stdout',
    }

    if use_json:
        console_handler['formatter'] = 'json'
    else:
        console_handler['formatter'] = 'standard'

    handlers['console'] = console_handler

    # File handler (optional)
    if log_file:
        file_handler = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        }

        if use_json:
            file_handler['formatter'] = 'json'
        else:
            file_handler['formatter'] = 'standard'

        handlers['file'] = file_handler

    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                '()': JSONFormatter,
            },
        },
        'handlers': handlers,
        'root': {
            'level': log_level,
            'handlers': list(handlers.keys()),
        },
        'loggers': {
            # Flask logger
            'flask': {
                'level': log_level,
                'handlers': list(handlers.keys()),
                'propagate': False,
            },
            # SQLAlchemy logger (set to WARNING to reduce noise)
            'sqlalchemy': {
                'level': 'WARNING',
                'handlers': list(handlers.keys()),
                'propagate': False,
            },
            # Celery logger
            'celery': {
                'level': log_level,
                'handlers': list(handlers.keys()),
                'propagate': False,
            },
            # Application loggers
            'services': {
                'level': log_level,
                'handlers': list(handlers.keys()),
                'propagate': False,
            },
            'validators': {
                'level': log_level,
                'handlers': list(handlers.keys()),
                'propagate': False,
            },
            'cleanup': {
                'level': log_level,
                'handlers': list(handlers.keys()),
                'propagate': False,
            },
        },
    }

    logging.config.dictConfig(config)


def get_logger(name: str, **context) -> logging.Logger:
    """
    Get a logger with optional contextual information.

    Args:
        name: Logger name (usually __name__)
        **context: Additional context to include in all log messages

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if context:
        return StructuredLoggerAdapter(logger, context)

    return logger


# Example usage and convenience functions
def log_request(logger: logging.Logger, method: str, path: str, status: int, duration_ms: float):
    """Log HTTP request with structured data."""
    logger.info(
        f"{method} {path} - {status} ({duration_ms:.2f}ms)",
        extra={
            'request_method': method,
            'request_path': path,
            'response_status': status,
            'duration_ms': duration_ms,
            'event_type': 'http_request'
        }
    )


def log_job_created(logger: logging.Logger, job_id: str, filename: str, file_size_kb: float):
    """Log job creation with structured data."""
    logger.info(
        f"Job created: {job_id}",
        extra={
            'job_id': job_id,
            'filename': filename,
            'file_size_kb': file_size_kb,
            'event_type': 'job_created'
        }
    )


def log_job_completed(
    logger: logging.Logger,
    job_id: str,
    status: str,
    duration_ms: int,
    method: str,
    page_count: int
):
    """Log job completion with structured data."""
    logger.info(
        f"Job completed: {job_id} ({status})",
        extra={
            'job_id': job_id,
            'status': status,
            'duration_ms': duration_ms,
            'extraction_method': method,
            'page_count': page_count,
            'event_type': 'job_completed'
        }
    )


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log error with structured data."""
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'event_type': 'error'
    }

    if context:
        error_data.update(context)

    logger.error(
        f"Error: {str(error)}",
        extra=error_data,
        exc_info=True
    )


if __name__ == "__main__":
    # Demo of logging capabilities
    configure_logging(log_level="INFO", use_json=True)

    logger = get_logger(__name__)

    logger.info("Application started")
    log_request(logger, "POST", "/upload", 200, 123.45)
    log_job_created(logger, "abc-123", "test.pdf", 1024.5)
    log_job_completed(logger, "abc-123", "COMPLETED", 5000, "OCR", 3)

    try:
        raise ValueError("Test error")
    except Exception as e:
        log_error(logger, e, {"job_id": "abc-123"})
