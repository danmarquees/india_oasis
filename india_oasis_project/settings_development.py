"""
Development settings for india_oasis_project.

This file contains development-specific configurations that override
the base settings for easier local development.
"""

from .settings import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Development database - use SQLite for simplicity
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable cache in development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Email backend for development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable security settings for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Development logging - simpler configuration
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
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/development.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'store': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'payment_processing': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'email_service': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Django Debug Toolbar (if installed)
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

        # Configure debug toolbar
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        }
        INTERNAL_IPS = [
            '127.0.0.1',
            'localhost',
        ]
    except ImportError:
        pass

# Remove health check apps for development
INSTALLED_APPS = [app for app in INSTALLED_APPS if not app.startswith('health_check')]

# Disable Celery for development (use synchronous execution)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# MercadoPago test credentials (use sandbox)
MERCADO_PAGO_PUBLIC_KEY = env('MERCADO_PAGO_PUBLIC_KEY', default='TEST-your-public-key')
MERCADO_PAGO_ACCESS_TOKEN = env('MERCADO_PAGO_ACCESS_TOKEN', default='TEST-your-access-token')

# Melhor Envio test token
MELHOR_ENVIO_TOKEN = env('MELHOR_ENVIO_TOKEN', default='test-token')
MELHOR_ENVIO_ENVIRONMENT = 'sandbox'

# Static files configuration for development
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Development-specific settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB for development
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB for development

# Session settings for development
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# CORS settings for development (if using frontend frameworks)
if 'corsheaders' in INSTALLED_APPS:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",  # React default
        "http://localhost:8000",  # Django dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    CORS_ALLOW_ALL_ORIGINS = True  # Only for development
    CORS_ALLOW_CREDENTIALS = True

# Disable some middleware for faster development
if DEBUG:
    # Remove cache middleware in development
    MIDDLEWARE = [m for m in MIDDLEWARE if 'cache' not in m.lower()]

# Development admin settings
ADMIN_URL = 'admin/'  # Keep simple for development

# Disable some security checks for development
SILENCED_SYSTEM_CHECKS = [
    'security.W004',  # SECURE_HSTS_SECONDS
    'security.W008',  # SECURE_SSL_REDIRECT
    'security.W012',  # SESSION_COOKIE_SECURE
    'security.W016',  # CSRF_COOKIE_SECURE
    'security.W019',  # X_FRAME_OPTIONS
]

# Email settings for development
ORDER_EMAIL_ENABLED = env.bool('ORDER_EMAIL_ENABLED', default=False)
ORDER_EMAIL_ADMIN = env('ORDER_EMAIL_ADMIN', default='admin@localhost')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@localhost')

# Performance settings for development
MAX_CART_ITEMS = env.int('MAX_CART_ITEMS', default=100)  # Higher limit for testing
ORDER_TIMEOUT_MINUTES = env.int('ORDER_TIMEOUT_MINUTES', default=60)  # Longer timeout for debugging

# Development tools
if DEBUG:
    # Add development apps if available
    DEV_APPS = []

    # Django Extensions (if installed)
    try:
        import django_extensions
        DEV_APPS.append('django_extensions')
    except ImportError:
        pass

    INSTALLED_APPS += DEV_APPS

# Override any production-specific settings
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Allow iframe for development

# Use development URLs
ROOT_URLCONF = 'india_oasis_project.urls_development'

print("🚀 Running in DEVELOPMENT mode")
print(f"📁 Database: {DATABASES['default']['NAME']}")
print(f"📧 Email backend: {EMAIL_BACKEND}")
print(f"🔧 Debug: {DEBUG}")
