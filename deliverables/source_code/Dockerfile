# Multi-stage Dockerfile for RFP Intelligence Platform
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging configuration
COPY pyproject.toml /app/

# Install python dependencies
RUN pip install --upgrade pip && \
    pip install .

# Copy project source and application files
COPY . /app/

# Install project in editable mode
RUN pip install -e .

# Expose ports for FastAPI (8000) and Streamlit Web UI (8501)
EXPOSE 8000 8501

# Default command runs the FastAPI server
CMD ["python", "-m", "rfp_intelligence.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
