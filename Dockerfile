# Multi-stage Dockerfile optimized for Hostinger VPS production

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /build

# Copy requirements files
COPY requirements.txt requirements-prod.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --user --no-warn-script-location -r requirements.txt && \
    pip install --user --no-warn-script-location -r requirements-prod.txt

# Stage 2: Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH=/home/django/.local/bin:$PATH

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libjpeg62-turbo \
    libpng16-16 \
    libwebp7 \
    libfreetype6 \
    liblcms2-2 \
    libopenjp2-7 \
    libtiff6 \
    curl \
    gettext \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with specific UID/GID for better security
RUN groupadd -g 1001 django && \
    useradd -r -u 1001 -g django -d /home/django -m django

# Create necessary directories
RUN mkdir -p \
    /app \
    /app/logs \
    /app/media \
    /app/staticfiles \
    /app/backups \
    && chown -R django:django /app

# Switch to non-root user
USER django

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder --chown=django:django /root/.local /home/django/.local

# Copy application code
COPY --chown=django:django . .

# Create cache table and collect static files
RUN python manage.py collectstatic --noinput --settings=india_oasis_project.settings_production || true

# Create log directory with proper permissions
RUN mkdir -p logs && chmod 755 logs

# Expose port (non-privileged port)
EXPOSE 8000

# Health check optimized for Hostinger
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f -H "Host: localhost" http://localhost:8000/health/ || exit 1

# Use JSON format for better signal handling
CMD ["gunicorn", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "2", \
    "--worker-class", "sync", \
    "--worker-connections", "1000", \
    "--timeout", "120", \
    "--keepalive", "5", \
    "--max-requests", "1000", \
    "--max-requests-jitter", "100", \
    "--preload", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info", \
    "india_oasis_project.wsgi:application"]
