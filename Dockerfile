# ==========================================
# 🕌 Islamic Bot - Docker Configuration
# ==========================================
# Multi-stage Docker build for production deployment
# Optimized for size and security

# ==========================================
# Stage 1: Build Dependencies
# ==========================================
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ==========================================
# Stage 2: Production Image
# ==========================================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r islamicbot && \
    useradd -r -g islamicbot -d /app -s /bin/bash islamicbot

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=islamicbot:islamicbot . .

# Create necessary directories
RUN mkdir -p /app/logs /app/backups /app/post_prayer_images && \
    chown -R islamicbot:islamicbot /app

# Switch to non-root user
USER islamicbot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://api.telegram.org/bot${BOT_TOKEN}/getMe')" || exit 1

# Expose port (if needed for webhooks)
EXPOSE 8080

# Default command
CMD ["python", "premium_Azkar.py"]

# ==========================================
# Build Instructions:
# ==========================================
# docker build -t islamic-bot:latest .
# docker run -d --name islamic-bot --env-file .env islamic-bot:latest
# ==========================================