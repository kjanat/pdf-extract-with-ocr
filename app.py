import os
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.wrappers import Response
from werkzeug.utils import secure_filename
from db import init_db, SessionLocal, OCRJob
from typing import Optional
from utils import check_stalled_jobs
from settings import IS_DOCKER
from tasks import process_pdf_task

app = Flask(__name__)
CORS(app)

if IS_DOCKER:
    app.logger.setLevel("WARNING")
else:
    app.logger.setLevel("INFO")
    app.logger.info("Running in local development mode")

@app.route('/')
def index() -> Response:
    return app.send_static_file('index.html')

@app.route('/jobs')
def jobs_view():
    return app.send_static_file('jobs.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    app.logger.info("Received a file upload request")
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No selected file"}), 400

    sanitized_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}.{sanitized_filename.split('.')[-1]}"
    temp_path = os.path.join("uploads", unique_filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(temp_path)

    task = process_pdf_task.delay(temp_path)

    with SessionLocal() as session:
        job = OCRJob(
            id=task.id, 
            filename=file.filename, 
            status="PENDING", 
            created_at=datetime.now(timezone.utc)
        )
        session.add(job)
        session.commit()

    return jsonify({
        "status": "processing",
        "task_id": task.id,
        "filename": file.filename
    })

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    # session = SessionLocal()
    # jobs = session.query(OCRJob).order_by(OCRJob.created_at.desc()).limit(20).all()
    # session.close()

    with SessionLocal() as session:
        jobs = session.query(OCRJob).order_by(OCRJob.created_at.desc()).limit(20).all()

    return jsonify([
        {
            "id": job.id,
            "filename": job.filename,
            "status": job.status,
            "method": job.method,
            "duration_ms": job.duration_ms,
            "created_at": job.created_at.isoformat(),
            "page_count": job.page_count,
            "file_size_kb": job.file_size_kb,
            "error_message": job.error_message
        } for job in jobs
    ])

@app.route('/api/result/<task_id>', methods=['GET'])
def get_result(task_id: str) -> Response:
    with SessionLocal() as session:
        job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
    
    # session = SessionLocal()
    # job = session.query(OCRJob).filter(OCRJob.id == task_id).first()
    # session.close()

    if not job:
        response = jsonify({"error": "Job not found"})
        response.status_code = 404
        return response

    # Return all details about the job, including the full text result
    return jsonify({
        "id": job.id,
        "filename": job.filename,
        "status": job.status,
        "method": job.method,
        "text": job.result_text,
        "duration_ms": job.duration_ms,
        "created_at": job.created_at.isoformat(),
        "page_count": job.page_count,
        "file_size_kb": job.file_size_kb,
        "error_message": job.error_message
    })

@app.route('/status/<task_id>', methods=['GET'])
def check_status(task_id: str) -> Response:
    with SessionLocal() as session:
        job: Optional[OCRJob] = session.query(OCRJob).filter(OCRJob.id == task_id).first()
    
    # session = SessionLocal()
    # job: Optional[OCRJob] = session.query(OCRJob).filter(OCRJob.id == task_id).first()
    # session.close()

    if not job:
        response = jsonify({"error": "Job not found"})
        response.status_code = 404
        return response

    return jsonify({
        "state": job.status,
        "method": job.method,
        "text": job.result_text,
        "duration_ms": job.duration_ms,
        "created_at": job.created_at.isoformat()
    })

if __name__ == '__main__':
    init_db()
    check_stalled_jobs()
    from waitress import serve
    
    if IS_DOCKER:
        host = os.getenv("FLASK_HOST", "0.0.0.0")
        port = int(os.getenv("FLASK_PORT", 80))
    else:
        host = os.getenv("FLASK_HOST", "127.0.0.1")
        port = int(os.getenv("FLASK_PORT", 8080))
    serve(app, host=host, port=port)