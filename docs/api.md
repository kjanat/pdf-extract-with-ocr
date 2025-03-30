# API Documentation

This page provides comprehensive documentation for the PDF Extract with OCR REST API.

## API Endpoints

The API provides several endpoints for uploading PDFs, retrieving results, and managing job history.

### Upload a PDF

Upload a PDF file for text extraction.

**Endpoint:** `POST /upload`  
**Content-Type:** `multipart/form-data`  
**Request Parameters:**

| Parameter | Type | Required | Description             |
| --------- | ---- | -------- | ----------------------- |
| file      | File | Yes      | The PDF file to process |

``` json title="Response:"
{
  "status": "processing",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "filename": "example.pdf"
}
```

The response includes a task ID that you'll need to poll for results.

****

``` bash title="Example:"
curl -X POST -F file=@path/to/your/file.pdf http://localhost:8080/upload
```

### Check Processing Status

Check the status of a PDF processing task.

**Endpoint:** `GET /api/result/{task_id}`  
**Path Parameters:**

| Parameter | Type   | Required | Description                                   |
| --------- | ------ | -------- | --------------------------------------------- |
| task_id   | String | Yes      | The task ID returned from the upload endpoint |

``` json title="Response when processing is complete:"
{
  "text": "Extracted text from the PDF here...",
  "status": "success",
  "method": "tesseract",
  "filename": "example.pdf",
  "datetime": "2025-03-21T12:34:56.789012+00:00",
  "duration_ms": 12.3
}
```

``` json title="Response if still processing:"
{
  "status": "processing"
}
```

```bash title="Example:"
curl http://localhost:8080/api/result/a1b2c3d4-e5f6-7890-abcd-1234567890ab
```

### List Processing Jobs

Retrieve the history of PDF processing jobs.

**Endpoint:** `GET /api/jobs`  
**Query Parameters:**

| Parameter | Type    | Required | Description                                    |
| --------- | ------- | -------- | ---------------------------------------------- |
| limit     | Integer | No       | Maximum number of jobs to return (default: 50) |
| page      | Integer | No       | Page number for pagination (default: 1)        |

```json title="Response:"
{
  "jobs": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "filename": "example.pdf",
      "status": "SUCCESS",
      "created_at": "2025-03-21T12:34:56.789012+00:00",
      "completed_at": "2025-03-21T12:35:02.123456+00:00",
      "method": "tesseract",
      "duration_ms": 5334
    },
    // Additional job entries...
  ],
  "pagination": {
    "page": 1,
    "total_pages": 5,
    "total_jobs": 124
  }
}
```

```bash title="Example:"
curl http://localhost:8080/api/jobs?limit=10&page=1
```

## Complete Workflow Example

Here's a complete example of how to use the API to extract text from a PDF:

1. **Upload the PDF file:**

    ```bash
    curl -X POST -F file=@path/to/your/file.pdf http://localhost:8080/upload
    ```

    ```json title="Response:"
    {
    "status": "processing",
    "task_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "filename": "example.pdf"
    }
    ```

2. **Poll for results using the task ID:**

    ```bash
    curl http://localhost:8080/api/result/a1b2c3d4-e5f6-7890-abcd-1234567890ab
    ```

    ```json title="Initial response (still processing):"
    {
    "status": "processing"
    }
    ```

    ```json title="Final response (processing complete):"
    {
    "text": "Extracted text from the PDF here...",
    "status": "success",
    "method": "tesseract",
    "filename": "example.pdf",
    "datetime": "2025-03-21T12:34:56.789012+00:00",
    "duration_ms": 12.3
    }
    ```

## Error Responses

The API may return the following error responses:

| Status Code | Description           | Possible Cause                  |
| ----------- | --------------------- | ------------------------------- |
| 400         | Bad Request           | Missing file, invalid file type |
| 404         | Not Found             | Invalid task ID, job not found  |
| 500         | Internal Server Error | Server error during processing  |

```json title="Error response format:"
{
  "error": "Error message describing the issue"
}
```

## Notes

- The maximum file size for uploads is determined by server configuration
- Supported file formats: PDF only
- Processing time varies based on PDF size, complexity, and whether OCR is needed
- Large PDFs may take longer to process, especially when OCR is required

For frontend integration examples, see the JavaScript in the [`script.js`](https://github.com/kjanat/pdf-extract-with-ocr/blob/docker/static/script.js) file.
