import io
import hashlib
import pymupdf as fitz
import pytesseract
from datetime import datetime, timezone, timedelta
from db import SessionLocal, OCRJob
from PIL import Image, ImageOps, ImageFilter
from typing import List
from settings import IS_DOCKER

def is_scanned(pdf_path: str) -> bool:
    doc = fitz.open(pdf_path)
    for page in doc:
        if page.get_text("text").strip(): # type: ignore
            return False
    return True

def preprocess_image(img: Image.Image) -> Image.Image:
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter(size=1))
    return img

def extract_text_from_scanned_pdf(pdf_path: str, lang: str = "nld", config: str = "--oem 1 --psm 3") -> str:
    doc = fitz.open(pdf_path)
    extracted_text: List[str] = []
    for page in doc:
        pix = page.get_pixmap(dpi=600) # type: ignore
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img = preprocess_image(img)
        text = pytesseract.image_to_string(img, lang=lang, config=config)
        extracted_text.append(text.strip())
    return "\n".join(extracted_text)

def extract_text_pymupdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE) for page in doc]) # type: ignore

def clean_text(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines]
    cleaned_text = '\n'.join(cleaned_lines)
    return '\n\n'.join([para for para in cleaned_text.split('\n\n') if para.strip()])

def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in 64kb chunks
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_pdf_page_count(pdf_path: str) -> int:
    doc = fitz.open(pdf_path)
    return len(doc)

def check_stalled_jobs():
    """Find and update jobs that have been stuck in PENDING status for too long."""
    with SessionLocal() as session:
        # Find jobs that have been pending for more than 5 minutes
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        stalled_jobs = session.query(OCRJob).filter(
            OCRJob.status == "PENDING",
            OCRJob.created_at < time_threshold.isoformat()
        ).all()
        
        # Update stalled jobs to FAILED status
        for job in stalled_jobs:
            setattr(job, "status", "FAILED")
            setattr(job, "error_message", "Job processing timed out or failed to start")
            print(f"Marking stalled job {job.id} as FAILED")
        
        if stalled_jobs:
            session.commit()
            print(f"Updated {len(stalled_jobs)} stalled jobs")
