# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash metadata && \
    chown -R metadata:metadata /app
USER metadata

# Create directories for metadata output
RUN mkdir -p /app/metadata /app/logs

# Set default environment variables
ENV LOG_LEVEL=INFO \
    METADATA_OUTPUT_DIR=/app/metadata_storage

# Expose port for potential web interface
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import metadata_builder; print('OK')" || exit 1

# Default command
CMD ["metadata-builder"]

# Labels for metadata
LABEL maintainer="your.email@example.com" \
      version="1.0.0" \
      description="Metadata Builder - Generate structured metadata from database tables" \
      org.opencontainers.image.source="https://github.com/yourusername/metadata-builder" \
      org.opencontainers.image.documentation="https://github.com/yourusername/metadata-builder#readme" \
      org.opencontainers.image.licenses="MIT" 