"""
Authentication and Authorization Middleware

This module provides API key authentication for protecting endpoints.
"""
import os
import logging
from functools import wraps
from flask import request, jsonify, current_app
from typing import Callable

logger = logging.getLogger(__name__)


def require_api_key(f: Callable) -> Callable:
    """
    Decorator to require API key authentication.

    The API key should be passed in the X-API-Key header.
    If API_KEY environment variable is not set, authentication is disabled.

    Usage:
        @app.route('/protected')
        @require_api_key
        def protected_route():
            return {'message': 'Success'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from environment
        required_api_key = os.getenv('API_KEY')

        # If no API key is configured, allow access (development mode)
        if not required_api_key:
            logger.warning("API_KEY not configured - authentication disabled!")
            return f(*args, **kwargs)

        # Get API key from request header
        provided_api_key = request.headers.get('X-API-Key')

        # Check if API key is provided
        if not provided_api_key:
            logger.warning(f"Missing API key for {request.path}")
            return jsonify({
                'error': 'Missing API key',
                'message': 'Please provide an API key in the X-API-Key header'
            }), 401

        # Validate API key
        if provided_api_key != required_api_key:
            logger.warning(f"Invalid API key attempt for {request.path}")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid'
            }), 401

        # API key is valid, proceed with the request
        return f(*args, **kwargs)

    return decorated_function


def optional_api_key(f: Callable) -> Callable:
    """
    Decorator for optional API key authentication.

    If API key is provided, it must be valid. If not provided, request proceeds.
    Useful for endpoints that have different behavior for authenticated users.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        required_api_key = os.getenv('API_KEY')

        # If no API key is configured, proceed
        if not required_api_key:
            return f(*args, **kwargs)

        # Get API key from request header
        provided_api_key = request.headers.get('X-API-Key')

        # If provided, validate it
        if provided_api_key and provided_api_key != required_api_key:
            logger.warning(f"Invalid API key attempt for {request.path}")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid'
            }), 401

        # Either no key provided (allowed) or valid key provided
        return f(*args, **kwargs)

    return decorated_function


class APIKeyAuth:
    """
    API Key authentication class for more advanced usage.

    Can be used as a decorator or called directly for authentication checks.
    """

    def __init__(self, required: bool = True):
        """
        Initialize API key authenticator.

        Args:
            required: Whether API key is required (default: True)
        """
        self.required = required

    def __call__(self, f: Callable) -> Callable:
        """Allow class to be used as a decorator."""
        if self.required:
            return require_api_key(f)
        else:
            return optional_api_key(f)

    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if current request is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        required_api_key = os.getenv('API_KEY')

        # If no API key configured, consider authenticated
        if not required_api_key:
            return True

        provided_api_key = request.headers.get('X-API-Key')

        return provided_api_key == required_api_key

    @staticmethod
    def get_api_key_status() -> dict:
        """
        Get API key configuration status.

        Returns:
            Dictionary with authentication status information
        """
        required_api_key = os.getenv('API_KEY')

        return {
            'enabled': bool(required_api_key),
            'authenticated': APIKeyAuth.is_authenticated() if required_api_key else None
        }
