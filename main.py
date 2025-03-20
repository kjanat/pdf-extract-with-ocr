from flask import Flask, request, jsonify
from PIL import Image, UnidentifiedImageError
import io
import os
import requests
import platform
import shutil
import pytesseract
import pymupdf as fitz

app = Flask(__name__)

# Automatically detect the Tesseract executable path
def detect_tesseract_path():
    if platform.system() == "Windows":
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_path):
            return default_path
        else:
            return shutil.which("tesseract")
    elif platform.system() == "Linux":
        default_path = "/usr/bin/tesseract"
        if os.path.exists(default_path):
            return default_path
        else:
            return shutil.which("tesseract")
    else:
        return shutil.which("tesseract")

tesseract_path = detect_tesseract_path()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    raise EnvironmentError("Tesseract executable not found. Please install Tesseract OCR.")

# Set Tesseract data path if necessary (Windows example)
if platform.system() == "Windows":
    os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
elif platform.system() == "Linux":
    os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/4.00/tessdata/"
else:
    os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/4.00/tessdata/"

def download_language_data(lang="nld"):
    tessdata_dir = os.environ["TESSDATA_PREFIX"]
    lang_file_path = os.path.join(tessdata_dir, f"{lang}.traineddata")
    
    if not os.path.exists(lang_file_path):
        print(f"Downloading {lang}.traineddata...")
        url = f"https://github.com/tesseract-ocr/tessdata/raw/main/{lang}.traineddata"
        response = requests.get(url)
        
        if response.status_code == 200:
            with open(lang_file_path, "wb") as f:
                f.write(response.content)
            print(f"{lang}.traineddata downloaded successfully.")
        else:
            raise Exception(f"Failed to download {lang}.traineddata. Status code: {response.status_code}")

def extract_text_from_scanned_pdf(pdf_path, lang="nld"):
    """Extract text from a scanned PDF using OCR without modifying the PDF."""
    download_language_data(lang)
    doc = fitz.open(pdf_path)
    extracted_text = []

    for page_num, page in enumerate(doc):
        # Convert page to an image
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Run OCR
        ocr_text = pytesseract.image_to_string(img, lang=lang)

        # Preserve ligatures & whitespace
        text_flags = fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE
        extracted_text.append(f"Page {page_num + 1}:\n{ocr_text.strip()}\n")

    return "\n".join(extracted_text)

def is_scanned(pdf_path):
    """Check if the PDF is scanned by checking if any page contains selectable text."""
    doc = fitz.open(pdf_path)
    for page in doc:
        text = page.get_text("text")
        if text.strip():  # If text is found, it's not scanned
            return False
    return True  # No text found, it's likely scanned

def extract_text_pymupdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE) for page in doc])
    return text

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the file temporarily
    temp_path = os.path.join("temp", file.filename)
    os.makedirs("temp", exist_ok=True)
    file.save(temp_path)

    try:
        if is_scanned(temp_path):
            print("Document is scanned. Running OCR...")
            extracted_text = extract_text_from_scanned_pdf(temp_path)
            method = "pymupdf/ocr"
        else:
            print("Document already has selectable text.")
            extracted_text = extract_text_pymupdf(temp_path)
            method = "pymupdf"

        return jsonify({"body": extracted_text, "status": "success", "method": method})
    except UnidentifiedImageError:
        return jsonify({"error": "Cannot identify image file"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up
        os.remove(temp_path)

if __name__ == '__main__':
    app.run(port=5000, host='127.0.0.1', debug=True)