"""Tests for database models."""
import pytest
from datetime import datetime, timezone
from db import OCRJob


def test_create_job(db_session):
    """Test creating an OCR job."""
    job = OCRJob(
        id="test-id-123",
        filename="test.pdf",
        status="PENDING",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(job)
    db_session.commit()

    # Query the job back
    retrieved_job = db_session.query(OCRJob).filter_by(id="test-id-123").first()
    assert retrieved_job is not None
    assert retrieved_job.filename == "test.pdf"
    assert retrieved_job.status == "PENDING"


def test_job_with_result(db_session):
    """Test job with result text."""
    job = OCRJob(
        id="test-id-456",
        filename="completed.pdf",
        status="COMPLETED",
        method="PyMuPDF",
        result_text="Extracted text content",
        duration_ms=1500,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(job)
    db_session.commit()

    retrieved_job = db_session.query(OCRJob).filter_by(id="test-id-456").first()
    assert retrieved_job.result_text == "Extracted text content"
    assert retrieved_job.method == "PyMuPDF"
    assert retrieved_job.duration_ms == 1500


def test_job_with_error(db_session):
    """Test job with error message."""
    job = OCRJob(
        id="test-id-789",
        filename="failed.pdf",
        status="FAILED",
        error_message="Processing failed",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(job)
    db_session.commit()

    retrieved_job = db_session.query(OCRJob).filter_by(id="test-id-789").first()
    assert retrieved_job.status == "FAILED"
    assert retrieved_job.error_message == "Processing failed"


def test_file_hash_unique(db_session):
    """Test that file hash is unique."""
    job1 = OCRJob(
        id="test-id-hash-1",
        filename="test1.pdf",
        status="COMPLETED",
        file_hash="abc123",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(job1)
    db_session.commit()

    # Try to add another job with the same hash
    job2 = OCRJob(
        id="test-id-hash-2",
        filename="test2.pdf",
        status="COMPLETED",
        file_hash="abc123",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(job2)

    with pytest.raises(Exception):  # Should raise IntegrityError
        db_session.commit()
