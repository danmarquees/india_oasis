#!/bin/bash

# India Oasis Development Setup Script
# This script sets up the local development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="India Oasis"
PYTHON_VERSION="3.11"
VENV_NAME="venv"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
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

# Check if Python is installed
check_python() {
    log "Checking Python installation..."

    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        error "Python is not installed. Please install Python 3.8+ first."
    fi

    # Check Python version
    PYTHON_VER=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
    PYTHON_MAJOR=$(echo $PYTHON_VER | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VER | cut -d'.' -f2)

    if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 8 ]]; then
        info "✓ Python $PYTHON_VER found"
    else
        error "Python 3.8+ is required. Found: $PYTHON_VER"
    fi
}

# Check if pip is installed
check_pip() {
    log "Checking pip..."

    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        error "pip is not installed. Please install pip first."
    fi

    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi

    info "✓ pip found"
}

# Create virtual environment
create_venv() {
    log "Creating virtual environment..."

    if [ -d "$VENV_NAME" ]; then
        warning "Virtual environment already exists. Removing old one..."
        rm -rf "$VENV_NAME"
    fi

    $PYTHON_CMD -m venv "$VENV_NAME"

    # Activate virtual environment
    source "$VENV_NAME/bin/activate" || source "$VENV_NAME/Scripts/activate" 2>/dev/null

    # Upgrade pip
    pip install --upgrade pip

    info "✓ Virtual environment created: $VENV_NAME"
}

# Install dependencies
install_dependencies() {
    log "Installing dependencies..."

    # Activate virtual environment
    source "$VENV_NAME/bin/activate" || source "$VENV_NAME/Scripts/activate" 2>/dev/null

    # Install production requirements
    if [ -f "requirements.txt" ]; then
        info "Installing production requirements..."
        pip install -r requirements.txt
    else
        error "requirements.txt not found!"
    fi

    # Install development requirements
    if [ -f "requirements-dev.txt" ]; then
        info "Installing development requirements..."
        pip install -r requirements-dev.txt
    else
        warning "requirements-dev.txt not found. Skipping development dependencies."
    fi

    info "✓ Dependencies installed"
}

# Setup environment file
setup_env_file() {
    log "Setting up environment file..."

    if [ ! -f ".env" ]; then
        if [ -f ".env.development" ]; then
            cp ".env.development" ".env"
            info "✓ Environment file created from .env.development"
        elif [ -f ".env.example" ]; then
            cp ".env.example" ".env"
            warning "Environment file created from .env.example - please review and update it"
        else
            warning "No environment template found. Creating basic .env file..."
            cat > .env << EOF
DEBUG=True
SECRET_KEY=dev-secret-key-change-this-in-production-12345678901234567890
DJANGO_SETTINGS_MODULE=india_oasis_project.settings_development
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
EOF
        fi
    else
        info "✓ Environment file already exists"
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."

    mkdir -p logs
    mkdir -p media
    mkdir -p static
    mkdir -p staticfiles

    # Create empty log file
    touch logs/development.log

    info "✓ Directories created"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    # Activate virtual environment
    source "$VENV_NAME/bin/activate" || source "$VENV_NAME/Scripts/activate" 2>/dev/null

    # Set Django settings
    export DJANGO_SETTINGS_MODULE=india_oasis_project.settings_development

    # Run migrations
    python manage.py makemigrations
    python manage.py migrate

    info "✓ Database migrations completed"
}

# Collect static files
collect_static() {
    log "Collecting static files..."

    # Activate virtual environment
    source "$VENV_NAME/bin/activate" || source "$VENV_NAME/Scripts/activate" 2>/dev/null

    # Set Django settings
    export DJANGO_SETTINGS_MODULE=india_oasis_project.settings_development

    # Collect static files
    python manage.py collectstatic --noinput

    info "✓ Static files collected"
}

# Create superuser
create_superuser() {
    log "Creating superuser..."

    # Activate virtual environment
    source "$VENV_NAME/bin/activate" || source "$VENV_NAME/Scripts/activate" 2>/dev/null

    # Set Django settings
    export DJANGO_SETTINGS_MODULE=india_oasis_project.settings_development

    # Check if superuser already exists
    if python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).exists())" | grep -q "True"; then
        info "✓ Superuser already exists"
    else
        # Create superuser with environment variables or prompt
        if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
            python manage.py createsuperuser --noinput
            info "✓ Superuser created: $DJANGO_SUPERUSER_USERNAME"
        else
            warning "Creating superuser with default credentials (admin/admin123)"
            echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@localhost', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell
            info "✓ Superuser created: admin/admin123"
        fi
    fi
}

# Install pre-commit hooks
setup_pre_commit() {
    if command -v pre-commit &> /dev/null; then
        log "Setting up pre-commit hooks..."

        # Activate virtual environment
        source "$VENV_NAME/bin/activate" || source "$VENV_NAME/Scripts/activate" 2>/dev/null

        # Create pre-commit config if it doesn't exist
        if [ ! -f ".pre-commit-config.yaml" ]; then
            cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-yaml
EOF
        fi

        pre-commit install
        info "✓ Pre-commit hooks installed"
    else
        info "Pre-commit not available, skipping hooks setup"
    fi
}

# Generate secret key
generate_secret_key() {
    log "Generating Django secret key..."

    # Activate virtual environment
    source "$VENV_NAME/bin/activate" || source "$VENV_NAME/Scripts/activate" 2>/dev/null

    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

    # Update .env file with new secret key
    if [ -f ".env" ]; then
        if grep -q "SECRET_KEY=" .env; then
            sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        else
            echo "SECRET_KEY=$SECRET_KEY" >> .env
        fi
        info "✓ Secret key generated and saved to .env"
    fi
}

# Create development scripts
create_dev_scripts() {
    log "Creating development scripts..."

    # Create run script
    cat > run-dev.sh << 'EOF'
#!/bin/bash
# Start development server

echo "🚀 Starting India Oasis Development Server..."

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Set Django settings
export DJANGO_SETTINGS_MODULE=india_oasis_project.settings_development

# Run development server
python manage.py runserver 0.0.0.0:8000
EOF

    # Create test script
    cat > test.sh << 'EOF'
#!/bin/bash
# Run tests

echo "🧪 Running Tests..."

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Set Django settings
export DJANGO_SETTINGS_MODULE=india_oasis_project.settings_development

# Run tests
python manage.py test
EOF

    # Create shell script
    cat > shell.sh << 'EOF'
#!/bin/bash
# Start Django shell

echo "🐚 Starting Django Shell..."

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Set Django settings
export DJANGO_SETTINGS_MODULE=india_oasis_project.settings_development

# Start shell
python manage.py shell
EOF

    # Make scripts executable
    chmod +x run-dev.sh test.sh shell.sh

    info "✓ Development scripts created"
}

# Print success message and instructions
print_success() {
    echo ""
    echo -e "${GREEN}🎉 Development environment setup completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📁 Project: $PROJECT_NAME${NC}"
    echo -e "${BLUE}🐍 Python: $PYTHON_VER${NC}"
    echo -e "${BLUE}📦 Virtual Environment: $VENV_NAME${NC}"
    echo ""
    echo -e "${YELLOW}🚀 To start development:${NC}"
    echo -e "   ${GREEN}./run-dev.sh${NC}                 # Start development server"
    echo -e "   ${GREEN}./test.sh${NC}                    # Run tests"
    echo -e "   ${GREEN}./shell.sh${NC}                   # Start Django shell"
    echo ""
    echo -e "${YELLOW}🔧 Useful commands:${NC}"
    echo -e "   ${GREEN}source venv/bin/activate${NC}     # Activate virtual environment"
    echo -e "   ${GREEN}python manage.py runserver${NC}   # Start server manually"
    echo -e "   ${GREEN}python manage.py makemigrations${NC} # Create migrations"
    echo -e "   ${GREEN}python manage.py migrate${NC}     # Apply migrations"
    echo ""
    echo -e "${YELLOW}🌐 URLs:${NC}"
    echo -e "   ${GREEN}http://localhost:8000${NC}        # Main application"
    echo -e "   ${GREEN}http://localhost:8000/admin${NC}   # Admin interface"
    echo -e "   ${GREEN}http://localhost:8000/health${NC}  # Health check"
    echo ""
    echo -e "${YELLOW}👤 Admin credentials:${NC}"
    echo -e "   ${GREEN}Username: admin${NC}"
    echo -e "   ${GREEN}Password: admin123${NC}"
    echo ""
    echo -e "${BLUE}Happy coding! 🎈${NC}"
}

# Main setup function
main() {
    log "Starting $PROJECT_NAME development environment setup..."

    check_python
    check_pip
    create_venv
    install_dependencies
    setup_env_file
    create_directories
    generate_secret_key
    run_migrations
    collect_static
    create_superuser
    setup_pre_commit
    create_dev_scripts
    print_success
}

# Run main function
main "$@"
