import os
import time
from datetime import datetime, timezone
from PIL import Image, UnidentifiedImageError, ImageOps, ImageFilter
import io
import pymupdf as fitz
import pytesseract
import uuid
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import BadRequest
from typing import Union

app = Flask(__name__)
CORS(app)

# Set the logger level to INFO to see log messages
if os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False):
    app.logger.setLevel("INFO")

def is_scanned(pdf_path):
    """
    Determines if a PDF document is scanned or not.

    This function opens a PDF file and checks each page for text content.
    If any text is found, the PDF is considered not scanned. If no text is
    found on any page, the PDF is likely scanned.

    Args:
        pdf_path (str): The file path to the PDF document.

    Returns:
        bool: True if the PDF is likely scanned (no text found), False otherwise.
    """
    doc = fitz.open(pdf_path)
    for page in doc:
        text = page.get_text("text")
        if text.strip():  # If text is found, it's not scanned
            return False
        else:
            return True  # No text found, it's likely scanned

def preprocess_image(img):
    """
    Preprocess the image to improve OCR quality.
    
    Parameters:
    img (PIL.Image.Image): The image to preprocess.
    
    Returns:
    PIL.Image.Image: The preprocessed image.
    """
    # Convert to grayscale
    img = ImageOps.grayscale(img)
    
    # Apply thresholding
    img = ImageOps.autocontrast(img)
    
    # Remove noise
    img = img.filter(ImageFilter.MedianFilter(size=1))
    
    return img

def extract_text_from_scanned_pdf(pdf_path, lang="nld", config="--oem 1 --psm 3"):
    """
    Extracts text from a scanned PDF file using OCR (Optical Character Recognition).
    Args:
        pdf_path (str): The file path to the scanned PDF.
        lang (str, optional): The language to be used by Tesseract OCR. Defaults to "nld" (Dutch).
        config (str, optional): Additional configuration options for Tesseract OCR. Defaults to "--oem 1 --psm 3".
    Returns:
        str: The extracted text from the PDF.
    """
    doc = fitz.open(pdf_path)
    extracted_text = []
    if os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False):
        app.logger.info("Running in Docker container")
        config += f" --tessdata-dir \"{os.environ['TESSDATA_PREFIX']}\""
    
    for page_num, page in enumerate(doc):
        # Convert page to an image
        pix = page.get_pixmap(dpi=600)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        # Preprocess the image
        img = preprocess_image(img)
        
        # Run OCR
        ocr_text = pytesseract.image_to_string(img, lang=lang, config=config)
        
        # Version with appending page number
        # extracted_text.append(f"Page {page_num + 1}:\n{ocr_text.strip()}\n")
        
        # Version without appending page number
        extracted_text.append(ocr_text.strip())
    
    return "\n".join(extracted_text)

def extract_text_pymupdf(pdf_path):
    """
    Extracts text from a PDF file using fitz.
    
    Args:
        pdf_path (str): The file path to the PDF document.
    
    Returns:
        str: The extracted text from the PDF, with ligatures and whitespace preserved.
    """
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE) for page in doc])
    app.logger.info(f"Extracted text using fitz: {text[:100]}...")  # Log the first 100 characters of the extracted text
    return text

def clean_text(text):
    """
    Cleans the input text by performing the following operations:
    1. Splits the text into lines.
    2. Strips leading and trailing whitespace from each line.
    3. Joins the cleaned lines back into a single string with newline characters.
    4. Splits the cleaned text into paragraphs (separated by double newlines).
    5. Removes any empty paragraphs.
    6. Joins the non-empty paragraphs back into a single string with double newlines.
    
    Args:
        text (str): The input text to be cleaned.
    
    Returns:
        str: The cleaned text with unnecessary whitespace and empty paragraphs removed.
    """
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines]
    cleaned_text = '\n'.join(cleaned_lines)
    return '\n\n'.join([para for para in cleaned_text.split('\n\n') if para.strip() != ''])

@app.route('/')
def index() -> Response:
    return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    app.logger.info("Received a file upload request")
    if 'file' not in request.files:
        app.logger.error("No file uploaded")
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        app.logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400
    
    # Save the file temporarily
    unique_filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    temp_path = os.path.join("temp", unique_filename)
    os.makedirs("temp", exist_ok=True)
    
    app.logger.info(f"Saving file {file.filename} to temp/{unique_filename}")
    file.save(temp_path)
    
    start_time = time.time()  # Record the start time
    app.logger.info("Starting text extraction...")

    file_is_scanned = is_scanned(temp_path)
    app.logger.info(f"Is scanned: {file_is_scanned}")
    
    try:
        if file_is_scanned:
            app.logger.info("Document is scanned, running OCR...")
            extracted_text = extract_text_from_scanned_pdf(temp_path)
            if not extracted_text:
                app.logger.error("No text found in the scanned PDF")
                return jsonify({"error": "No text found in the scanned PDF"}), 400
            method = "tesseract"
        elif not file_is_scanned:
            app.logger.info("Document already has selectable text.")
            extracted_text = extract_text_pymupdf(temp_path)
            if not extracted_text:
                app.logger.error("No text found in the PDF")
                return jsonify({"error": "No text found in the PDF"}), 400
            method = "pymupdf"
        else:
            app.logger.error("Unknown error")
            return jsonify({"error": "Unknown error"}), 500
        
        # Reduce multiple sequential newlines to a maximum of two newlines
        extracted_text = clean_text(extracted_text)
        app.logger.info(f"Extracted text: {extracted_text[:100]}...")  # Log the first 100 characters of the extracted text
        
        # Calculate the duration in milliseconds
        duration = round((time.time() - start_time) * 1000, 0)
        app.logger.info(f"Text extraction completed in {duration} ms")
        
        return jsonify({
            "body": extracted_text,
            "status": "success",
            "method": method,
            "filename": file.filename,
            "datetime": datetime.now(timezone.utc).isoformat(),
            "duration (ms)": duration
        })
    except UnidentifiedImageError:
        app.logger.error("Cannot identify image file")
        return jsonify({"error": "Cannot identify image file"}), 400
    except Exception as e:
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        app.logger.info(f"Removing temporary file: {temp_path}")
        os.remove(temp_path)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)