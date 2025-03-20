from flask import Flask, request, jsonify
from pdfminer.high_level import extract_text
import os

app = Flask(__name__)

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

    # Clean up
    os.remove(temp_path)

    return jsonify({"text": extracted_text})

if __name__ == '__main__':
    app.run(debug=True)
