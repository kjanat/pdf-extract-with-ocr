<div align="center">

# PDF Extract with OCR

</div>

<div align="center" style="padding: 2vh 10vw 1vh 10vw; display: flex; flex-basis: auto; flex-wrap: wrap; flex-shrink: 1; flex-flow: row wrap; float: inline-flex; justify-content: space-around; justify-items: center;">

<!--[![GitHub Release](https://img.shields.io/github/v/release/kjanat/pdf-extract-with-ocr?display_name=tag&style=for-the-badge)][2]
[![GitHub License](https://img.shields.io/github/license/kjanat/pdf-extract-with-ocr?style=for-the-badge)][3]-->
[![Commits](https://img.shields.io/github/commit-activity/m/kjanat/pdf-extract-with-ocr?label=commits&style=for-the-badge)][4]
[![GitHub last commit](https://img.shields.io/github/last-commit/kjanat/pdf-extract-with-ocr?style=for-the-badge&display_timestamp=committer)][5]

</div>

<!--<div align="center">

# PDF Extract with OCR

</div>-->

This project is a Flask-based web application that extracts text from PDF files. It determines whether the PDF contains selectable text or is a scanned document, using [`PyMuPDF`][pymupdf] for direct text extraction and [`Tesseract OCR`][tesseract] for scanned images.

## Features

- Extracts text from PDFs with selectable text using [`pymupdf`][pymupdf]
- Detects scanned PDFs and applies OCR with [`tesseract`][tesseract]
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

[1]: #installation
[2]: https://github.com/kjanat/Hi-Res-Redirector/releases/latest "Latest release"
[3]: # "Not licensed"
[4]: https://github.com/kjanat/pdf-extract-with-ocr/commits "Commit History"
[5]: https://github.com/kjanat/pdf-extract-with-ocr/pulse/monthly "Last activity"
[tesseract]: https://github.com/tesseract-ocr/tesseract
[pymupdf]: https://github.com/pymupdf/PyMuPDF
