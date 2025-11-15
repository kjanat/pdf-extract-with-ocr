"""
Object Storage Module

Provides abstraction for file storage with support for local filesystem and S3/MinIO.
"""
import os
import logging
from typing import BinaryIO, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_file(self, file_obj: BinaryIO, filename: str) -> str:
        """
        Save a file to storage.

        Args:
            file_obj: File-like object to save
            filename: Destination filename

        Returns:
            Path or URL to the saved file
        """
        pass

    @abstractmethod
    def get_file(self, filename: str) -> bytes:
        """
        Retrieve a file from storage.

        Args:
            filename: File to retrieve

        Returns:
            File contents as bytes
        """
        pass

    @abstractmethod
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from storage.

        Args:
            filename: File to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists.

        Args:
            filename: File to check

        Returns:
            True if file exists, False otherwise
        """
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path: str = "uploads"):
        """
        Initialize local storage.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        logger.info(f"Initialized local storage at {base_path}")

    def save_file(self, file_obj: BinaryIO, filename: str) -> str:
        """Save file to local filesystem."""
        filepath = os.path.join(self.base_path, filename)

        try:
            with open(filepath, 'wb') as f:
                f.write(file_obj.read())
            logger.info(f"Saved file to local storage: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}", exc_info=True)
            raise

    def get_file(self, filename: str) -> bytes:
        """Retrieve file from local filesystem."""
        filepath = os.path.join(self.base_path, filename)

        try:
            with open(filepath, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {filename}: {e}", exc_info=True)
            raise

    def delete_file(self, filename: str) -> bool:
        """Delete file from local filesystem."""
        filepath = os.path.join(self.base_path, filename)

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted file from local storage: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {e}", exc_info=True)
            return False

    def file_exists(self, filename: str) -> bool:
        """Check if file exists in local filesystem."""
        filepath = os.path.join(self.base_path, filename)
        return os.path.exists(filepath)


class S3Storage(StorageBackend):
    """S3/MinIO storage backend."""

    def __init__(
        self,
        bucket: str,
        endpoint: Optional[str] = None,
        region: str = 'us-east-1'
    ):
        """
        Initialize S3 storage.

        Args:
            bucket: S3 bucket name
            endpoint: Custom S3 endpoint (for MinIO)
            region: AWS region (default: us-east-1)
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. "
                "Install it with: pip install boto3"
            )

        self.bucket = bucket
        self.region = region
        self.ClientError = ClientError

        # Initialize S3 client
        client_kwargs = {
            'region_name': region
        }

        if endpoint:
            client_kwargs['endpoint_url'] = endpoint

        self.s3_client = boto3.client('s3', **client_kwargs)

        # Verify bucket exists
        try:
            self.s3_client.head_bucket(Bucket=bucket)
            logger.info(f"Initialized S3 storage with bucket: {bucket}")
        except self.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket {bucket} does not exist")
                raise ValueError(f"S3 bucket {bucket} does not exist")
            else:
                logger.error(f"Error accessing bucket {bucket}: {e}")
                raise

    def save_file(self, file_obj: BinaryIO, filename: str) -> str:
        """Save file to S3."""
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket,
                filename
            )
            logger.info(f"Saved file to S3: {filename}")
            return f"s3://{self.bucket}/{filename}"
        except self.ClientError as e:
            logger.error(f"Failed to upload file {filename} to S3: {e}", exc_info=True)
            raise

    def get_file(self, filename: str) -> bytes:
        """Retrieve file from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=filename
            )
            return response['Body'].read()
        except self.ClientError as e:
            logger.error(f"Failed to download file {filename} from S3: {e}", exc_info=True)
            raise

    def delete_file(self, filename: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=filename
            )
            logger.info(f"Deleted file from S3: {filename}")
            return True
        except self.ClientError as e:
            logger.error(f"Failed to delete file {filename} from S3: {e}", exc_info=True)
            return False

    def file_exists(self, filename: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket,
                Key=filename
            )
            return True
        except self.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking if file {filename} exists: {e}", exc_info=True)
            raise


def get_storage_backend() -> StorageBackend:
    """
    Get the configured storage backend.

    Returns:
        Storage backend instance (LocalStorage or S3Storage)

    Environment variables:
        USE_S3: Set to 'true' to use S3 storage
        S3_BUCKET: S3 bucket name (required if USE_S3=true)
        S3_ENDPOINT: Custom S3 endpoint for MinIO (optional)
        AWS_REGION: AWS region (default: us-east-1)
    """
    use_s3 = os.getenv('USE_S3', 'false').lower() == 'true'

    if use_s3:
        bucket = os.getenv('S3_BUCKET')
        if not bucket:
            raise ValueError("S3_BUCKET environment variable is required when USE_S3=true")

        endpoint = os.getenv('S3_ENDPOINT')
        region = os.getenv('AWS_REGION', 'us-east-1')

        logger.info(f"Using S3 storage backend (bucket: {bucket})")
        return S3Storage(
            bucket=bucket,
            endpoint=endpoint,
            region=region
        )
    else:
        logger.info("Using local filesystem storage backend")
        return LocalStorage()


# Global storage instance
storage = get_storage_backend()
