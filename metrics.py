"""
Request Metrics Middleware

Provides request/response timing, metrics collection, and observability features.
"""
import time
import logging
from functools import wraps
from typing import Dict, Any, Callable
from flask import request, g, Response
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock

logger = logging.getLogger(__name__)

# Global metrics storage (in-memory for simplicity)
# In production, you'd use Redis, Prometheus, or a proper metrics backend
_metrics = {
    "requests": defaultdict(int),
    "response_times": defaultdict(list),
    "status_codes": defaultdict(int),
    "errors": defaultdict(int),
    "active_requests": 0,
}
_metrics_lock = Lock()


class RequestMetrics:
    """
    Middleware for collecting request metrics and timing information.
    """

    def __init__(self, app=None):
        """Initialize the metrics middleware."""
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the middleware with a Flask app."""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)

    @staticmethod
    def _before_request():
        """Record request start time."""
        g.request_start_time = time.time()

        with _metrics_lock:
            _metrics["active_requests"] += 1

    @staticmethod
    def _after_request(response: Response) -> Response:
        """Record request metrics after response."""
        if not hasattr(g, 'request_start_time'):
            return response

        # Calculate request duration
        duration = time.time() - g.request_start_time
        duration_ms = duration * 1000

        # Get request info
        method = request.method
        path = request.path
        status_code = response.status_code

        # Record metrics
        with _metrics_lock:
            _metrics["requests"][f"{method}:{path}"] += 1
            _metrics["response_times"][f"{method}:{path}"].append(duration_ms)
            _metrics["status_codes"][status_code] += 1

            # Keep only last 1000 response times to prevent memory growth
            if len(_metrics["response_times"][f"{method}:{path}"]) > 1000:
                _metrics["response_times"][f"{method}:{path}"] = \
                    _metrics["response_times"][f"{method}:{path}"][-1000:]

        # Add timing header to response
        response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"

        # Log slow requests (> 1 second)
        if duration > 1.0:
            logger.warning(
                f"Slow request: {method} {path} took {duration_ms:.2f}ms",
                extra={
                    'request_method': method,
                    'request_path': path,
                    'duration_ms': duration_ms,
                    'status_code': status_code,
                    'event_type': 'slow_request'
                }
            )

        # Log request
        logger.info(
            f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
            extra={
                'request_method': method,
                'request_path': path,
                'response_status': status_code,
                'duration_ms': duration_ms,
                'event_type': 'http_request'
            }
        )

        return response

    @staticmethod
    def _teardown_request(exception=None):
        """Clean up after request."""
        with _metrics_lock:
            _metrics["active_requests"] = max(0, _metrics["active_requests"] - 1)

        if exception:
            # Log exception
            logger.error(
                f"Request failed with exception: {exception}",
                extra={
                    'request_method': request.method if request else None,
                    'request_path': request.path if request else None,
                    'exception_type': type(exception).__name__,
                    'event_type': 'request_exception'
                },
                exc_info=True
            )

            with _metrics_lock:
                _metrics["errors"][type(exception).__name__] += 1


def get_metrics() -> Dict[str, Any]:
    """
    Get current metrics snapshot.

    Returns:
        Dictionary with current metrics
    """
    with _metrics_lock:
        # Calculate statistics for response times
        response_time_stats = {}
        for endpoint, times in _metrics["response_times"].items():
            if times:
                response_time_stats[endpoint] = {
                    "count": len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "avg_ms": sum(times) / len(times),
                    "p50_ms": sorted(times)[len(times) // 2],
                    "p95_ms": sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times),
                    "p99_ms": sorted(times)[int(len(times) * 0.99)] if len(times) > 100 else max(times),
                }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_requests": _metrics["active_requests"],
            "total_requests": dict(_metrics["requests"]),
            "response_times": response_time_stats,
            "status_codes": dict(_metrics["status_codes"]),
            "errors": dict(_metrics["errors"]),
        }


def reset_metrics():
    """Reset all metrics to initial state."""
    with _metrics_lock:
        _metrics["requests"].clear()
        _metrics["response_times"].clear()
        _metrics["status_codes"].clear()
        _metrics["errors"].clear()
        _metrics["active_requests"] = 0


def track_operation(operation_name: str):
    """
    Decorator to track operation timing.

    Usage:
        @track_operation("pdf_processing")
        def process_pdf(path):
            # ... processing logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                duration_ms = duration * 1000

                # Log operation
                if error:
                    logger.error(
                        f"Operation {operation_name} failed after {duration_ms:.2f}ms: {error}",
                        extra={
                            'operation_name': operation_name,
                            'duration_ms': duration_ms,
                            'error': str(error),
                            'event_type': 'operation_failed'
                        }
                    )
                else:
                    logger.info(
                        f"Operation {operation_name} completed in {duration_ms:.2f}ms",
                        extra={
                            'operation_name': operation_name,
                            'duration_ms': duration_ms,
                            'event_type': 'operation_completed'
                        }
                    )

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Demo metrics collection
    import json

    print("Metrics Demo:")
    print("=" * 50)

    # Simulate some requests
    with _metrics_lock:
        _metrics["requests"]["GET:/api/jobs"] = 100
        _metrics["requests"]["POST:/upload"] = 50
        _metrics["response_times"]["GET:/api/jobs"] = [45.2, 52.1, 48.3, 51.0, 49.5]
        _metrics["response_times"]["POST:/upload"] = [150.0, 200.5, 175.3]
        _metrics["status_codes"][200] = 140
        _metrics["status_codes"][400] = 8
        _metrics["status_codes"][500] = 2
        _metrics["errors"]["ValueError"] = 2
        _metrics["active_requests"] = 3

    # Get metrics
    metrics = get_metrics()
    print(json.dumps(metrics, indent=2))
