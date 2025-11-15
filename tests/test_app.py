"""Tests for Flask application routes."""
import pytest
from io import BytesIO


def test_index_route(client):
    """Test the index route returns the HTML page."""
    response = client.get('/')
    assert response.status_code == 200


def test_jobs_route(client):
    """Test the jobs page route."""
    response = client.get('/jobs')
    assert response.status_code == 200


def test_upload_no_file(client):
    """Test upload endpoint with no file."""
    response = client.post('/upload')
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'No file uploaded'


def test_upload_empty_filename(client):
    """Test upload with empty filename."""
    data = {'file': (BytesIO(b''), '')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'No selected file'


def test_upload_non_pdf(client):
    """Test upload with non-PDF file."""
    data = {'file': (BytesIO(b'test content'), 'test.txt')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'Only PDF files are allowed'


def test_upload_empty_file(client):
    """Test upload with empty PDF file."""
    data = {'file': (BytesIO(b''), 'test.pdf')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'File is empty'


def test_get_jobs(client):
    """Test getting list of jobs."""
    response = client.get('/api/jobs')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_get_result_not_found(client):
    """Test getting result for non-existent job."""
    response = client.get('/api/result/nonexistent-id')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


def test_check_status_not_found(client):
    """Test checking status for non-existent job."""
    response = client.get('/status/nonexistent-id')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert data['state'] == 'FAILED'
