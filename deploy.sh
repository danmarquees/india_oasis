#!/bin/bash

# India Oasis Production Deployment Script
# This script automates the deployment process for production environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="india_oasis"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deploy.log"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    echo "[ERROR] $1" >> "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
    echo "[INFO] $1" >> "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."

    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi

    if ! command -v git &> /dev/null; then
        error "Git is not installed. Please install Git first."
    fi

    log "All dependencies are installed"
}

# Check environment file
check_env_file() {
    if [ ! -f ".env" ]; then
        error "Environment file (.env) not found. Please create it based on .env.production.example"
    fi

    # Check required environment variables
    local required_vars=("SECRET_KEY" "DATABASE_URL" "ALLOWED_HOSTS" "MERCADO_PAGO_PUBLIC_KEY" "MERCADO_PAGO_ACCESS_TOKEN")

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            error "Required environment variable ${var} not found in .env file"
        fi
    done

    log "Environment file validation passed"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."

    mkdir -p logs
    mkdir -p backups
    mkdir -p media
    mkdir -p nginx/ssl

    # Set permissions
    chmod 755 logs backups media

    log "Directories created successfully"
}

# Backup database
backup_database() {
    if [ "$1" = "--skip-backup" ]; then
        warning "Skipping database backup as requested"
        return
    fi

    log "Creating database backup..."

    local backup_file="${BACKUP_DIR}/db_backup_$(date +%Y%m%d_%H%M%S).sql"

    # Check if database container is running
    if docker-compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
        docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "${POSTGRES_USER:-postgres}" "${POSTGRES_DB:-india_oasis}" > "$backup_file" 2>/dev/null || {
            warning "Database backup failed, but continuing deployment"
        }

        if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
            log "Database backup created: $backup_file"
        else
            warning "Database backup appears to be empty or failed"
        fi
    else
        info "Database container not running, skipping backup"
    fi
}

# Build and deploy
deploy() {
    log "Starting deployment process..."

    # Pull latest code
    if [ -d ".git" ]; then
        log "Pulling latest code from repository..."
        git pull origin main || warning "Git pull failed, continuing with local code"
    fi

    # Build images
    log "Building Docker images..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache

    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" down

    # Start database and redis first
    log "Starting database and Redis..."
    docker-compose -f "$COMPOSE_FILE" up -d db redis

    # Wait for database to be ready
    log "Waiting for database to be ready..."
    timeout=60
    while ! docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            error "Database failed to start within 60 seconds"
        fi
    done

    # Run migrations
    log "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" run --rm web python manage.py migrate --settings=india_oasis_project.settings_production

    # Create cache table
    log "Creating cache table..."
    docker-compose -f "$COMPOSE_FILE" run --rm web python manage.py createcachetable --settings=india_oasis_project.settings_production

    # Collect static files
    log "Collecting static files..."
    docker-compose -f "$COMPOSE_FILE" run --rm web python manage.py collectstatic --noinput --settings=india_oasis_project.settings_production

    # Create superuser if it doesn't exist
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        log "Creating/updating superuser..."
        docker-compose -f "$COMPOSE_FILE" run --rm web python manage.py createsuperuser --noinput --settings=india_oasis_project.settings_production || info "Superuser already exists"
    fi

    # Start all services
    log "Starting all services..."
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for application to be ready
    log "Waiting for application to be ready..."
    timeout=120
    while ! curl -f http://localhost:8000/health/ > /dev/null 2>&1; do
        sleep 5
        timeout=$((timeout - 5))
        if [ $timeout -le 0 ]; then
            error "Application failed to start within 120 seconds"
        fi
    done

    log "Deployment completed successfully!"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."

    # Check if all containers are running
    local containers=("db" "redis" "web" "celery" "celery-beat" "nginx")

    for container in "${containers[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" ps "$container" | grep -q "Up"; then
            info "✓ $container is running"
        else
            error "✗ $container is not running"
        fi
    done

    # Check health endpoint
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        info "✓ Health check passed"
    else
        warning "✗ Health check failed"
    fi

    # Check database connectivity
    if docker-compose -f "$COMPOSE_FILE" exec -T web python manage.py check --database default --settings=india_oasis_project.settings_production > /dev/null 2>&1; then
        info "✓ Database connectivity verified"
    else
        warning "✗ Database connectivity check failed"
    fi

    log "Deployment verification completed"
}

# Rollback function
rollback() {
    log "Rolling back deployment..."

    # Stop current containers
    docker-compose -f "$COMPOSE_FILE" down

    # Restore from backup if available
    local latest_backup=$(ls -t ${BACKUP_DIR}/db_backup_*.sql 2>/dev/null | head -n1)

    if [ -n "$latest_backup" ]; then
        log "Restoring database from backup: $latest_backup"

        # Start database
        docker-compose -f "$COMPOSE_FILE" up -d db

        # Wait for database
        sleep 10

        # Restore backup
        docker-compose -f "$COMPOSE_FILE" exec -T db psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-india_oasis}" < "$latest_backup"

        log "Database restored from backup"
    else
        warning "No backup found for rollback"
    fi

    # Start services with previous version
    docker-compose -f "$COMPOSE_FILE" up -d

    log "Rollback completed"
}

# Cleanup old resources
cleanup() {
    log "Cleaning up old resources..."

    # Remove unused Docker images
    docker image prune -f

    # Remove old backups (keep last 10)
    find "$BACKUP_DIR" -name "db_backup_*.sql" -type f | sort -r | tail -n +11 | xargs -r rm

    # Remove old log files (keep last 30 days)
    find logs -name "*.log" -type f -mtime +30 -delete

    log "Cleanup completed"
}

# Main function
main() {
    log "Starting India Oasis deployment script"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                SKIP_BACKUP="--skip-backup"
                shift
                ;;
            --rollback)
                rollback
                exit 0
                ;;
            --cleanup)
                cleanup
                exit 0
                ;;
            --verify)
                verify_deployment
                exit 0
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-backup    Skip database backup"
                echo "  --rollback       Rollback to previous version"
                echo "  --cleanup        Clean up old resources"
                echo "  --verify         Verify current deployment"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done

    # Run checks
    check_root
    check_dependencies
    check_env_file
    create_directories

    # Backup and deploy
    backup_database "$SKIP_BACKUP"
    deploy
    verify_deployment
    cleanup

    log "Deployment process completed successfully!"
    info "Application is now running at: http://$(hostname):80"
    info "Admin interface: http://$(hostname):80/admin/"
    info "Health check: http://$(hostname):80/health/"
}

# Trap errors and cleanup
trap 'error "Deployment failed! Check logs for details."' ERR

# Run main function
main "$@"
