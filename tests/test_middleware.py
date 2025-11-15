"""
Tests for API key authentication middleware
"""
import os
import pytest
from flask import Flask, jsonify
from middleware import require_api_key, optional_api_key


@pytest.fixture
def app():
    """Create a test Flask app with authentication"""
    app = Flask(__name__)

    @app.route('/protected')
    @require_api_key
    def protected_route():
        return jsonify({"message": "success"})

    @app.route('/optional')
    @optional_api_key
    def optional_route():
        return jsonify({"message": "success"})

    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


def test_require_api_key_with_valid_key(client, monkeypatch):
    """Test that require_api_key allows access with valid API key"""
    monkeypatch.setenv("API_KEY", "test-api-key-123")

    response = client.get('/protected', headers={'X-API-Key': 'test-api-key-123'})
    assert response.status_code == 200
    assert response.json == {"message": "success"}


def test_require_api_key_with_invalid_key(client, monkeypatch):
    """Test that require_api_key denies access with invalid API key"""
    monkeypatch.setenv("API_KEY", "test-api-key-123")

    response = client.get('/protected', headers={'X-API-Key': 'wrong-key'})
    assert response.status_code == 401
    assert 'error' in response.json


def test_require_api_key_with_missing_key(client, monkeypatch):
    """Test that require_api_key denies access without API key"""
    monkeypatch.setenv("API_KEY", "test-api-key-123")

    response = client.get('/protected')
    assert response.status_code == 401
    assert 'error' in response.json


def test_require_api_key_when_not_configured(client, monkeypatch):
    """Test that require_api_key allows access when API_KEY is not configured"""
    # Remove API_KEY from environment
    monkeypatch.delenv("API_KEY", raising=False)

    response = client.get('/protected')
    assert response.status_code == 200
    assert response.json == {"message": "success"}


def test_optional_api_key_with_valid_key(client, monkeypatch):
    """Test that optional_api_key allows access with valid API key"""
    monkeypatch.setenv("API_KEY", "test-api-key-123")

    response = client.get('/optional', headers={'X-API-Key': 'test-api-key-123'})
    assert response.status_code == 200
    assert response.json == {"message": "success"}


def test_optional_api_key_with_invalid_key(client, monkeypatch):
    """Test that optional_api_key denies access with invalid API key"""
    monkeypatch.setenv("API_KEY", "test-api-key-123")

    response = client.get('/optional', headers={'X-API-Key': 'wrong-key'})
    assert response.status_code == 401
    assert 'error' in response.json


def test_optional_api_key_without_key_when_not_configured(client, monkeypatch):
    """Test that optional_api_key allows access without key when not configured"""
    # Remove API_KEY from environment
    monkeypatch.delenv("API_KEY", raising=False)

    response = client.get('/optional')
    assert response.status_code == 200
    assert response.json == {"message": "success"}


def test_optional_api_key_without_key_when_configured(client, monkeypatch):
    """Test that optional_api_key allows access without key even when configured"""
    monkeypatch.setenv("API_KEY", "test-api-key-123")

    # optional_api_key allows access without a key (it's optional)
    response = client.get('/optional')
    # Based on the implementation, optional_api_key allows access even without the key
    assert response.status_code == 200
    assert response.json == {"message": "success"}
