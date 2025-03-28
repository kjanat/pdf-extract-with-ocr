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
from utils import (
    is_scanned,
    extract_text_from_scanned_pdf,
    extract_text_pymupdf,
    clean_text,
    calculate_file_hash,
    get_pdf_page_count
)
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
    # Get task ID
    task_id = self.request.id
    session = None
    start_time = time.time()
    result = None
    
    logger.info(f"Processing PDF: {pdf_path} with task ID: {task_id}")
    
    try:
        # Calculate file hash and size
        file_hash = calculate_file_hash(pdf_path)
        file_size_kb = os.path.getsize(pdf_path) / 1024  # Convert bytes to KB

        # Open a database session
        session = SessionLocal()
        
        # Check if we already processed this file before (by hash)
        previous_job = session.query(OCRJob).filter(OCRJob.file_hash == file_hash).first()
        if previous_job and str(previous_job.status) == "COMPLETED":
            logger.info(f"Found cached result for task ID: {task_id} with file hash: {file_hash}")
            # Handle cached result case
            try:
                # First check if a job with this ID already exists
                existing_job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
                
                if existing_job:
                    # Update the existing job instead of creating a new one
                    setattr(existing_job, "status", "COMPLETED")
                    setattr(existing_job, "method", previous_job.method)
                    setattr(existing_job, "result_text", previous_job.result_text)
                    setattr(existing_job, "duration_ms", previous_job.duration_ms)
                    setattr(existing_job, "file_hash", file_hash)
                    setattr(existing_job, "file_size_kb", file_size_kb)
                    setattr(existing_job, "page_count", previous_job.page_count)
                else:
                    # Create a new job
                    job = OCRJob(
                        id=task_id,
                        filename=os.path.basename(pdf_path),
                        status="COMPLETED",
                        method=previous_job.method,
                        result_text=previous_job.result_text,
                        duration_ms=previous_job.duration_ms,
                        created_at=datetime.now(timezone.utc),
                        file_hash=file_hash,
                        file_size_kb=file_size_kb,
                        page_count=previous_job.page_count
                    )
                    session.add(job)
                    
                session.commit()
            except sqlalchemy.exc.IntegrityError:
                # If we still get an integrity error, just rollback and try a different approach
                session.rollback()
                
                # Handle the case where another process created the job in the meantime
                existing_job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
                if existing_job:
                    # Update the existing job with the cached results
                    setattr(existing_job, "status", "COMPLETED")
                    setattr(existing_job, "method", previous_job.method)
                    setattr(existing_job, "result_text", previous_job.result_text)
                    setattr(existing_job, "duration_ms", previous_job.duration_ms)
                    setattr(existing_job, "file_hash", file_hash)
                    setattr(existing_job, "file_size_kb", file_size_kb)
                    setattr(existing_job, "page_count", previous_job.page_count)
                    session.commit()
            finally:
                session.close()
            
            # Clean up temp file
            try:
                os.remove(pdf_path)
            except:
                pass
                
            return {
                "status": "completed",
                "method": previous_job.method,
                "text": previous_job.result_text,
                "duration_ms": previous_job.duration_ms,
                "page_count": previous_job.page_count,
                "file_size_kb": file_size_kb,
                "cached": True
            }
        
        # If no cached result, process the file
        
        # First make sure a job record exists and is marked as PROCESSING
        existing_job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
        if existing_job:
            setattr(existing_job, "status", "PROCESSING")
            setattr(existing_job, "file_hash", file_hash)
            setattr(existing_job, "file_size_kb", file_size_kb)
        else:
            job = OCRJob(
                id=task_id,
                filename=os.path.basename(pdf_path),
                status="PROCESSING",
                created_at=datetime.now(timezone.utc),
                file_hash=file_hash,
                file_size_kb=file_size_kb
            )
            session.add(job)
        session.commit()
        
        # Get page count
        page_count = get_pdf_page_count(pdf_path)
        
        # Process the PDF
        # Check if it's a scanned document or native
        if is_scanned(pdf_path):
            text = extract_text_from_scanned_pdf(pdf_path)
            method = "OCR"
        else:
            text = extract_text_pymupdf(pdf_path)
            method = "PYMUPDF"
        
        # Clean the extracted text
        cleaned_text = clean_text(text)
        
        # Calculate processing duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Update the job status
        job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
        if job:
            setattr(job, "status", "COMPLETED")
            setattr(job, "method", method)
            setattr(job, "result_text", cleaned_text)
            setattr(job, "duration_ms", duration_ms)
            setattr(job, "page_count", page_count)
            # setattr(job, "file_hash", file_hash)
            # setattr(job, "file_size_kb", file_size_kb)
            # setattr(job, "created_at", datetime.now(timezone.utc))
            
            # job.status = "COMPLETED"
            # job.method = method
            # job.result_text = cleaned_text
            # job.duration_ms = duration_ms
            # job.page_count = page_count
            session.commit()
        
        # Create the result
        result = {
            "status": "completed",
            "method": method,
            "text": cleaned_text,
            "duration_ms": duration_ms,
            "page_count": page_count,
            "file_size_kb": file_size_kb,
            "cached": False
        }
    
    except Exception as e:
        # Handle exceptions
        error_message = f"Error processing PDF: {str(e)}"
        print(f"Error in task {task_id}: {error_message}")
        
        try:
            if session:
                # Update job status to FAILED
                job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
                if job:
                    # Uncomment the next line if you want to set the status to "FAILED"
                    # job.status = "FAILED"
                    # job.error_message = error_message
                    setattr(job, "status", "FAILED")
                    setattr(job, "error_message", error_message)
                    session.commit()
        except Exception as db_error:
            print(f"Failed to update job status: {db_error}")
            
        # Return error result
        result = {
            "status": "failed",
            "error": error_message
        }
    
    finally:
        # Clean up resources
        if session:
            session.close()
        
        # Clean up temp file
        try:
            os.remove(pdf_path)
        except Exception as e:
            print(f"Failed to remove temp file {pdf_path}: {e}")
    
    # Always return a result
    return result