#!/bin/bash

# India Oasis - Initial Setup Script for Hostinger VPS
# This script sets up the production environment from scratch
# Usage: curl -sSL https://raw.githubusercontent.com/your-repo/india-oasis/main/scripts/setup.sh | bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "/tmp")"
PROJECT_NAME="india_oasis"
PROJECT_DIR="/opt/$PROJECT_NAME"
DEPLOY_USER="django"
DOCKER_COMPOSE_VERSION="2.23.0"
NODE_VERSION="18"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
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
        error "This script must be run as root"
        echo "Run: sudo $0"
        exit 1
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."

    apt-get update
    apt-get upgrade -y

    # Install essential packages
    apt-get install -y \
        curl \
        wget \
        gnupg \
        lsb-release \
        ca-certificates \
        software-properties-common \
        apt-transport-https \
        build-essential \
        git \
        unzip \
        supervisor \
        nginx \
        certbot \
        python3-certbot-nginx \
        htop \
        fail2ban \
        ufw \
        logrotate

    log "System update completed"
}

# Install Docker
install_docker() {
    log "Installing Docker..."

    # Remove old Docker installations
    apt-get remove -y docker docker-engine docker.io containerd runc || true

    # Add Docker GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

    # Install Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Start and enable Docker
    systemctl start docker
    systemctl enable docker

    # Install Docker Compose standalone
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    # Verify installation
    docker --version
    docker-compose --version

    log "Docker installation completed"
}

# Install Node.js (for frontend tools)
install_nodejs() {
    log "Installing Node.js..."

    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt-get install -y nodejs

    # Install global packages
    npm install -g pm2

    node --version
    npm --version

    log "Node.js installation completed"
}

# Create deployment user
create_deploy_user() {
    log "Creating deployment user..."

    # Create user if doesn't exist
    if ! id "$DEPLOY_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$DEPLOY_USER"
        usermod -aG docker "$DEPLOY_USER"
        usermod -aG sudo "$DEPLOY_USER"
    fi

    # Create SSH directory
    mkdir -p "/home/$DEPLOY_USER/.ssh"
    chmod 700 "/home/$DEPLOY_USER/.ssh"
    chown "$DEPLOY_USER:$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"

    # Set up sudoers
    echo "$DEPLOY_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$DEPLOY_USER"

    log "Deployment user created: $DEPLOY_USER"
}

# Configure firewall
setup_firewall() {
    log "Configuring firewall..."

    # Reset UFW
    ufw --force reset

    # Default policies
    ufw default deny incoming
    ufw default allow outgoing

    # Allow SSH (keep current connection)
    ufw allow ssh

    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp

    # Allow Docker subnet
    ufw allow from 172.0.0.0/8

    # Enable firewall
    ufw --force enable

    log "Firewall configuration completed"
}

# Configure Nginx
setup_nginx() {
    log "Configuring Nginx..."

    # Remove default site
    rm -f /etc/nginx/sites-enabled/default

    # Create project directory
    mkdir -p "$PROJECT_DIR"
    chown "$DEPLOY_USER:$DEPLOY_USER" "$PROJECT_DIR"

    # Create basic Nginx configuration
    cat > /etc/nginx/sites-available/$PROJECT_NAME << 'EOF'
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /opt/india_oasis/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/india_oasis/media/;
        expires 1M;
        add_header Cache-Control "public";
    }

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location = /robots.txt {
        access_log off;
        log_not_found off;
    }
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/

    # Test and reload Nginx
    nginx -t
    systemctl reload nginx

    log "Nginx configuration completed"
}

# Configure Fail2Ban
setup_fail2ban() {
    log "Configuring Fail2Ban..."

    # Create jail for Nginx
    cat > /etc/fail2ban/jail.d/nginx.conf << 'EOF'
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10

[nginx-botsearch]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 2
EOF

    systemctl enable fail2ban
    systemctl restart fail2ban

    log "Fail2Ban configuration completed"
}

# Setup log rotation
setup_logrotate() {
    log "Setting up log rotation..."

    cat > /etc/logrotate.d/india-oasis << 'EOF'
/opt/india_oasis/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su django django
}
EOF

    log "Log rotation setup completed"
}

# Create directory structure
create_directories() {
    log "Creating directory structure..."

    mkdir -p "$PROJECT_DIR"/{logs,media,staticfiles,backups,ssl}
    mkdir -p /var/log/india_oasis

    chown -R "$DEPLOY_USER:$DEPLOY_USER" "$PROJECT_DIR"
    chown -R "$DEPLOY_USER:$DEPLOY_USER" /var/log/india_oasis

    log "Directory structure created"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."

    # Create monitoring script
    cat > /usr/local/bin/india-oasis-monitor << 'EOF'
#!/bin/bash
# Simple monitoring script for India Oasis

LOG_FILE="/var/log/india_oasis/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check if containers are running
if ! docker-compose -f /opt/india_oasis/docker-compose.prod.yml ps | grep -q "Up"; then
    echo "[$DATE] ERROR: Some containers are not running" >> $LOG_FILE
    # Send alert (configure your preferred notification method)
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "[$DATE] WARNING: Disk usage is ${DISK_USAGE}%" >> $LOG_FILE
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ "$MEM_USAGE" -gt 85 ]; then
    echo "[$DATE] WARNING: Memory usage is ${MEM_USAGE}%" >> $LOG_FILE
fi

echo "[$DATE] Health check completed" >> $LOG_FILE
EOF

    chmod +x /usr/local/bin/india-oasis-monitor

    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/india-oasis-monitor") | crontab -

    log "Monitoring setup completed"
}

# Optimize system for production
optimize_system() {
    log "Optimizing system for production..."

    # Kernel parameters
    cat >> /etc/sysctl.conf << 'EOF'

# India Oasis optimizations
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 400000
net.ipv4.tcp_tw_reuse = 1
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

    sysctl -p

    # Increase file limits
    cat >> /etc/security/limits.conf << 'EOF'

# India Oasis limits
django soft nofile 65535
django hard nofile 65535
django soft nproc 32768
django hard nproc 32768
EOF

    log "System optimization completed"
}

# Display final instructions
show_final_instructions() {
    log "Setup completed successfully!"

    info "Next steps:"
    echo "1. Clone your repository to $PROJECT_DIR"
    echo "2. Create .env file with your configuration"
    echo "3. Run the deployment script: ./scripts/deploy.sh"
    echo ""
    echo "Useful commands:"
    echo "  - Switch to deploy user: sudo su - $DEPLOY_USER"
    echo "  - Check logs: tail -f $PROJECT_DIR/logs/*.log"
    echo "  - Monitor containers: docker-compose -f $PROJECT_DIR/docker-compose.prod.yml ps"
    echo "  - View system status: systemctl status nginx docker"
    echo ""
    echo "Security notes:"
    echo "  - Change default SSH port: Edit /etc/ssh/sshd_config"
    echo "  - Setup SSL certificate: certbot --nginx -d yourdomain.com"
    echo "  - Configure backup strategy for database and media files"
    echo ""
    warning "Remember to:"
    warning "  - Set strong passwords for all accounts"
    warning "  - Configure proper DNS records"
    warning "  - Set up SSL certificates"
    warning "  - Configure monitoring and alerting"
}

# Main setup function
main() {
    log "Starting India Oasis server setup..."

    check_root
    update_system
    install_docker
    install_nodejs
    create_deploy_user
    setup_firewall
    setup_nginx
    setup_fail2ban
    setup_logrotate
    create_directories
    setup_monitoring
    optimize_system
    show_final_instructions

    log "Server setup completed successfully!"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
