import os
import uuid
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any
from settings import IS_DOCKER
from db import SessionLocal, OCRJob
from utils import (
    is_scanned, 
    extract_text_from_scanned_pdf,
    extract_text_pymupdf,
    clean_text,
    calculate_file_hash,
    get_pdf_page_count
)

# Import the real Celery task for Docker mode
if IS_DOCKER:
    print("Loading asynchronous Celery task processor")
    from celery_worker import process_pdf_task
else:
    print("Loading synchronous local task processor")
    
    # Define a synchronous version with Celery-like interface for local mode
    def _process_pdf_sync(pdf_path: str, task_id: str) -> Dict[str, Any]:
        """The actual implementation of the PDF processing logic"""
        start_time = time.time()
        session = None
        
        print(f"[SYNC] Processing PDF: {pdf_path} with task ID: {task_id}")
        
        try:
            # Calculate file hash and size
            file_hash = calculate_file_hash(pdf_path)
            file_size_kb = os.path.getsize(pdf_path) / 1024
            
            # Open a database session
            session = SessionLocal()
            
            # First update the existing job with file details
            existing_job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
            if existing_job:
                setattr(existing_job, "status", "PROCESSING")
                setattr(existing_job, "file_hash", file_hash)
                setattr(existing_job, "file_size_kb", file_size_kb)
                session.commit()
            
            # Check if we already processed this file before
            previous_job = session.query(OCRJob).filter(
                OCRJob.file_hash == file_hash, 
                OCRJob.id != task_id  # Don't match the current job
            ).first()
            
            if previous_job and str(previous_job.status) == "COMPLETED":
                print(f"Found cached result for {task_id}")
                # Update existing job with cached results
                if existing_job:
                    setattr(existing_job, "status", "COMPLETED")
                    setattr(existing_job, "method", previous_job.method)
                    setattr(existing_job, "result_text", previous_job.result_text)
                    setattr(existing_job, "duration_ms", previous_job.duration_ms)
                    setattr(existing_job, "page_count", previous_job.page_count)
                    session.commit()
                
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
            
            # Process the file normally
            # Get page count
            page_count = get_pdf_page_count(pdf_path)
            
            # Process the PDF
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
            if existing_job:
                setattr(existing_job, "status", "COMPLETED")
                setattr(existing_job, "method", method)
                setattr(existing_job, "result_text", cleaned_text)
                setattr(existing_job, "duration_ms", duration_ms)
                setattr(existing_job, "page_count", page_count)
                session.commit()
            
            # Create the result
            return {
                "status": "completed",
                "method": method,
                "text": cleaned_text,
                "duration_ms": duration_ms,
                "page_count": page_count,
                "file_size_kb": file_size_kb,
                "cached": False
            }
        
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            if session:
                # Update job status to FAILED
                job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
                if job:
                    setattr(job, "status", "FAILED")
                    setattr(job, "error_message", str(e))
                    session.commit()
            
            return {"status": "failed", "error": str(e)}
        
        finally:
            if session:
                session.close()
            
            # Clean up temp file
            try:
                os.remove(pdf_path)
            except Exception as e:
                print(f"Failed to remove temp file {pdf_path}: {e}")
    
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