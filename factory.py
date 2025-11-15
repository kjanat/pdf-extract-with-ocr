"""
Flask Application Factory

This module implements the application factory pattern for better testability
and configuration management.
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from typing import Optional

from db import init_db
from settings import IS_DOCKER


def create_app(config: Optional[dict] = None) -> Flask:
    """
    Application factory for creating Flask app instances.

    Args:
        config: Optional configuration dictionary to override defaults

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load default configuration
    app.config.update(
        MAX_FILE_SIZE=50 * 1024 * 1024,  # 50MB
        ALLOWED_ORIGINS=os.getenv("ALLOWED_ORIGINS", "*"),
        RATE_LIMIT_STORAGE_URL=os.getenv("RATE_LIMIT_STORAGE_URL", "memory://"),
    )

    # Override with provided config
    if config:
        app.config.update(config)

    # Configure logging
    if IS_DOCKER:
        app.logger.setLevel("WARNING")
    else:
        app.logger.setLevel("INFO")
        app.logger.info("Running in local development mode")

    # Configure CORS
    allowed_origins = app.config["ALLOWED_ORIGINS"].split(",")
    CORS(app, origins=allowed_origins if allowed_origins != ["*"] else "*")

    # Configure rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config["RATE_LIMIT_STORAGE_URL"]
    )

    # Store limiter in app extensions
    app.extensions['limiter'] = limiter

    # Register blueprints
    from routes import api_bp, pages_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)

    # Register error handlers
    register_error_handlers(app)

    # Initialize database
    with app.app_context():
        init_db()

    return app


def register_error_handlers(app: Flask):
    """Register error handlers for the application."""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({"error": "File too large"}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
