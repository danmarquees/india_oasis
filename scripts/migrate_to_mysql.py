#!/usr/bin/env python
"""
Migration script to convert India Oasis project from PostgreSQL to MySQL
This script helps migrate the database schema and data for cPanel compatibility.
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
from django.conf import settings
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'mysql_migration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_mysql_connection():
    """Test MySQL database connection"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            logger.info(f"Connected to MySQL version: {version[0]}")
            return True
    except Exception as e:
        logger.error(f"MySQL connection failed: {e}")
        return False

def setup_mysql_database():
    """Configure MySQL database settings"""
    logger.info("Setting up MySQL database...")

    try:
        with connection.cursor() as cursor:
            # Set MySQL settings for better Django compatibility
            cursor.execute("SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
            cursor.execute("SET GLOBAL innodb_file_format = 'Barracuda'")
            cursor.execute("SET GLOBAL innodb_file_per_table = ON")
            cursor.execute("SET GLOBAL innodb_large_prefix = ON")

            logger.info("MySQL database configured successfully")
            return True

    except Exception as e:
        logger.warning(f"Could not set all MySQL configurations: {e}")
        logger.info("Continuing with default MySQL settings...")
        return True

def create_mysql_migrations():
    """Create fresh migrations for MySQL"""
    logger.info("Creating fresh migrations for MySQL...")

    apps_to_migrate = ['store', 'payment_processing', 'email_service']

    try:
        # Remove old migration files
        for app in apps_to_migrate:
            migrations_dir = project_root / app / 'migrations'
            if migrations_dir.exists():
                for file in migrations_dir.glob('*.py'):
                    if file.name != '__init__.py':
                        file.unlink()
                        logger.info(f"Removed old migration: {file}")

        # Create new migrations
        for app in apps_to_migrate:
            execute_from_command_line(['manage.py', 'makemigrations', app])
            logger.info(f"Created new migrations for {app}")

        return True

    except Exception as e:
        logger.error(f"Failed to create migrations: {e}")
        return False

def apply_migrations():
    """Apply migrations to MySQL database"""
    logger.info("Applying migrations to MySQL database...")

    try:
        # Apply Django's built-in migrations first
        execute_from_command_line(['manage.py', 'migrate', 'auth'])
        execute_from_command_line(['manage.py', 'migrate', 'contenttypes'])
        execute_from_command_line(['manage.py', 'migrate', 'sessions'])
        execute_from_command_line(['manage.py', 'migrate', 'admin'])
        execute_from_command_line(['manage.py', 'migrate', 'messages'])

        # Apply custom app migrations
        execute_from_command_line(['manage.py', 'migrate'])

        logger.info("All migrations applied successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to apply migrations: {e}")
        return False

def create_superuser():
    """Create a superuser for admin access"""
    logger.info("Creating superuser...")

    try:
        from django.contrib.auth.models import User

        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            logger.info("Superuser already exists")
            return True

        # Get superuser details from environment or prompt
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@yourdomain.com')
        password = os.environ.get('ADMIN_PASSWORD')

        if not password:
            logger.warning("No ADMIN_PASSWORD set in environment")
            logger.info("Please create superuser manually: python manage.py createsuperuser")
            return True

        User.objects.create_superuser(username, email, password)
        logger.info(f"Superuser '{username}' created successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to create superuser: {e}")
        return False

def optimize_mysql_tables():
    """Optimize MySQL tables for better performance"""
    logger.info("Optimizing MySQL tables...")

    try:
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                cursor.execute(f"OPTIMIZE TABLE `{table_name}`")
                logger.info(f"Optimized table: {table_name}")

        logger.info("MySQL tables optimized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to optimize tables: {e}")
        return False

def create_database_backup_script():
    """Create a simple backup script for MySQL"""
    backup_script = project_root / 'scripts' / 'backup_mysql.sh'

    script_content = """#!/bin/bash
# MySQL Backup Script for India Oasis cPanel

# Configuration
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
DB_PASSWORD="${DB_PASSWORD}"
DB_HOST="${DB_HOST:-localhost}"
BACKUP_DIR="$(dirname "$0")/../backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_backup_$DATE.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Database backup created successfully: $BACKUP_FILE"

    # Compress backup
    gzip "$BACKUP_FILE"
    echo "Backup compressed: ${BACKUP_FILE}.gz"

    # Keep only last 7 backups
    find "$BACKUP_DIR" -name "${DB_NAME}_backup_*.sql.gz" -mtime +7 -delete
    echo "Old backups cleaned up"
else
    echo "Database backup failed!"
    exit 1
fi
"""

    try:
        backup_script.parent.mkdir(exist_ok=True)
        backup_script.write_text(script_content)
        backup_script.chmod(0o755)
        logger.info(f"Backup script created: {backup_script}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup script: {e}")
        return False

def main():
    """Main migration process"""
    logger.info("Starting MySQL migration for India Oasis...")

    # Create necessary directories
    (project_root / 'logs').mkdir(exist_ok=True)
    (project_root / 'backups').mkdir(exist_ok=True)

    steps = [
        ("Checking MySQL connection", check_mysql_connection),
        ("Setting up MySQL database", setup_mysql_database),
        ("Creating MySQL migrations", create_mysql_migrations),
        ("Applying migrations", apply_migrations),
        ("Creating superuser", create_superuser),
        ("Optimizing MySQL tables", optimize_mysql_tables),
        ("Creating backup script", create_database_backup_script),
    ]

    failed_steps = []

    for step_name, step_function in steps:
        logger.info(f"Step: {step_name}")
        if not step_function():
            failed_steps.append(step_name)
            logger.error(f"Step failed: {step_name}")
        else:
            logger.info(f"Step completed: {step_name}")

    if failed_steps:
        logger.error(f"Migration completed with errors. Failed steps: {failed_steps}")
        return False
    else:
        logger.info("MySQL migration completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Update your .env file with MySQL database credentials")
        logger.info("2. Upload files to your cPanel hosting")
        logger.info("3. Set up Python application in cPanel")
        logger.info("4. Configure your domain to point to the application")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
