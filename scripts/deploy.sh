#!/bin/bash

# India Oasis - Automated Deploy Script for Hostinger VPS
# This script automates the deployment process for production environment
# Usage: ./scripts/deploy.sh [environment]

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
DEPLOY_USER="${DEPLOY_USER:-django}"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_FILE="/tmp/india_oasis_deploy.log"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
check_user() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."

    local required_commands=("docker" "docker-compose" "git" "curl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "$cmd is not installed. Please install it first."
            exit 1
        fi
    done

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi

    log "System requirements check passed"
}

# Validate environment file
validate_env() {
    log "Validating environment configuration..."

    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        error ".env file not found. Please create it from .env.example"
        exit 1
    fi

    # Check required environment variables
    local required_vars=(
        "SECRET_KEY"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "ALLOWED_HOSTS"
        "MERCADO_PAGO_ACCESS_TOKEN"
        "EMAIL_HOST_USER"
        "EMAIL_HOST_PASSWORD"
    )

    source "$PROJECT_DIR/.env"

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done

    log "Environment validation passed"
}

# Create backup
create_backup() {
    log "Creating backup..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="backup_${timestamp}"

    mkdir -p "$BACKUP_DIR"

    # Backup database if containers are running
    if docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" ps db | grep -q "Up"; then
        info "Creating database backup..."
        docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T db pg_dump \
            -U "${POSTGRES_USER:-postgres}" \
            -d "${POSTGRES_DB:-india_oasis}" \
            > "$BACKUP_DIR/db_${backup_name}.sql" || warning "Database backup failed"
    fi

    # Backup media files
    if [[ -d "$PROJECT_DIR/media" ]]; then
        info "Creating media files backup..."
        tar -czf "$BACKUP_DIR/media_${backup_name}.tar.gz" -C "$PROJECT_DIR" media/ || warning "Media backup failed"
    fi

    # Backup static files
    if [[ -d "$PROJECT_DIR/staticfiles" ]]; then
        info "Creating static files backup..."
        tar -czf "$BACKUP_DIR/static_${backup_name}.tar.gz" -C "$PROJECT_DIR" staticfiles/ || warning "Static files backup failed"
    fi

    log "Backup completed: $backup_name"
}

# Pull latest changes
update_code() {
    log "Updating code from repository..."

    cd "$PROJECT_DIR"

    # Stash any local changes
    if ! git diff --quiet; then
        warning "Local changes detected, stashing them..."
        git stash push -m "Deploy stash $(date)"
    fi

    # Pull latest changes
    git fetch origin
    git checkout main
    git pull origin main

    log "Code update completed"
}

# Build and deploy containers
deploy_containers() {
    log "Building and deploying containers..."

    cd "$PROJECT_DIR"

    # Pull latest base images
    info "Pulling latest base images..."
    docker-compose -f docker-compose.prod.yml pull

    # Build application images
    info "Building application images..."
    docker-compose -f docker-compose.prod.yml build --no-cache

    # Stop existing containers gracefully
    info "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down --timeout 30

    # Start new containers
    info "Starting new containers..."
    docker-compose -f docker-compose.prod.yml up -d

    log "Container deployment completed"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    # Wait for database to be ready
    info "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T db pg_isready -U "${POSTGRES_USER:-postgres}" &> /dev/null; then
            break
        fi
        ((attempt++))
        sleep 2
    done

    if [[ $attempt -eq $max_attempts ]]; then
        error "Database is not ready after $max_attempts attempts"
        exit 1
    fi

    # Run migrations
    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T web python manage.py migrate --noinput

    log "Database migrations completed"
}

# Collect static files
collect_static() {
    log "Collecting static files..."

    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T web \
        python manage.py collectstatic --noinput --clear

    log "Static files collection completed"
}

# Create cache table
create_cache_table() {
    log "Creating cache table..."

    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T web \
        python manage.py createcachetable || warning "Cache table creation failed (may already exist)"

    log "Cache table creation completed"
}

# Health check
health_check() {
    log "Running health checks..."

    local max_attempts=20
    local attempt=0
    local health_url="http://localhost/health/"

    info "Waiting for application to be ready..."
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            log "Application is healthy and ready"
            return 0
        fi
        ((attempt++))
        sleep 3
    done

    error "Application health check failed after $max_attempts attempts"
    return 1
}

# Cleanup old images and containers
cleanup() {
    log "Cleaning up old Docker resources..."

    # Remove unused images
    docker image prune -f

    # Remove unused containers
    docker container prune -f

    # Remove unused volumes (be careful with this)
    # docker volume prune -f

    # Remove old backups (keep last 10)
    if [[ -d "$BACKUP_DIR" ]]; then
        find "$BACKUP_DIR" -name "*.sql" -type f | sort | head -n -10 | xargs -r rm
        find "$BACKUP_DIR" -name "*.tar.gz" -type f | sort | head -n -10 | xargs -r rm
    fi

    log "Cleanup completed"
}

# Send deployment notification
send_notification() {
    local status=$1
    local message="India Oasis deployment $status on $(hostname) at $(date)"

    # Send to logs
    log "$message"

    # Send email notification if configured
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
        echo "$message" | mail -s "India Oasis Deployment $status" "$NOTIFICATION_EMAIL" || warning "Email notification failed"
    fi

    # Send to Slack webhook if configured
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL" || warning "Slack notification failed"
    fi
}

# Rollback function
rollback() {
    error "Deployment failed. Starting rollback..."

    # Stop current containers
    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" down --timeout 30

    # Restore from backup if available
    local latest_backup=$(ls -t "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null | head -n1)
    if [[ -n "$latest_backup" ]]; then
        warning "Restoring database from backup: $latest_backup"
        # Add restore logic here if needed
    fi

    error "Please check logs and fix issues before retrying deployment"
    exit 1
}

# Main deployment function
main() {
    log "Starting India Oasis deployment to $ENVIRONMENT environment"

    # Set trap for cleanup on exit
    trap 'send_notification "FAILED"' ERR
    trap rollback ERR

    check_user
    check_requirements
    validate_env
    create_backup
    update_code
    deploy_containers
    run_migrations
    collect_static
    create_cache_table

    # Wait a bit for services to stabilize
    sleep 10

    if health_check; then
        cleanup
        send_notification "SUCCESS"
        log "Deployment completed successfully!"

        info "Application URLs:"
        info "  - Web: http://$(hostname)"
        info "  - Admin: http://$(hostname)/admin/"
        info "  - Health: http://$(hostname)/health/"

    else
        error "Health check failed"
        exit 1
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
