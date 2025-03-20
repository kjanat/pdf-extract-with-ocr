# PDF Extract with OCR

This project is a Flask-based web application that extracts text from PDF files. It uses `pdfminer.six` for text extraction and falls back to OCR using `pytesseract` if the PDF is a scanned image.

## Features

- Extract text from PDF files using `pdfminer.six`
- Fallback to OCR using `pytesseract` for scanned images
- Returns extracted text in a structured JSON format

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/pdf-extract-with-ocr.git
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

2. Use a tool like `curl` to upload a PDF file to the `/upload` endpoint:

    ```sh
    curl -X POST -F file=@path/to/your/file.pdf http://127.0.0.1:5000/upload
    ```

3. The application will return a JSON response with the extracted text, status, and method used.

## Example Response

```json
{
  "body": "Extracted text from the PDF here...",
  "status": "success",
  "method": "pdfminer/ocr"
}
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.
