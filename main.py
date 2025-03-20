from flask import Flask, request, jsonify
from pdfminer.high_level import extract_text
import pytesseract
from PIL import Image
import os

app = Flask(__name__)

def ocr_image(image_path):
    return pytesseract.image_to_string(Image.open(image_path))

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

    # Extract text
    extracted_text = extract_text(pdf_file=temp_path)
    method = "pdfminer"

    if not extracted_text.strip():  # If no text is extracted, use OCR
        extracted_text = ocr_image(temp_path)
        method = "ocr"

    # Clean up
    os.remove(temp_path)

    return jsonify({"body": extracted_text, "status": "success", "method": method})

if __name__ == '__main__':
    app.run(port=5000, host='127.0.0.1', debug=True)