#!/usr/bin/env python
"""
Automated conversion script for India Oasis project
Converts the project from VPS/Docker setup to cPanel compatible version

This script:
1. Creates cPanel-compatible directory structure
2. Modifies settings and configurations
3. Updates dependencies
4. Creates deployment files
5. Prepares migration scripts

Usage:
    python scripts/convert_to_cpanel.py [--output-dir cpanel_version]
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
import re
import json

class cPanelConverter:
    def __init__(self, project_root, output_dir):
        self.project_root = Path(project_root)
        self.output_dir = Path(output_dir)
        self.conversion_log = []

    def log(self, message, level="INFO"):
        """Log conversion steps"""
        log_entry = f"[{level}] {message}"
        self.conversion_log.append(log_entry)
        print(log_entry)

    def create_output_directory(self):
        """Create output directory structure"""
        self.log("Creating output directory structure...")

        # Create main directories
        directories = [
            "",
            "logs",
            "cache",
            "media",
            "static",
            "public_html",
            "public_html/static",
            "public_html/media",
            "scripts",
            "backups",
            "templates"
        ]

        for dir_path in directories:
            full_path = self.output_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            self.log(f"Created directory: {full_path}")

    def copy_core_files(self):
        """Copy core Django files and apps"""
        self.log("Copying core Django files...")

        # Files and directories to copy
        copy_items = [
            "manage.py",
            "india_oasis_project",
            "store",
            "payment_processing",
            "email_service",
            "templates",
            "static",
            "media"
        ]

        for item in copy_items:
            src = self.project_root / item
            dst = self.output_dir / item

            if src.exists():
                if src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst, ignore=self.ignore_files)
                    self.log(f"Copied directory: {item}")
                else:
                    shutil.copy2(src, dst)
                    self.log(f"Copied file: {item}")
            else:
                self.log(f"Warning: {item} not found", "WARN")

    def ignore_files(self, dir, files):
        """Ignore unnecessary files during copy"""
        ignore = {
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.git',
            '.gitignore',
            'Dockerfile',
            'docker-compose.yml',
            'docker-compose.prod.yml',
            '.dockerignore',
            'requirements-prod.txt',
            'requirements-dev.txt',
            'Procfile',
            'build.sh',
            'deploy.sh',
            'nginx',
            'venv',
            'virtualenv'
        }

        return [f for f in files if f in ignore or f.endswith('.pyc')]

    def create_cpanel_settings(self):
        """Create cPanel-specific settings file"""
        self.log("Creating cPanel settings...")

        settings_content = '''"""
Django settings for india_oasis_project - cPanel Optimized Version

This settings file is specifically configured for GoDaddy cPanel shared hosting.
It removes complex dependencies like Redis, Celery, and PostgreSQL.
"""

from pathlib import Path
import environ
import os
import logging.config

# Initialise environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# cPanel hosting typically uses domain names
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'payment_processing',
    'email_service',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'india_oasis_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'store.context_processors.cart_processor',
                'store.context_processors.static_files_processor',
                'store.context_processors.categories_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'india_oasis_project.wsgi.application'

# Database - MySQL for cPanel compatibility
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'public_html' / 'static'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'public_html' / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# MercadoPago Settings
MERCADO_PAGO_PUBLIC_KEY = env('MERCADO_PAGO_PUBLIC_KEY')
MERCADO_PAGO_ACCESS_TOKEN = env('MERCADO_PAGO_ACCESS_TOKEN')

# Melhor Envio Settings
MELHOR_ENVIO_TOKEN = env('MELHOR_ENVIO_TOKEN', default='')
MELHOR_ENVIO_CEP_ORIGEM = env('MELHOR_ENVIO_CEP_ORIGEM', default='01034-001')

# Email Settings (simplified for cPanel)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@yourdomain.com')
EMAIL_TIMEOUT = 30

# Order email notifications
ORDER_EMAIL_ENABLED = env('ORDER_EMAIL_ENABLED', default=True)
ORDER_EMAIL_ADMIN = env('ORDER_EMAIL_ADMIN', default='admin@yourdomain.com')

# Logging Configuration (simplified for cPanel)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'store': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'payment_processing': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
    SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
    CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', default=3600)
SESSION_COOKIE_NAME = 'india_oasis_sessionid'
SESSION_COOKIE_HTTPONLY = True

# Cache Configuration (file-based cache for cPanel)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': BASE_DIR / 'cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        },
    }
}

# Application-specific settings
MAX_CART_ITEMS = env.int('MAX_CART_ITEMS', default=50)
ORDER_TIMEOUT_MINUTES = env.int('ORDER_TIMEOUT_MINUTES', default=30)

# Version
VERSION = env('VERSION', default='1.0.0-cpanel')

# cPanel specific settings
FORCE_SCRIPT_NAME = env('FORCE_SCRIPT_NAME', default='')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Disable features that require background processing
ENABLE_BACKGROUND_TASKS = False
ENABLE_ASYNC_PROCESSING = False

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'cache', exist_ok=True)
'''

        settings_file = self.output_dir / 'india_oasis_project' / 'settings_cpanel.py'
        settings_file.write_text(settings_content)
        self.log("Created cPanel settings file")

    def create_passenger_wsgi(self):
        """Create passenger_wsgi.py for cPanel"""
        self.log("Creating passenger WSGI file...")

        wsgi_content = '''"""
WSGI config for india_oasis_project - cPanel Passenger compatible

This module contains the WSGI application used by Passenger on cPanel hosting.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_home = Path(__file__).resolve().parent
if project_home not in sys.path:
    sys.path.insert(0, str(project_home))

# Set the Django settings module for cPanel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'india_oasis_project.settings_cpanel')

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except ImportError:
    # Handle import errors gracefully
    import traceback
    import logging

    # Log the error
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=project_home / 'logs' / 'wsgi_error.log'
    )

    logging.error("Failed to import Django WSGI application")
    logging.error(traceback.format_exc())

    # Create a simple error application
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/html')]
        start_response(status, response_headers)

        error_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>India Oasis - Erro de Sistema</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .error { color: #d32f2f; background: #ffebee; padding: 20px; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="error">
                <h2>Erro de Configuração</h2>
                <p>Ocorreu um erro ao carregar a aplicação Django.</p>
                <p>Verifique os logs em <code>logs/wsgi_error.log</code> para mais detalhes.</p>
            </div>
        </body>
        </html>
        """

        return [error_html.encode('utf-8')]

# Ensure logs directory exists
logs_dir = project_home / 'logs'
logs_dir.mkdir(exist_ok=True)
'''

        wsgi_file = self.output_dir / 'passenger_wsgi.py'
        wsgi_file.write_text(wsgi_content)
        self.log("Created passenger WSGI file")

    def create_requirements(self):
        """Create simplified requirements.txt for cPanel"""
        self.log("Creating simplified requirements...")

        requirements_content = '''# India Oasis - cPanel Compatible Requirements
# Simplified dependencies for GoDaddy cPanel shared hosting

# Core Django
Django==5.2.3
asgiref==3.8.1
sqlparse==0.5.3

# MySQL Database (instead of PostgreSQL)
mysqlclient==2.2.4

# Environment and Configuration
django-environ==0.11.2

# Static Files (no whitenoise needed in cPanel)
Pillow==11.2.1

# Payment Processing
mercadopago==2.2.0

# HTTP Client
requests==2.31.0

# Email
django-email-backend==1.1.0

# Security (basic only)
django-cors-headers==4.3.1

# Utilities
python-dateutil==2.8.2
pytz==2023.3

# File handling
python-magic==0.4.27

# JSON handling
python-json-logger==2.0.7
'''

        req_file = self.output_dir / 'requirements-cpanel.txt'
        req_file.write_text(requirements_content)
        self.log("Created cPanel requirements file")

    def create_env_example(self):
        """Create example .env file for cPanel"""
        self.log("Creating example environment file...")

        env_content = '''# India Oasis - cPanel Environment Configuration
# Copy this file to .env and update with your actual values

# Django Core Settings
SECRET_KEY=your-very-long-secret-key-here-minimum-50-characters
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (MySQL for cPanel)
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306

# Email Settings
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=False
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
ORDER_EMAIL_ADMIN=admin@yourdomain.com
ORDER_EMAIL_ENABLED=True

# Payment Processing
MERCADO_PAGO_PUBLIC_KEY=APP_USR-your-public-key-here
MERCADO_PAGO_ACCESS_TOKEN=APP_USR-your-access-token-here

# Shipping Integration
MELHOR_ENVIO_TOKEN=your-melhor-envio-token
MELHOR_ENVIO_CEP_ORIGEM=01034-001

# Security Settings
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Application Settings
VERSION=1.0.0-cpanel
MAX_CART_ITEMS=50
ORDER_TIMEOUT_MINUTES=30
SESSION_COOKIE_AGE=3600

# Admin Settings
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
ADMIN_EMAIL=admin@yourdomain.com
'''

        env_file = self.output_dir / '.env.cpanel.example'
        env_file.write_text(env_content)
        self.log("Created example environment file")

    def create_htaccess(self):
        """Create .htaccess file for cPanel"""
        self.log("Creating .htaccess file...")

        htaccess_content = '''# India Oasis - cPanel Configuration
RewriteEngine On

# Handle static files
RewriteRule ^static/(.*)$ /public_html/static/$1 [L]
RewriteRule ^media/(.*)$ /public_html/media/$1 [L]

# Python application configuration
# These will be set automatically by cPanel Python App setup
# PassengerAppRoot "/home/username/indiaoasis"
# PassengerBaseURI "/"
# PassengerPython "/home/username/virtualenv/indiaoasis/3.11/bin/python"
# PassengerAppLogFile "/home/username/indiaoasis/logs/passenger.log"

# Security headers
<IfModule mod_headers.c>
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>

# Compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>

# Browser caching for static files
<IfModule mod_expires.c>
    ExpiresActive on
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/ico "access plus 1 year"
    ExpiresByType image/icon "access plus 1 year"
    ExpiresByType text/plain "access plus 1 month"
    ExpiresByType application/pdf "access plus 1 month"
</IfModule>
'''

        htaccess_file = self.output_dir / '.htaccess.example'
        htaccess_file.write_text(htaccess_content)
        self.log("Created example .htaccess file")

    def create_migration_script(self):
        """Create MySQL migration script"""
        self.log("Creating MySQL migration script...")

        script_content = '''#!/usr/bin/env python
"""
MySQL Migration Script for India Oasis cPanel Version
Run this script after uploading to cPanel to set up the database
"""

import os
import sys
import django
from pathlib import Path

# Add project to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'india_oasis_project.settings_cpanel')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'migration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_database_connection():
    """Test database connection"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            logger.info(f"Connected to MySQL version: {version[0]}")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def run_migrations():
    """Run Django migrations"""
    try:
        logger.info("Running Django migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        logger.info("Migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def collect_static():
    """Collect static files"""
    try:
        logger.info("Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        logger.info("Static files collected successfully")
        return True
    except Exception as e:
        logger.error(f"Static files collection failed: {e}")
        return False

def create_superuser():
    """Create superuser if needed"""
    try:
        from django.contrib.auth.models import User

        if User.objects.filter(is_superuser=True).exists():
            logger.info("Superuser already exists")
            return True

        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@yourdomain.com')
        password = os.environ.get('ADMIN_PASSWORD')

        if password:
            User.objects.create_superuser(username, email, password)
            logger.info(f"Superuser '{username}' created successfully")
        else:
            logger.info("Run 'python manage.py createsuperuser' to create admin user")

        return True
    except Exception as e:
        logger.error(f"Superuser creation failed: {e}")
        return False

def main():
    """Main setup process"""
    logger.info("Starting cPanel setup...")

    # Create logs directory
    (project_root / 'logs').mkdir(exist_ok=True)

    steps = [
        ("Database connection", check_database_connection),
        ("Migrations", run_migrations),
        ("Static files", collect_static),
        ("Superuser", create_superuser),
    ]

    for step_name, step_func in steps:
        logger.info(f"Running: {step_name}")
        if not step_func():
            logger.error(f"Failed: {step_name}")
            return False
        logger.info(f"Completed: {step_name}")

    logger.info("cPanel setup completed successfully!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
'''

        script_file = self.output_dir / 'scripts' / 'setup_cpanel.py'
        script_file.write_text(script_content)
        script_file.chmod(0o755)
        self.log("Created MySQL migration script")

    def create_deployment_guide(self):
        """Create deployment guide"""
        self.log("Creating deployment guide...")

        guide_content = '''# India Oasis - cPanel Deployment Guide

## Quick Start

1. **Upload Files**
   - Upload all files to your cPanel hosting
   - Extract to desired directory (e.g., `indiaoasis/`)

2. **Database Setup**
   - Create MySQL database in cPanel
   - Update `.env` file with database credentials

3. **Python App Setup**
   - Go to cPanel > Setup Python App
   - Application root: `indiaoasis`
   - Startup file: `passenger_wsgi.py`
   - Entry point: `application`

4. **Install Dependencies**
   ```bash
   source /home/username/virtualenv/indiaoasis/3.11/bin/activate
   cd ~/indiaoasis
   pip install -r requirements-cpanel.txt
   ```

5. **Run Setup Script**
   ```bash
   python scripts/setup_cpanel.py
   ```

6. **Configure Domain**
   - Update `.htaccess` as needed
   - Test the application

## Detailed Instructions

See `DEPLOY_CPANEL.md` for complete deployment instructions.

## Support

Check logs in `logs/` directory for troubleshooting.
'''

        guide_file = self.output_dir / 'README_CPANEL.md'
        guide_file.write_text(guide_content)
        self.log("Created deployment guide")

    def remove_incompatible_code(self):
        """Remove code that's incompatible with cPanel"""
        self.log("Removing incompatible code...")

        # Files to check and modify
        files_to_modify = [
            'store/views.py',
            'payment_processing/views.py',
            'email_service/views.py'
        ]

        for file_path in files_to_modify:
            full_path = self.output_dir / file_path
            if full_path.exists():
                content = full_path.read_text()

                # Remove Celery imports and calls
                content = re.sub(r'from celery.*\n', '', content)
                content = re.sub(r'import celery.*\n', '', content)
                content = re.sub(r'@shared_task.*\n', '', content)
                content = re.sub(r'\.delay\(', '(', content)
                content = re.sub(r'\.apply_async\(', '(', content)

                # Remove Redis imports
                content = re.sub(r'import redis.*\n', '', content)
                content = re.sub(r'from django_redis.*\n', '', content)

                full_path.write_text(content)
                self.log(f"Cleaned incompatible code from {file_path}")

    def create_conversion_report(self):
        """Create conversion report"""
        self.log("Creating conversion report...")

        report = {
            "conversion_date": "2024-01-01",
            "source_version": "VPS/Docker",
            "target_version": "cPanel",
            "changes": [
                "PostgreSQL → MySQL",
                "Redis → File-based cache",
                "Celery → Removed (synchronous processing)",
                "Docker → Native Python",
                "Gunicorn → Passenger WSGI",
                "Whitenoise → Native static file serving"
            ],
            "files_created": [
                "passenger_wsgi.py",
                "settings_cpanel.py",
                "requirements-cpanel.txt",
                ".env.cpanel.example",
                ".htaccess.example",
                "scripts/setup_cpanel.py",
                "README_CPANEL.md"
            ],
            "features_removed": [
                "Background task processing",
                "Advanced caching",
                "Container orchestration",
                "Advanced monitoring"
            ],
            "features_maintained": [
                "E-commerce functionality",
                "Payment processing",
                "Email notifications",
                "Admin interface",
                "User authentication"
            ]
        }

        report_file = self.output_dir / 'CONVERSION_REPORT.json'
        report_file.write_text(json.dumps(report, indent=2))

        # Also create human-readable report
        readable_report = f"""
# India Oasis - Conversion Report

## Conversion Summary
- **Source**: VPS/Docker Version
- **Target**: cPanel Compatible Version
- **Date**: 2024-01-01

## Major Changes
{chr(10).join(['- ' + change for change in report['changes']])}

## Files Created
{chr(10).join(['- ' + file for file in report['files_created']])}

## Features Removed
{chr(10).join(['- ' + feature for feature in report['features_removed']])}

## Features Maintained
{chr(10).join(['- ' + feature for feature in report['features_maintained']])}

## Next Steps
1. Review all created files
2. Update configuration as needed
3. Test the application locally
4. Deploy to cPanel hosting
5. Run setup script
6. Verify functionality

## Conversion Log
{chr(10).join(self.conversion_log)}
"""

        readable_file = self.output_dir / 'CONVERSION_REPORT.md'
        readable_file.write_text(readable_report)

        self.log("Created conversion report")

    def convert(self):
        """Run the complete conversion process"""
        self.log("Starting India Oasis cPanel conversion...")

        try:
            # Main conversion steps
            self.create_output_directory()
            self.copy_core_files()
            self.create_cpanel_settings()
            self.create_passenger_wsgi()
            self.create_requirements()
            self.create_env_example()
            self.create_htaccess()
            self.create_migration_script()
            self.create_deployment_guide()
            self.remove_incompatible_code()
            self.create_conversion_report()

            self.log("Conversion completed successfully!")
            self.log(f"cPanel-compatible version created in: {self.output_dir}")
            self.log("Next steps:")
            self.log
