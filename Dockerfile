# ==========================================
# ApexFinance - Production Dockerfile
# ==========================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    DATABASE_PATH=/app/data/finance.db

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create persistent data directory with proper permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; resp = urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=3); exit(0 if resp.status == 200 else 1)"

# Start production WSGI server
CMD ["python", "wsgi.py"]
