FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2, PDF rendering, and open-source OCR
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    ffmpeg \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-nep \
    tesseract-ocr-hin \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2}"]
