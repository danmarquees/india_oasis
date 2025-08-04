# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.

# Import Celery only if it's available (for production)
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not available, skip import (development mode)
    __all__ = ()
