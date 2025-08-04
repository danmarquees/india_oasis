#!/usr/bin/env python
"""
India Oasis - cPanel Setup Script
Final setup script for GoDaddy cPanel deployment

This script performs all necessary setup tasks after uploading files to cPanel:
1. Checks system requirements
2. Sets up the database
3. Runs migrations
4. Creates superuser
5. Collects static files
6. Sets proper permissions
7. Validates the installation

Usage:
    python setup_cpanel.py

Make sure to:
1. Configure your .env file first
2. Activate the virtual environment
3. Run this script from the project root directory
"""

import os
import sys
import django
from pathlib import Path
import subprocess
import logging
from datetime import datetime

class cPanelSetup:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
        self.setup_log = []
        self.success_count = 0
        self.total_steps = 8

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.project_root / 'logs'
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'setup.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_step(self, step_name, success=True, message=""):
        """Log setup step result"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        log_message = f"[{step_name}] {status}"
        if message:
            log_message += f" - {message}"

        self.logger.info(log_message)
        self.setup_log.append({
            'step': step_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now()
        })

        if success:
            self.success_count += 1

    def print_header(self):
        """Print setup header"""
        print("=" * 60)
        print("🛍️  INDIA OASIS - cPANEL SETUP SCRIPT")
        print("=" * 60)
        print("🔧 Setting up Django e-commerce for GoDaddy cPanel")
        print("📅 Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("-" * 60)

    def check_requirements(self):
        """Check system requirements"""
        self.logger.info("Step 1/8: Checking system requirements...")

        try:
            # Check Python version
            python_version = sys.version_info
            if python_version < (3, 7):
                raise Exception(f"Python 3.7+ required, found {python_version.major}.{python_version.minor}")

            # Check if we're in the right directory
            if not (self.project_root / 'manage.py').exists():
                raise Exception("manage.py not found - run this script from project root")

            # Check if .env file exists
            if not (self.project_root / '.env').exists():
                raise Exception(".env file not found - copy from .env.cpanel.example")

            # Check if virtual environment is activated
            if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                self.logger.warning("Virtual environment may not be activated")

            self.log_step("Requirements Check", True, f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            return True

        except Exception as e:
            self.log_step("Requirements Check", False, str(e))
            return False

    def setup_django(self):
        """Setup Django configuration"""
        self.logger.info("Step 2/8: Setting up Django configuration...")

        try:
            # Add project to Python path
            if str(self.project_root) not in sys.path:
                sys.path.insert(0, str(self.project_root))

            # Configure Django settings
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'india_oasis_project.settings')
            django.setup()

            # Import Django components
            from django.core.management import execute_from_command_line
            from django.db import connection
            from django.conf import settings

            self.execute_from_command_line = execute_from_command_line
            self.connection = connection
            self.settings = settings

            self.log_step("Django Setup", True, f"Using {settings.DATABASES['default']['ENGINE']}")
            return True

        except Exception as e:
            self.log_step("Django Setup", False, str(e))
            return False

    def check_database_connection(self):
        """Test database connection"""
        self.logger.info("Step 3/8: Testing database connection...")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()

            db_engine = self.settings.DATABASES['default']['ENGINE']
            db_name = self.settings.DATABASES['default']['NAME']

            self.log_step("Database Connection", True, f"Connected to {db_name} ({version[0] if version else 'Unknown version'})")
            return True

        except Exception as e:
            self.log_step("Database Connection", False, str(e))
            return False

    def run_migrations(self):
        """Run Django migrations"""
        self.logger.info("Step 4/8: Running database migrations...")

        try:
            # Run migrations
            self.execute_from_command_line(['manage.py', 'migrate', '--verbosity=1'])

            self.log_step("Database Migrations", True, "All migrations applied successfully")
            return True

        except Exception as e:
            self.log_step("Database Migrations", False, str(e))
            return False

    def create_superuser(self):
        """Create superuser if needed"""
        self.logger.info("Step 5/8: Setting up admin user...")

        try:
            from django.contrib.auth.models import User

            # Check if superuser already exists
            if User.objects.filter(is_superuser=True).exists():
                self.log_step("Admin User", True, "Superuser already exists")
                return True

            # Get admin credentials from environment
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@yourdomain.com')
            admin_password = os.environ.get('ADMIN_PASSWORD')

            if admin_password:
                User.objects.create_superuser(admin_username, admin_email, admin_password)
                self.log_step("Admin User", True, f"Superuser '{admin_username}' created")
            else:
                self.log_step("Admin User", True, "Run 'python manage.py createsuperuser' manually")

            return True

        except Exception as e:
            self.log_step("Admin User", False, str(e))
            return False

    def collect_static_files(self):
        """Collect static files"""
        self.logger.info("Step 6/8: Collecting static files...")

        try:
            self.execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--verbosity=1'])

            static_root = self.settings.STATIC_ROOT
            self.log_step("Static Files", True, f"Files collected to {static_root}")
            return True

        except Exception as e:
            self.log_step("Static Files", False, str(e))
            return False

    def set_permissions(self):
        """Set proper file permissions"""
        self.logger.info("Step 7/8: Setting file permissions...")

        try:
            # Create necessary directories
            directories = [
                self.project_root / 'logs',
                self.project_root / 'cache',
                self.project_root / 'public_html' / 'media',
                self.project_root / 'public_html' / 'static',
                self.project_root / 'backups'
            ]

            for directory in directories:
                directory.mkdir(exist_ok=True, parents=True)
                directory.chmod(0o755)

            # Set permissions for specific files
            wsgi_file = self.project_root / 'passenger_wsgi.py'
            if wsgi_file.exists():
                wsgi_file.chmod(0o644)

            manage_file = self.project_root / 'manage.py'
            if manage_file.exists():
                manage_file.chmod(0o755)

            self.log_step("File Permissions", True, "Permissions set successfully")
            return True

        except Exception as e:
            self.log_step("File Permissions", False, str(e))
            return False

    def validate_installation(self):
        """Validate the installation"""
        self.logger.info("Step 8/8: Validating installation...")

        try:
            # Run Django system checks
            self.execute_from_command_line(['manage.py', 'check', '--verbosity=1'])

            # Check critical files exist
            critical_files = [
                'passenger_wsgi.py',
                'manage.py',
                '.env',
                'requirements.txt'
            ]

            missing_files = []
            for file in critical_files:
                if not (self.project_root / file).exists():
                    missing_files.append(file)

            if missing_files:
                raise Exception(f"Missing critical files: {', '.join(missing_files)}")

            # Check if static files were collected
            static_root = Path(self.settings.STATIC_ROOT)
            if not static_root.exists() or not any(static_root.iterdir()):
                self.logger.warning("Static files directory is empty")

            self.log_step("Installation Validation", True, "All checks passed")
            return True

        except Exception as e:
            self.log_step("Installation Validation", False, str(e))
            return False

    def print_summary(self):
        """Print setup summary"""
        print("\n" + "=" * 60)
        print("📊 SETUP SUMMARY")
        print("=" * 60)

        for log_entry in self.setup_log:
            status = "✅" if log_entry['success'] else "❌"
            print(f"{status} {log_entry['step']}")
            if log_entry['message']:
                print(f"   └─ {log_entry['message']}")

        print("-" * 60)
        print(f"🎯 Success Rate: {self.success_count}/{self.total_steps} ({(self.success_count/self.total_steps)*100:.1f}%)")

        if self.success_count == self.total_steps:
            print("🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("\n📋 Next Steps:")
            print("1. Test your application in a web browser")
            print("2. Access admin panel at /admin/")
            print("3. Configure your domain settings in cPanel")
            print("4. Set up SSL certificate if needed")
            print("5. Configure email settings")
            print("\n📝 Important Files:")
            print(f"   • Logs: {self.project_root}/logs/")
            print(f"   • Static Files: {self.project_root}/public_html/static/")
            print(f"   • Media Files: {self.project_root}/public_html/media/")
            print(f"   • Passenger WSGI: {self.project_root}/passenger_wsgi.py")

        else:
            print("⚠️  SETUP COMPLETED WITH ISSUES!")
            print("\nCheck the logs above for details on failed steps.")
            print("You may need to fix these issues manually.")

        print("\n📞 Support:")
        print("   • Documentation: DEPLOY_CPANEL.md")
        print("   • Logs: logs/setup.log")
        print("   • Django Docs: https://docs.djangoproject.com/")
        print("=" * 60)

    def run_setup(self):
        """Run the complete setup process"""
        self.print_header()

        setup_steps = [
            self.check_requirements,
            self.setup_django,
            self.check_database_connection,
            self.run_migrations,
            self.create_superuser,
            self.collect_static_files,
            self.set_permissions,
            self.validate_installation
        ]

        for step in setup_steps:
            if not step():
                break

        self.print_summary()

        # Return success status
        return self.success_count == self.total_steps

def main():
    """Main entry point"""
    setup = cPanelSetup()
    success = setup.run_setup()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
