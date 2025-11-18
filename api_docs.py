"""
API Documentation with Swagger/OpenAPI

This module sets up Swagger UI documentation for the API endpoints.
"""
from flask import Blueprint
from flask_restx import Api, Resource, fields, Namespace
from werkzeug.datastructures import FileStorage

# Create the API documentation
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-Key'
    }
}

api = Api(
    version='1.0',
    title='PDF Extract with OCR API',
    description='''
    A powerful REST API for extracting text from PDF files using OCR technology.

    ## Features
    - Automatic detection of scanned vs. digital PDFs
    - PyMuPDF for digital PDFs (fast)
    - Tesseract OCR for scanned PDFs (accurate)
    - File hash-based caching for duplicate detection
    - Asynchronous processing with Celery
    - Real-time status monitoring

    ## Authentication
    Protected endpoints require an API key passed in the `X-API-Key` header.

    ## Rate Limiting
    - Upload endpoint: 10 requests per minute
    - Other endpoints: 50 requests per hour, 200 per day
    ''',
    doc='/docs',  # Swagger UI will be at /docs
    authorizations=authorizations,
    security='apikey'
)

# Define namespaces
health_ns = Namespace('health', description='Health check operations')
jobs_ns = Namespace('jobs', description='Job management operations')
upload_ns = Namespace('upload', description='File upload operations')

api.add_namespace(health_ns, path='/api')
api.add_namespace(jobs_ns, path='/api')
api.add_namespace(upload_ns, path='/')

# Define models for documentation
job_model = api.model('Job', {
    'id': fields.String(required=True, description='Unique job identifier'),
    'filename': fields.String(required=True, description='Original filename'),
    'status': fields.String(required=True, description='Job status', enum=['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']),
    'method': fields.String(description='Extraction method used', enum=['PYMUPDF', 'OCR']),
    'duration_ms': fields.Integer(description='Processing duration in milliseconds'),
    'created_at': fields.String(description='Job creation timestamp'),
    'page_count': fields.Integer(description='Number of pages in PDF'),
    'file_size_kb': fields.Float(description='File size in kilobytes'),
    'error_message': fields.String(description='Error message if job failed')
})

job_result_model = api.model('JobResult', {
    'id': fields.String(required=True, description='Unique job identifier'),
    'filename': fields.String(required=True, description='Original filename'),
    'status': fields.String(required=True, description='Job status'),
    'method': fields.String(description='Extraction method used'),
    'text': fields.String(description='Extracted text content'),
    'duration_ms': fields.Integer(description='Processing duration in milliseconds'),
    'created_at': fields.String(description='Job creation timestamp'),
    'page_count': fields.Integer(description='Number of pages in PDF'),
    'file_size_kb': fields.Float(description='File size in kilobytes'),
    'error_message': fields.String(description='Error message if job failed')
})

job_status_model = api.model('JobStatus', {
    'state': fields.String(required=True, description='Current job state'),
    'method': fields.String(description='Extraction method'),
    'text': fields.String(description='Extracted text (if completed)'),
    'duration_ms': fields.Integer(description='Processing duration'),
    'created_at': fields.String(description='Job creation timestamp'),
    'error_message': fields.String(description='Error message if failed')
})

upload_response_model = api.model('UploadResponse', {
    'status': fields.String(required=True, description='Upload status'),
    'task_id': fields.String(required=True, description='Task identifier for tracking'),
    'filename': fields.String(required=True, description='Uploaded filename')
})

health_model = api.model('Health', {
    'status': fields.String(required=True, description='Health status'),
    'service': fields.String(required=True, description='Service name')
})

readiness_model = api.model('Readiness', {
    'status': fields.String(required=True, description='Readiness status'),
    'database': fields.String(required=True, description='Database connection status'),
    'error': fields.String(description='Error message if not ready')
})

error_model = api.model('Error', {
    'error': fields.String(required=True, description='Error message')
})

# File upload parser
upload_parser = api.parser()
upload_parser.add_argument(
    'file',
    location='files',
    type=FileStorage,
    required=True,
    help='PDF file to process (max 50MB)'
)


# Health Check Resources
@health_ns.route('/health')
class HealthCheck(Resource):
    @api.doc('health_check')
    @api.marshal_with(health_model)
    @api.response(200, 'Service is healthy')
    def get(self):
        """Basic health check endpoint"""
        return {'status': 'healthy', 'service': 'pdf-extract-with-ocr'}, 200


@health_ns.route('/ready')
class ReadinessCheck(Resource):
    @api.doc('readiness_check')
    @api.marshal_with(readiness_model)
    @api.response(200, 'Service is ready')
    @api.response(503, 'Service is not ready', error_model)
    def get(self):
        """Readiness check with database connectivity test"""
        # This will be implemented in routes.py
        pass


# Job Management Resources
@jobs_ns.route('/jobs')
class JobList(Resource):
    @api.doc('list_jobs', security='apikey')
    @api.marshal_list_with(job_model)
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    def get(self):
        """Get list of recent OCR jobs"""
        pass


@jobs_ns.route('/result/<string:task_id>')
@api.param('task_id', 'The job identifier')
class JobResult(Resource):
    @api.doc('get_result', security='apikey')
    @api.marshal_with(job_result_model)
    @api.response(200, 'Success')
    @api.response(404, 'Job not found', error_model)
    @api.response(401, 'Unauthorized', error_model)
    def get(self, task_id):
        """Get the result of a completed OCR job"""
        pass


@jobs_ns.route('/status/<string:task_id>')
@api.param('task_id', 'The job identifier')
class JobStatus(Resource):
    @api.doc('check_status', security='apikey')
    @api.marshal_with(job_status_model)
    @api.response(200, 'Success')
    @api.response(404, 'Job not found', error_model)
    @api.response(401, 'Unauthorized', error_model)
    def get(self, task_id):
        """Check the status of an OCR job"""
        pass


# Upload Resources
@upload_ns.route('/upload')
class Upload(Resource):
    @api.doc('upload_pdf', security='apikey')
    @api.expect(upload_parser)
    @api.marshal_with(upload_response_model)
    @api.response(200, 'File uploaded successfully')
    @api.response(400, 'Bad request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(413, 'File too large', error_model)
    @api.response(429, 'Rate limit exceeded', error_model)
    def post(self):
        """
        Upload and process a PDF file

        The file will be processed asynchronously. Use the returned task_id
        to check the status and retrieve results.

        **Limits:**
        - Maximum file size: 50MB
        - Rate limit: 10 uploads per minute
        - Allowed format: PDF only
        """
        pass
