#!/bin/bash

# India Oasis Production Monitoring Script
# This script monitors the health and performance of the production environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="india_oasis"
COMPOSE_FILE="docker-compose.prod.yml"
LOG_FILE="./logs/monitor.log"
ALERT_EMAIL="admin@indiaoasis.com.br"
HEALTH_URL="http://localhost/health/"
MAX_RESPONSE_TIME=5000  # milliseconds
MIN_DISK_SPACE=20       # percentage
MAX_CPU_USAGE=80        # percentage
MAX_MEMORY_USAGE=80     # percentage

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    echo "[ERROR] $1" >> "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
    echo "[INFO] $1" >> "$LOG_FILE"
}

# Send alert email
send_alert() {
    local subject="$1"
    local message="$2"

    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
    else
        warning "Mail command not available. Alert: $subject - $message"
    fi
}

# Check container health
check_containers() {
    log "Checking container health..."

    local containers=("db" "redis" "web" "celery" "celery-beat" "nginx")
    local failed_containers=()

    for container in "${containers[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" ps "$container" | grep -q "Up"; then
            info "✓ $container is running"
        else
            error "✗ $container is not running"
            failed_containers+=("$container")
        fi
    done

    if [ ${#failed_containers[@]} -gt 0 ]; then
        local message="The following containers are not running: ${failed_containers[*]}"
        send_alert "Container Health Alert - $PROJECT_NAME" "$message"
        return 1
    fi

    return 0
}

# Check application health
check_application() {
    log "Checking application health..."

    local start_time=$(date +%s%3N)
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" --max-time 10)
    local end_time=$(date +%s%3N)
    local response_time=$((end_time - start_time))

    if [ "$http_code" = "200" ]; then
        info "✓ Application health check passed (${response_time}ms)"

        if [ $response_time -gt $MAX_RESPONSE_TIME ]; then
            warning "Response time is high: ${response_time}ms (threshold: ${MAX_RESPONSE_TIME}ms)"
            send_alert "High Response Time - $PROJECT_NAME" "Application response time is ${response_time}ms, which exceeds the threshold of ${MAX_RESPONSE_TIME}ms"
        fi

        return 0
    else
        error "✗ Application health check failed (HTTP $http_code)"
        send_alert "Application Health Alert - $PROJECT_NAME" "Health check failed with HTTP code: $http_code"
        return 1
    fi
}

# Check database connectivity
check_database() {
    log "Checking database connectivity..."

    if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1; then
        info "✓ Database is accessible"

        # Check database size
        local db_size=$(docker-compose -f "$COMPOSE_FILE" exec -T db psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-india_oasis}" -t -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB:-india_oasis}'));" 2>/dev/null | xargs)

        if [ -n "$db_size" ]; then
            info "Database size: $db_size"
        fi

        return 0
    else
        error "✗ Database is not accessible"
        send_alert "Database Connectivity Alert - $PROJECT_NAME" "Database is not accessible"
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    log "Checking Redis connectivity..."

    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        info "✓ Redis is accessible"

        # Check Redis memory usage
        local redis_info=$(docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli info memory 2>/dev/null)
        local used_memory=$(echo "$redis_info" | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')

        if [ -n "$used_memory" ]; then
            info "Redis memory usage: $used_memory"
        fi

        return 0
    else
        error "✗ Redis is not accessible"
        send_alert "Redis Connectivity Alert - $PROJECT_NAME" "Redis is not accessible"
        return 1
    fi
}

# Check system resources
check_system_resources() {
    log "Checking system resources..."

    # Check disk space
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    local available_space=$((100 - disk_usage))

    if [ $available_space -lt $MIN_DISK_SPACE ]; then
        error "✗ Low disk space: ${available_space}% available (threshold: ${MIN_DISK_SPACE}%)"
        send_alert "Low Disk Space Alert - $PROJECT_NAME" "Available disk space is ${available_space}%, which is below the threshold of ${MIN_DISK_SPACE}%"
    else
        info "✓ Disk space: ${available_space}% available"
    fi

    # Check CPU usage
    if command -v top &> /dev/null; then
        local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
        local cpu_usage_int=${cpu_usage%.*}

        if [ "$cpu_usage_int" -gt $MAX_CPU_USAGE ]; then
            warning "High CPU usage: ${cpu_usage}% (threshold: ${MAX_CPU_USAGE}%)"
            send_alert "High CPU Usage Alert - $PROJECT_NAME" "CPU usage is ${cpu_usage}%, which exceeds the threshold of ${MAX_CPU_USAGE}%"
        else
            info "✓ CPU usage: ${cpu_usage}%"
        fi
    fi

    # Check memory usage
    if command -v free &> /dev/null; then
        local memory_usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')

        if [ "$memory_usage" -gt $MAX_MEMORY_USAGE ]; then
            warning "High memory usage: ${memory_usage}% (threshold: ${MAX_MEMORY_USAGE}%)"
            send_alert "High Memory Usage Alert - $PROJECT_NAME" "Memory usage is ${memory_usage}%, which exceeds the threshold of ${MAX_MEMORY_USAGE}%"
        else
            info "✓ Memory usage: ${memory_usage}%"
        fi
    fi
}

# Check SSL certificate expiration
check_ssl_certificate() {
    log "Checking SSL certificate..."

    local domain="indiaoasis.com.br"

    if command -v openssl &> /dev/null; then
        local cert_info=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)

        if [ -n "$cert_info" ]; then
            local expiry_date=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
            local expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null)
            local current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))

            if [ $days_until_expiry -lt 30 ]; then
                warning "SSL certificate expires in $days_until_expiry days"
                send_alert "SSL Certificate Expiration Warning - $PROJECT_NAME" "SSL certificate for $domain expires in $days_until_expiry days"
            else
                info "✓ SSL certificate valid for $days_until_expiry more days"
            fi
        else
            warning "Could not retrieve SSL certificate information"
        fi
    else
        info "OpenSSL not available, skipping SSL check"
    fi
}

# Check log file sizes
check_log_files() {
    log "Checking log file sizes..."

    local max_size=104857600  # 100MB in bytes

    find logs -name "*.log" -type f | while read -r logfile; do
        local file_size=$(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null)

        if [ "$file_size" -gt $max_size ]; then
            warning "Large log file detected: $logfile ($(( file_size / 1024 / 1024 ))MB)"
        fi
    done
}

# Check backup status
check_backups() {
    log "Checking backup status..."

    local backup_dir="./backups"
    local latest_backup=$(find "$backup_dir" -name "db_backup_*.sql" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

    if [ -n "$latest_backup" ]; then
        local backup_age=$(( ($(date +%s) - $(stat -c%Y "$latest_backup" 2>/dev/null || stat -f%m "$latest_backup" 2>/dev/null)) / 3600 ))

        if [ $backup_age -gt 24 ]; then
            warning "Latest backup is $backup_age hours old"
            send_alert "Backup Age Warning - $PROJECT_NAME" "Latest database backup is $backup_age hours old"
        else
            info "✓ Latest backup is $backup_age hours old"
        fi
    else
        warning "No database backups found"
        send_alert "No Backups Found - $PROJECT_NAME" "No database backups found in $backup_dir"
    fi
}

# Generate monitoring report
generate_report() {
    local report_file="./logs/monitor_report_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "India Oasis Monitoring Report"
        echo "Generated at: $(date)"
        echo "=================================="
        echo ""

        echo "Container Status:"
        docker-compose -f "$COMPOSE_FILE" ps
        echo ""

        echo "System Resources:"
        df -h /
        free -h
        uptime
        echo ""

        echo "Application Health:"
        curl -s "$HEALTH_URL" | python -m json.tool 2>/dev/null || echo "Health check failed"
        echo ""

        echo "Recent Errors (last 100 lines):"
        tail -100 logs/errors.log 2>/dev/null || echo "No error log found"
        echo ""

        echo "Docker Image Information:"
        docker images | grep india_oasis
        echo ""

    } > "$report_file"

    info "Monitoring report generated: $report_file"
}

# Performance test
performance_test() {
    log "Running performance test..."

    if command -v ab &> /dev/null; then
        local test_url="http://localhost/"
        local result=$(ab -n 100 -c 10 "$test_url" 2>/dev/null | grep "Requests per second\|Time per request")

        if [ -n "$result" ]; then
            info "Performance test results:"
            echo "$result" | while read -r line; do
                info "$line"
            done
        fi
    else
        info "Apache Bench (ab) not available, skipping performance test"
    fi
}

# Main monitoring function
run_monitoring() {
    log "Starting monitoring checks for $PROJECT_NAME"

    local failed_checks=0

    check_containers || ((failed_checks++))
    check_application || ((failed_checks++))
    check_database || ((failed_checks++))
    check_redis || ((failed_checks++))
    check_system_resources
    check_ssl_certificate
    check_log_files
    check_backups

    if [ $failed_checks -eq 0 ]; then
        log "All monitoring checks passed ✓"
    else
        error "$failed_checks monitoring checks failed"
    fi

    return $failed_checks
}

# Main function
main() {
    case "${1:-monitor}" in
        monitor)
            run_monitoring
            ;;
        report)
            generate_report
            ;;
        performance)
            performance_test
            ;;
        containers)
            check_containers
            ;;
        health)
            check_application
            ;;
        resources)
            check_system_resources
            ;;
        ssl)
            check_ssl_certificate
            ;;
        backups)
            check_backups
            ;;
        help)
            echo "Usage: $0 [COMMAND]"
            echo "Commands:"
            echo "  monitor       Run all monitoring checks (default)"
            echo "  report        Generate detailed monitoring report"
            echo "  performance   Run performance test"
            echo "  containers    Check container status only"
            echo "  health        Check application health only"
            echo "  resources     Check system resources only"
            echo "  ssl           Check SSL certificate only"
            echo "  backups       Check backup status only"
            echo "  help          Show this help message"
            ;;
        *)
            error "Unknown command: $1. Use 'help' for available commands."
            exit 1
            ;;
    esac
}

# Create log directory if it doesn't exist
mkdir -p logs

# Run main function
main "$@"
