FROM python:3.11-slim

# Install system dependencies:
# - libgl1: OpenGL library required by OpenCV
# - libglib2.0-0: GLib library required by OpenCV
# - tesseract-ocr: OCR engine for text extraction
# - curl: for health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        tesseract-ocr \
        curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create required directories
RUN mkdir -p data/uploads data/samples output/graphs output/visuals

# Render uses PORT env var (default 10000), fallback to 8000 for local
ENV PORT=8000

EXPOSE ${PORT}

# Use shell form so $PORT is expanded at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
