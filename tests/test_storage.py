"""
Tests for storage backends
"""
import os
import pytest
import tempfile
import shutil
from io import BytesIO
from storage import LocalStorage, get_storage_backend


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def local_storage(temp_dir):
    """Create a LocalStorage instance with temp directory"""
    return LocalStorage(base_path=temp_dir)


class TestLocalStorage:
    """Tests for LocalStorage backend"""

    def test_save_file(self, local_storage, temp_dir):
        """Test saving a file to local storage"""
        content = b"Test PDF content"
        file_obj = BytesIO(content)
        filename = "test.pdf"

        filepath = local_storage.save_file(file_obj, filename)

        assert filepath == os.path.join(temp_dir, filename)
        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            assert f.read() == content

    def test_get_file(self, local_storage, temp_dir):
        """Test retrieving a file from local storage"""
        content = b"Test PDF content"
        filename = "test.pdf"
        filepath = os.path.join(temp_dir, filename)

        # Create a test file
        with open(filepath, 'wb') as f:
            f.write(content)

        retrieved_content = local_storage.get_file(filename)
        assert retrieved_content == content

    def test_get_file_not_found(self, local_storage):
        """Test retrieving a non-existent file raises an error"""
        with pytest.raises(Exception):
            local_storage.get_file("nonexistent.pdf")

    def test_delete_file(self, local_storage, temp_dir):
        """Test deleting a file from local storage"""
        filename = "test.pdf"
        filepath = os.path.join(temp_dir, filename)

        # Create a test file
        with open(filepath, 'wb') as f:
            f.write(b"Test content")

        assert local_storage.file_exists(filename)
        result = local_storage.delete_file(filename)

        assert result is True
        assert not os.path.exists(filepath)

    def test_delete_nonexistent_file(self, local_storage):
        """Test deleting a non-existent file returns False"""
        result = local_storage.delete_file("nonexistent.pdf")
        assert result is False

    def test_file_exists(self, local_storage, temp_dir):
        """Test checking if a file exists"""
        filename = "test.pdf"
        filepath = os.path.join(temp_dir, filename)

        assert not local_storage.file_exists(filename)

        # Create a test file
        with open(filepath, 'wb') as f:
            f.write(b"Test content")

        assert local_storage.file_exists(filename)


class TestStorageBackendFactory:
    """Tests for get_storage_backend factory function"""

    def test_get_local_storage_by_default(self, monkeypatch):
        """Test that get_storage_backend returns LocalStorage by default"""
        monkeypatch.delenv("USE_S3", raising=False)

        backend = get_storage_backend()
        assert isinstance(backend, LocalStorage)

    def test_get_local_storage_explicitly(self, monkeypatch):
        """Test that get_storage_backend returns LocalStorage when USE_S3=false"""
        monkeypatch.setenv("USE_S3", "false")

        backend = get_storage_backend()
        assert isinstance(backend, LocalStorage)

    def test_s3_storage_requires_bucket(self, monkeypatch):
        """Test that S3 storage requires S3_BUCKET environment variable"""
        monkeypatch.setenv("USE_S3", "true")
        monkeypatch.delenv("S3_BUCKET", raising=False)

        with pytest.raises(ValueError, match="S3_BUCKET environment variable is required"):
            get_storage_backend()


# Note: S3Storage tests would require mocking boto3 or using moto for S3 mocking
# These tests are skipped for now but can be added with:
# @pytest.mark.skipif(not HAS_BOTO3, reason="boto3 not installed")
# or using moto: @mock_s3
