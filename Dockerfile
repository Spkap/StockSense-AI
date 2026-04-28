# syntax=docker/dockerfile:1

# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

# Install build deps (needed for grpcio and other compiled packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install locked third-party dependencies into the project virtualenv.
RUN uv sync --frozen --no-dev --no-install-project

# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY stocksense/ ./stocksense/

# Cloud Run sets PORT env var; default to 8080 (Cloud Run standard)
ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8080
ENV LOG_LEVEL=info
ENV UVICORN_RELOAD=false

EXPOSE 8080

# workers=1: Cloud Run scales via instances, not worker processes
CMD ["sh", "-c", "uvicorn stocksense.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
