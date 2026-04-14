# syntax=docker/dockerfile:1

# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build deps (needed for grpcio and other compiled packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-backend.txt .

# Install into a prefix so we can copy to final stage cleanly
RUN pip install --no-cache-dir --prefix=/install -r requirements-backend.txt

# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY stocksense/ ./stocksense/

# Cloud Run sets PORT env var; default to 8080 (Cloud Run standard)
ENV PORT=8080
ENV LOG_LEVEL=info
ENV UVICORN_RELOAD=false

EXPOSE 8080

# workers=1: Cloud Run scales via instances, not worker processes
CMD ["sh", "-c", "uvicorn stocksense.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
