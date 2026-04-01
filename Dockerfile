FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY auth.py .

# Create directories
RUN mkdir -p /app/data /app/logs

# Environment
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Tashkent

CMD ["python", "app/main.py"]