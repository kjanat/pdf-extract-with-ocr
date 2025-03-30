# Multi-stage build for better performance on ARM architectures

# Build stage
FROM python:3 AS builder

WORKDIR /wheels

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install build dependencies with better cache handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    pkg-config \
    gcc \
    python3-dev \
    libpq-dev \
    swig \
    && rm -rf /var/lib/apt/lists/*

# Build wheels with pip cache
RUN pip wheel --wheel-dir=/wheels -r requirements.txt

# Final stage
FROM python:3-slim

# Add metadata labels
LABEL org.opencontainers.image.description="PDF Extract with OCR: A web service that extracts text from PDF files using direct extraction for text PDFs and Tesseract OCR for scanned documents. Provides both API endpoints and web interface for text extraction."
LABEL org.opencontainers.image.source="https://github.com/kjanat/pdf-extract-with-ocr"
LABEL org.opencontainers.image.licenses="Proprietary"

WORKDIR /app

# Copy requirements first to maintain layer separation
COPY requirements.txt .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install runtime dependencies with better locking
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-nld \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/uploads

# Install Python dependencies with cache
COPY --from=builder /wheels /wheels
RUN pip install --upgrade pip --root-user-action \
    && pip install --no-index --find-links=/wheels -r requirements.txt --root-user-action \
    && rm -rf /wheels

# Copy application code last to maximize cache usage for previous layers
COPY . .

EXPOSE 80
CMD ["python3", "app.py"]