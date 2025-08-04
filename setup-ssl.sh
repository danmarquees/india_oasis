#!/bin/bash

# India Oasis SSL Setup Script using Let's Encrypt
# This script automates SSL certificate setup and renewal

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="indiaoasis.com.br"
WWW_DOMAIN="www.indiaoasis.com.br"
EMAIL="admin@indiaoasis.com.br"
WEBROOT="/var/www/certbot"
SSL_DIR="./nginx/ssl"
NGINX_CONF_DIR="./nginx/conf.d"
COMPOSE_FILE="docker-compose.prod.yml"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root for SSL certificate management"
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

    log "Dependencies check passed"
}

# Create necessary directories
create_directories() {
    log "Creating SSL directories..."

    mkdir -p "$SSL_DIR"
    mkdir -p "$WEBROOT"
    mkdir -p /var/log/letsencrypt

    # Set permissions
    chmod 755 "$SSL_DIR"
    chmod 755 "$WEBROOT"

    log "SSL directories created"
}

# Create temporary nginx configuration for certificate validation
create_temp_nginx_config() {
    log "Creating temporary nginx configuration..."

    cat > "$NGINX_CONF_DIR/temp-ssl.conf" << EOF
server {
    listen 80;
    server_name $DOMAIN $WWW_DOMAIN;

    # Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
        try_files \$uri =404;
    }

    # Redirect all other traffic to HTTPS (after certificate is obtained)
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

    log "Temporary nginx configuration created"
}

# Install certbot
install_certbot() {
    log "Installing certbot..."

    if command -v certbot &> /dev/null; then
        info "Certbot is already installed"
        return
    fi

    # Install certbot based on OS
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        apt-get update
        apt-get install -y certbot
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum install -y epel-release
        yum install -y certbot
    elif command -v dnf &> /dev/null; then
        # Fedora
        dnf install -y certbot
    else
        # Use Docker method as fallback
        warning "Package manager not found, using Docker for certbot"
        CERTBOT_DOCKER=true
    fi

    log "Certbot installation completed"
}

# Get SSL certificates using certbot
get_certificates() {
    log "Obtaining SSL certificates from Let's Encrypt..."

    # Start nginx temporarily for validation
    docker-compose -f "$COMPOSE_FILE" up -d nginx

    sleep 10

    if [ "$CERTBOT_DOCKER" = true ]; then
        # Use certbot via Docker
        docker run --rm \
            -v "$SSL_DIR:/etc/letsencrypt" \
            -v "$WEBROOT:/var/www/certbot" \
            certbot/certbot certonly \
            --webroot \
            --webroot-path=/var/www/certbot \
            --email "$EMAIL" \
            --agree-tos \
            --no-eff-email \
            --force-renewal \
            -d "$DOMAIN" \
            -d "$WWW_DOMAIN"
    else
        # Use system certbot
        certbot certonly \
            --webroot \
            --webroot-path="$WEBROOT" \
            --email "$EMAIL" \
            --agree-tos \
            --no-eff-email \
            --force-renewal \
            -d "$DOMAIN" \
            -d "$WWW_DOMAIN"

        # Copy certificates to nginx directory
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/"
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/"
    fi

    # Set proper permissions
    chmod 644 "$SSL_DIR/fullchain.pem"
    chmod 600 "$SSL_DIR/privkey.pem"

    log "SSL certificates obtained successfully"
}

# Create DH parameters for enhanced security
create_dhparam() {
    log "Generating DH parameters (this may take a while)..."

    if [ ! -f "$SSL_DIR/dhparam.pem" ]; then
        openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048
        chmod 644 "$SSL_DIR/dhparam.pem"
        log "DH parameters generated"
    else
        info "DH parameters already exist"
    fi
}

# Update nginx configuration with SSL
update_nginx_config() {
    log "Updating nginx configuration with SSL..."

    # Remove temporary configuration
    rm -f "$NGINX_CONF_DIR/temp-ssl.conf"

    # The main SSL configuration should already be in place
    # from the previous nginx configuration files

    log "Nginx configuration updated"
}

# Create certificate renewal script
create_renewal_script() {
    log "Creating certificate renewal script..."

    cat > /usr/local/bin/renew-ssl-india-oasis.sh << 'EOF'
#!/bin/bash

# India Oasis SSL Certificate Renewal Script

set -e

# Configuration
DOMAIN="indiaoasis.com.br"
SSL_DIR="/path/to/india_oasis/nginx/ssl"
COMPOSE_FILE="/path/to/india_oasis/docker-compose.prod.yml"
LOG_FILE="/var/log/ssl-renewal.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting SSL certificate renewal check..."

# Renew certificates
if certbot renew --quiet --deploy-hook "systemctl reload nginx"; then
    log "Certificate renewal check completed successfully"

    # Copy renewed certificates
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/"
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/"
        chmod 644 "$SSL_DIR/fullchain.pem"
        chmod 600 "$SSL_DIR/privkey.pem"

        # Reload nginx in Docker
        docker-compose -f "$COMPOSE_FILE" exec nginx nginx -s reload

        log "Certificates updated and nginx reloaded"
    fi
else
    log "Certificate renewal failed"
    exit 1
fi

log "SSL renewal process completed"
EOF

    # Make the script executable
    chmod +x /usr/local/bin/renew-ssl-india-oasis.sh

    # Update paths in the script
    sed -i "s|/path/to/india_oasis|$(pwd)|g" /usr/local/bin/renew-ssl-india-oasis.sh

    log "Certificate renewal script created"
}

# Setup automatic renewal with cron
setup_auto_renewal() {
    log "Setting up automatic certificate renewal..."

    # Create cron job for certificate renewal (twice daily)
    cat > /etc/cron.d/india-oasis-ssl-renewal << EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# India Oasis SSL Certificate Renewal
# Runs twice daily at 12:00 and 00:00
0 0,12 * * * root /usr/local/bin/renew-ssl-india-oasis.sh >/dev/null 2>&1
EOF

    # Set proper permissions
    chmod 644 /etc/cron.d/india-oasis-ssl-renewal

    # Restart cron service
    if systemctl is-active --quiet cron; then
        systemctl restart cron
    elif systemctl is-active --quiet crond; then
        systemctl restart crond
    fi

    log "Automatic renewal setup completed"
}

# Test SSL configuration
test_ssl_config() {
    log "Testing SSL configuration..."

    # Test nginx configuration
    if docker-compose -f "$COMPOSE_FILE" exec nginx nginx -t; then
        info "✓ Nginx configuration is valid"
    else
        error "✗ Nginx configuration test failed"
    fi

    # Restart nginx with SSL configuration
    docker-compose -f "$COMPOSE_FILE" restart nginx

    sleep 10

    # Test HTTPS connectivity
    if curl -f -s "https://$DOMAIN/health/" > /dev/null; then
        info "✓ HTTPS connectivity test passed"
    else
        warning "✗ HTTPS connectivity test failed - please check manually"
    fi

    # Test SSL certificate
    if openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -verify_return_error < /dev/null > /dev/null 2>&1; then
        info "✓ SSL certificate validation passed"
    else
        warning "✗ SSL certificate validation failed - please check manually"
    fi

    log "SSL configuration testing completed"
}

# Create SSL monitoring script
create_ssl_monitor() {
    log "Creating SSL monitoring script..."

    cat > /usr/local/bin/monitor-ssl-india-oasis.sh << 'EOF'
#!/bin/bash

# India Oasis SSL Certificate Monitoring Script

set -e

DOMAIN="indiaoasis.com.br"
ALERT_EMAIL="admin@indiaoasis.com.br"
LOG_FILE="/var/log/ssl-monitor.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check certificate expiration
check_certificate_expiry() {
    local expiry_date=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
    local expiry_timestamp=$(date -d "$expiry_date" +%s)
    local current_timestamp=$(date +%s)
    local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))

    log "SSL certificate expires in $days_until_expiry days"

    if [ $days_until_expiry -lt 7 ]; then
        log "WARNING: SSL certificate expires in $days_until_expiry days!"

        # Send alert email
        if command -v mail &> /dev/null; then
            echo "SSL certificate for $DOMAIN expires in $days_until_expiry days. Please renew immediately." | \
                mail -s "URGENT: SSL Certificate Expiring Soon - $DOMAIN" "$ALERT_EMAIL"
        fi

        return 1
    elif [ $days_until_expiry -lt 30 ]; then
        log "NOTICE: SSL certificate expires in $days_until_expiry days"
        return 0
    else
        log "SSL certificate is valid for $days_until_expiry more days"
        return 0
    fi
}

# Main monitoring
log "Starting SSL certificate monitoring for $DOMAIN"
check_certificate_expiry
log "SSL monitoring completed"
EOF

    chmod +x /usr/local/bin/monitor-ssl-india-oasis.sh

    # Add monitoring to cron (daily check)
    cat >> /etc/cron.d/india-oasis-ssl-renewal << EOF

# SSL Certificate Monitoring (daily at 08:00)
0 8 * * * root /usr/local/bin/monitor-ssl-india-oasis.sh >/dev/null 2>&1
EOF

    log "SSL monitoring script created"
}

# Backup existing certificates
backup_certificates() {
    if [ -f "$SSL_DIR/fullchain.pem" ]; then
        log "Backing up existing certificates..."
        cp "$SSL_DIR/fullchain.pem" "$SSL_DIR/fullchain.pem.backup.$(date +%Y%m%d)"
        cp "$SSL_DIR/privkey.pem" "$SSL_DIR/privkey.pem.backup.$(date +%Y%m%d)" 2>/dev/null || true
        log "Certificates backed up"
    fi
}

# Main function
main() {
    log "Starting SSL setup for India Oasis"

    case "${1:-setup}" in
        setup)
            check_root
            check_dependencies
            create_directories
            backup_certificates
            create_temp_nginx_config
            install_certbot
            get_certificates
            create_dhparam
            update_nginx_config
            create_renewal_script
            setup_auto_renewal
            create_ssl_monitor
            test_ssl_config
            log "SSL setup completed successfully!"
            info "Your site should now be accessible at: https://$DOMAIN"
            ;;
        renew)
            log "Manual certificate renewal requested"
            /usr/local/bin/renew-ssl-india-oasis.sh
            ;;
        monitor)
            /usr/local/bin/monitor-ssl-india-oasis.sh
            ;;
        test)
            test_ssl_config
            ;;
        help)
            echo "Usage: $0 [COMMAND]"
            echo "Commands:"
            echo "  setup     Setup SSL certificates (default)"
            echo "  renew     Manually renew certificates"
            echo "  monitor   Check certificate expiration"
            echo "  test      Test SSL configuration"
            echo "  help      Show this help message"
            ;;
        *)
            error "Unknown command: $1. Use 'help' for available commands."
            ;;
    esac
}

# Run main function
main "$@"
