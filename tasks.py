import os
import uuid
import time
import threading
import logging
from typing import Dict, Any
from settings import IS_DOCKER
from db import SessionLocal, OCRJob
from services import PDFProcessor

logger = logging.getLogger(__name__)

# Import the real Celery task for Docker mode
if IS_DOCKER:
    print("Loading asynchronous Celery task processor")
    from celery_worker import process_pdf_task
else:
    print("Loading synchronous local task processor")
    
    # Define a synchronous version with Celery-like interface for local mode
    def _process_pdf_sync(pdf_path: str, task_id: str) -> Dict[str, Any]:
        """
        Synchronous PDF processing for local development.

        Uses the PDFProcessor service to handle all PDF processing logic.
        This provides the same functionality as the Celery task but runs synchronously.

        Args:
            pdf_path: Path to the PDF file to process
            task_id: Unique task identifier

        Returns:
            Dictionary with processing results
        """
        logger.info(f"[SYNC] Processing PDF: {pdf_path} with task ID: {task_id}")

        try:
            # Use the PDFProcessor service to handle all processing logic
            processor = PDFProcessor()
            result = processor.process_pdf(pdf_path, task_id, cleanup=True)

            logger.info(f"[SYNC] Task {task_id} completed successfully")
            return result

        except Exception as e:
            logger.error(f"[SYNC] Task {task_id} failed: {str(e)}", exc_info=True)

            # Update job status to FAILED
            try:
                with SessionLocal() as session:
                    job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
                    if job:
                        job.status = "FAILED"
                        job.error_message = str(e)
                        session.commit()
            except Exception as db_error:
                logger.error(f"Failed to update job status: {db_error}", exc_info=True)

            # Clean up temp file
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    logger.info(f"Cleaned up temp file: {pdf_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup temp file {pdf_path}: {cleanup_error}")

            return {
                "status": "failed",
                "error": str(e)
            }
    
    # Create a simple class to mimic Celery's task interface
    class SyncTask:
        def __init__(self, func):
            self.func = func
        
        def delay(self, pdf_path):
            class TaskResult:
                def __init__(self, task_id):
                    self.id = task_id
            
            # Generate a task ID
            task_id = str(uuid.uuid4())
            
            # Run the task in a separate thread to allow the API to return
            def run_task():
                try:
                    self.func(pdf_path, task_id)
                except Exception as e:
                    print(f"Task error: {e}")
            
            thread = threading.Thread(target=run_task)
            thread.daemon = True
            thread.start()
            
            # Return a task-like object with an ID
            return TaskResult(task_id)
    
    # Wrap the function to provide a Celery-like interface
    process_pdf_task = SyncTask(_process_pdf_sync)
