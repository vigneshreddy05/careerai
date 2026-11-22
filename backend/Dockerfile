# =====================================================================
# CareerAI Backend - Production Container
# Compatible with Hugging Face Spaces (CPU Basic: 2 vCPU, 16 GB RAM)
# and container hosting platforms (Render, Railway, Fly.io)
# =====================================================================
FROM python:3.11-slim

# Prevent Python from writing bytecode and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install minimal build tools and curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install lightweight CPU-only PyTorch first to minimize image layer size
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining backend Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend application source code and models
COPY backend /app/backend

# Create directory for SQLite persistent database
RUN mkdir -p /app/backend/data

# Expose server port (defaults to 8000; override with -e PORT=7860 on HF Spaces)
EXPOSE 8000

# Container Health Check
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Start FastAPI application via Uvicorn ASGI server
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
