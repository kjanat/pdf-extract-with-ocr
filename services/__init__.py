"""
PDF Processing Service

This module contains the core PDF processing logic that is shared between
synchronous (local development) and asynchronous (production) task executors.
"""
import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from db import SessionLocal, OCRJob
from utils import (
    is_scanned,
    extract_text_from_scanned_pdf,
    extract_text_pymupdf,
    clean_text,
    calculate_file_hash,
    get_pdf_page_count
)

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service class for processing PDF files with OCR capabilities."""

    def __init__(self):
        self.logger = logger

    def process_pdf(
        self,
        pdf_path: str,
        task_id: str,
        cleanup: bool = True
    ) -> Dict[str, Any]:
        """
        Process a PDF file and extract text.

        Args:
            pdf_path: Path to the PDF file
            task_id: Unique task identifier
            cleanup: Whether to delete the PDF file after processing

        Returns:
            Dictionary with processing results including status, text, method, etc.
        """
        start_time = time.time()
        session = None

        self.logger.info(f"Processing PDF: {pdf_path} with task ID: {task_id}")

        try:
            # Calculate file hash and size
            file_hash = calculate_file_hash(pdf_path)
            file_size_kb = os.path.getsize(pdf_path) / 1024

            # Open a database session
            session = SessionLocal()

            # Update job status to PROCESSING
            existing_job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
            if existing_job:
                existing_job.status = "PROCESSING"
                existing_job.file_hash = file_hash
                existing_job.file_size_kb = file_size_kb
                session.commit()

            # Check for cached results
            cached_result = self._check_cache(session, file_hash, task_id)
            if cached_result:
                self.logger.info(f"Found cached result for task {task_id}")
                if existing_job:
                    self._update_job_with_cached_result(existing_job, cached_result, session)

                if cleanup:
                    self._cleanup_file(pdf_path)

                return {
                    "status": "completed",
                    "method": cached_result.method,
                    "text": cached_result.result_text,
                    "duration_ms": cached_result.duration_ms,
                    "page_count": cached_result.page_count,
                    "file_size_kb": file_size_kb,
                    "cached": True
                }

            # Process the PDF (no cache hit)
            result = self._process_pdf_file(pdf_path, file_size_kb, start_time)

            # Update job with results
            if existing_job:
                self._update_job_with_result(existing_job, result, session)

            return result

        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_path}: {str(e)}", exc_info=True)
            if session:
                self._mark_job_failed(session, task_id, str(e))

            return {"status": "failed", "error": str(e)}

        finally:
            if session:
                session.close()

            if cleanup:
                self._cleanup_file(pdf_path)

    def _check_cache(
        self,
        session,
        file_hash: str,
        current_task_id: str
    ) -> Optional[OCRJob]:
        """Check if we have a cached result for this file hash."""
        return session.query(OCRJob).filter(
            OCRJob.file_hash == file_hash,
            OCRJob.id != current_task_id,
            OCRJob.status == "COMPLETED"
        ).first()

    def _update_job_with_cached_result(self, job: OCRJob, cached_job: OCRJob, session):
        """Update job with cached results."""
        job.status = "COMPLETED"
        job.method = cached_job.method
        job.result_text = cached_job.result_text
        job.duration_ms = cached_job.duration_ms
        job.page_count = cached_job.page_count
        session.commit()

    def _process_pdf_file(
        self,
        pdf_path: str,
        file_size_kb: float,
        start_time: float
    ) -> Dict[str, Any]:
        """Process the PDF file and extract text."""
        # Get page count
        page_count = get_pdf_page_count(pdf_path)

        # Determine processing method and extract text
        if is_scanned(pdf_path):
            self.logger.info(f"PDF is scanned, using OCR for {pdf_path}")
            text = extract_text_from_scanned_pdf(pdf_path)
            method = "OCR"
        else:
            self.logger.info(f"PDF has selectable text, using PyMuPDF for {pdf_path}")
            text = extract_text_pymupdf(pdf_path)
            method = "PYMUPDF"

        # Clean the extracted text
        cleaned_text = clean_text(text)

        # Calculate processing duration
        duration_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "completed",
            "method": method,
            "text": cleaned_text,
            "duration_ms": duration_ms,
            "page_count": page_count,
            "file_size_kb": file_size_kb,
            "cached": False
        }

    def _update_job_with_result(self, job: OCRJob, result: Dict[str, Any], session):
        """Update job with processing results."""
        job.status = "COMPLETED"
        job.method = result["method"]
        job.result_text = result["text"]
        job.duration_ms = result["duration_ms"]
        job.page_count = result["page_count"]
        session.commit()

    def _mark_job_failed(self, session, task_id: str, error_message: str):
        """Mark a job as failed with an error message."""
        job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
        if job:
            job.status = "FAILED"
            job.error_message = error_message
            session.commit()

    def _cleanup_file(self, pdf_path: str):
        """Clean up the temporary PDF file."""
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                self.logger.info(f"Cleaned up temporary file: {pdf_path}")
        except Exception as e:
            self.logger.warning(f"Failed to remove temporary file {pdf_path}: {e}")


# Global instance
pdf_processor = PDFProcessor()
