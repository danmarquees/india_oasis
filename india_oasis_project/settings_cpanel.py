"""
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
        'simple': {
            'format': '{levelname} {message}',
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
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django-error.log',
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
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Security settings for production
if not DEBUG:
    # SSL settings (adjust based on cPanel SSL configuration)
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
    SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
    CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)

    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'same-origin'

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', default=3600)  # 1 hour
SESSION_COOKIE_NAME = 'india_oasis_sessionid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF Protection
CSRF_COOKIE_NAME = 'india_oasis_csrftoken'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# File upload settings (conservative for shared hosting)
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
MAX_UPLOAD_SIZE = 5242880  # 5MB

# Cache Configuration (file-based cache for cPanel)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': BASE_DIR / 'cache',
        'TIMEOUT': 300,  # 5 minutes
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

# Rate limiting (disabled for cPanel to avoid issues)
RATELIMIT_ENABLE = False

# Admin interface customization (optional)
ADMIN_SITE_HEADER = 'India Oasis Admin'
ADMIN_SITE_TITLE = 'India Oasis Admin Portal'
ADMIN_INDEX_TITLE = 'Bem-vindo ao India Oasis Admin'

# Performance optimizations for shared hosting
DATABASE_ROUTERS = []
DATABASE_CONNECTION_POOLING = False

# Disable debug toolbar and development tools
INTERNAL_IPS = []

# Error reporting (simplified)
ADMINS = [
    ('Admin', env('ADMIN_EMAIL', default='admin@yourdomain.com')),
]
MANAGERS = ADMINS

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'cache', exist_ok=True)
