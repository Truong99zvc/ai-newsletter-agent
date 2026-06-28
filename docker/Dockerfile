# ==============================================================================
# Multi-stage Dockerfile for AI Newsletter Agent (FastAPI Backend)
# ==============================================================================

# Build stage: Install dependencies and build project
FROM python:3.12-slim AS builder

# Install system dependencies needed for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install project dependencies into a virtual environment
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv sync --frozen --no-install-project

# Final stage: Create lightweight runtime image
FROM python:3.12-slim AS runner

# Install runtime dependencies (libpq is needed for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment paths
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy application source code
COPY app/ ./app/
COPY main.py ./

# Expose API port
EXPOSE 8000

# Start FastAPI server using uvicorn
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
