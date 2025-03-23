# PDF Extract with OCR

This project is a Flask-based web application that extracts text from PDF files. It determines whether the PDF contains selectable text or is a scanned document, using `pymupdf` for direct text extraction and `Tesseract OCR` for scanned images.

## Features

- Extracts text from PDFs with selectable text using `pymupdf`
- Detects scanned PDFs and applies OCR with `Tesseract`
- Automatic Tesseract installation check and language data download
- Returns extracted text in a structured JSON format
- Provides processing time and extraction method details

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/kjanat/pdf-extract-with-ocr.git
    cd pdf-extract-with-ocr
    ```

2. Create a virtual environment and activate it:

    ```sh
    python -m venv venv
    
    # On macOS/Linux
    source venv/bin/activate

    # On Windows
    venv\Scripts\activate
    ```

3. Install the required dependencies:

    ```sh
    pip install -U -r requirements.txt
    ```

4. Install Tesseract OCR:
    - On Windows, use winget:

        ```powershell
        winget install --id=tesseract-ocr.tesseract
        ```

    - On macOS, use Homebrew:

        ```sh
        brew install tesseract
        ```

    - On Linux, use your package manager:

        ```sh
        sudo apt-get install tesseract-ocr
        ```

## Usage

1. Run the Flask application:

    ```sh
    python main.py
    ```

2. Open your browser and navigate to `http://127.0.0.1:5000` to access the web interface and upload a pdf, or upload a PDF file through the `/upload` endpoint:

    ```sh
    curl -X POST -F file=@path/to/your/file.pdf http://127.0.0.1:5000/upload
    ```

3. The API will return a JSON response with the extracted text, status, method used, and processing duration.

## Example Response

```json
{
   "body": "Extracted text from the PDF here...",
   "status": "success",
   "method": "tesseract",
   "filename": "example.pdf",
   "datetime": "2025-03-21T12:34:56.789012+00:00",
   "duration (ms)": 12.3
}
```

## License

© 2025 Kaj Kowalski. All Rights Reserved.

This software and associated documentation files are proprietary and may not be copied, distributed, modified, or used in any manner without prior written permission from the owner.
