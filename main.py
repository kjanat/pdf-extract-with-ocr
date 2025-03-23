from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
from datetime import datetime, timezone
from PIL import Image, UnidentifiedImageError, ImageOps, ImageFilter
import io
import pymupdf
import pytesseract
import uuid

app = Flask(__name__)
CORS(app)

def is_scanned(pdf_path):
    """Check if the PDF is scanned by checking if any page contains selectable text."""
    doc = pymupdf.open(pdf_path)
    for page in doc:
        text = page.get_text("text")
        if text.strip():  # If text is found, it's not scanned
            return False
    return True  # No text found, it's likely scanned

def extract_text_pymupdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = "\n".join([page.get_text("text", flags=pymupdf.TEXT_PRESERVE_LIGATURES | pymupdf.TEXT_PRESERVE_WHITESPACE) for page in doc])
    return text

def preprocess_image(img):
    # Preprocess the image to improve OCR quality.
    
    # Convert to grayscale
    img = ImageOps.grayscale(img)
    
    # Apply thresholding
    img = ImageOps.autocontrast(img)

    # Remove noise
    img = img.filter(ImageFilter.MedianFilter(size=1))

    return img

def extract_text_from_scanned_pdf(pdf_path, lang="nld", config="--oem 1 --psm 3"):
    """Extract text from a scanned PDF using OCR without modifying the PDF."""
    # download_language_data(lang)
    doc = pymupdf.open(pdf_path)
    extracted_text = []
    if os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False):
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

def clean_text(text):
    """Remove lines that contain only whitespace characters and reduce multiple sequential newlines to a maximum of two newlines."""
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines]
    cleaned_text = '\n'.join(cleaned_lines)
    return '\n\n'.join([para for para in cleaned_text.split('\n\n') if para.strip() != ''])

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the file temporarily
    unique_filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    temp_path = os.path.join("temp", unique_filename)
    os.makedirs("temp", exist_ok=True)
    file.save(temp_path)
    
    start_time = time.time()  # Record the start time

    try:
        if is_scanned(temp_path):
            print("Document is scanned. Running OCR...")
            extracted_text = extract_text_from_scanned_pdf(temp_path)
            method = "tesseract"
        else:
            print("Document already has selectable text.")
            extracted_text = extract_text_pymupdf(temp_path)
            method = "pymupdf"
            
        # Reduce multiple sequential newlines to a maximum of two newlines
        extracted_text = clean_text(extracted_text)
        
        # Calculate the duration in milliseconds
        duration = round((time.time() - start_time) * 1000, 0)

        return jsonify({
            "body": extracted_text,
            "status": "success",
            "method": method,
            "filename": file.filename,
            "datetime": datetime.now(timezone.utc).isoformat(),
            "duration (ms)": duration
        })
    except UnidentifiedImageError:
        return jsonify({"error": "Cannot identify image file"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up
        os.remove(temp_path)

if __name__ == '__main__':
    import hypercorn.asyncio
    from hypercorn.config import Config
    import asyncio

    config = Config()
    config.bind = ["0.0.0.0:5000"]
    config.alpn_protocols = ["h2", "http/1.1"]

    asyncio.run(hypercorn.asyncio.serve(app, config))
