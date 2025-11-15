import os
import time
import sqlalchemy.exc
from datetime import datetime, timezone
from typing import Dict, Any, cast, Callable
import uuid
import logging
from celery import Celery, Task
from settings import CELERY_BROKER_URL, IS_DOCKER
from db import SessionLocal, OCRJob
from services import PDFProcessor

logger = logging.getLogger(__name__)

""" if IS_DOCKER:
    from celery import Celery
else:
    print("[dev-mode] Celery is running in LOCAL SYNCHRONOUS mode")
    from dev_celery import DevCelery as Celery """

# Initialize Celery
celery = Celery('worker', broker=CELERY_BROKER_URL)
celery.conf.broker_connection_retry_on_startup = True

""" # Patch Celery for local synchronous dev
if not IS_DOCKER:
    print("[dev-mode] Celery is running in LOCAL SYNCHRONOUS mode")
    
    def fake_task(*args, **kwargs):
        def decorator(func):
            func.delay = func  # Make .delay() just call the function
            return func
        return decorator
    celery.task = fake_task # type: ignore """

# Create synchronous task decorator for local development
if not IS_DOCKER:
    print("[dev-mode] Celery is running in LOCAL SYNCHRONOUS mode")
    
    # Store the original task decorator
    original_task = celery.task
    
    def synchronous_task(*args, **kwargs):
        def decorator(func):
            # Create a synchronous version that runs immediately
            def wrapped_func(*func_args, **func_kwargs):
                # For synchronous execution, we need to handle the task ID
                task_id = str(uuid.uuid4())
                
                # Create a simple Task-like object with a request attribute
                class SyncTask:
                    class Request:
                        id = task_id
                    request = Request()
                
                # If the task is bound (has 'self' as first arg)
                try:
                    if kwargs.get('bind', False):
                        result = func(SyncTask(), *func_args, **func_kwargs)
                    else:
                        result = func(*func_args, **func_kwargs)
                    
                    # Return result but keep task_id accessible
                    return result
                except Exception as e:
                    print(f"Error in task {task_id}: {e}")
                    raise
            
            # Return a task-like object that has an 'id' and supports 'delay'
            class SyncTaskResult:
                def __init__(self, task_func):
                    self.task_func = task_func
                    self.id = str(uuid.uuid4())
                
                def delay(self, *args, **kwargs):
                    try:
                        # Execute the function immediately
                        result = self.task_func(*args, **kwargs)
                        # Return self to maintain the task interface
                        return self
                    except Exception as e:
                        print(f"Error in task {self.id}: {e}")
                        raise
                
                def apply_async(self, args=None, kwargs=None, **options):
                    args = args or ()
                    kwargs = kwargs or {}
                    return self.delay(*args, **kwargs)
            
            # Create and return a task-like object
            return SyncTaskResult(wrapped_func)
        
        # If called with a function directly
        if len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        return decorator
    
    # Replace the celery task decorator with our synchronous version
    celery.task = synchronous_task # type: ignore
else:
    # If running in Docker, use the original task decorator
    print("[docker-mode] Celery is running in DOCKER mode")
    pass


""" def process_pdf_task(self, pdf_path: str) -> Dict[str, Any]:
    task_id = getattr(self.request, "id", f"local-{int(time.time())}")
    session = None
    start_time = time.time()
    result = None """

@celery.task(bind=True,
             acks_late=True,
             autoretry_for=(sqlalchemy.exc.OperationalError,),
             retry_kwargs={'max_retries': 3, 'countdown': 5}
             )
def process_pdf_task(self, pdf_path: str) -> Dict[str, Any]:
    """
    Celery task for processing PDF files.

    This task uses the PDFProcessor service to handle all PDF processing logic.
    The service handles caching, text extraction, and database updates.

    Args:
        pdf_path: Path to the PDF file to process

    Returns:
        Dictionary with processing results
    """
    task_id = self.request.id
    logger.info(f"Celery task {task_id} starting for PDF: {pdf_path}")

    try:
        # Use the PDFProcessor service to handle all processing logic
        processor = PDFProcessor()
        result = processor.process_pdf(pdf_path, task_id, cleanup=True)

        logger.info(f"Celery task {task_id} completed successfully")
        return result

    except Exception as e:
        logger.error(f"Celery task {task_id} failed: {str(e)}", exc_info=True)

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
