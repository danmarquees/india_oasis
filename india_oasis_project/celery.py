"""
Celery configuration for India Oasis project.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'india_oasis_project.settings')

app = Celery('india_oasis_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery Configuration Options
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,

    # Task execution settings
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_eager_result=True,

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,

    # Broker settings
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,

    # Task routing
    task_routes={
        'email_service.tasks.*': {'queue': 'email'},
        'payment_processing.tasks.*': {'queue': 'payments'},
        'store.tasks.*': {'queue': 'default'},
    },

    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-expired-sessions': {
            'task': 'store.tasks.cleanup_expired_sessions',
            'schedule': 3600.0,  # Every hour
        },
        'process-pending-orders': {
            'task': 'payment_processing.tasks.process_pending_orders',
            'schedule': 300.0,  # Every 5 minutes
        },
        'send-daily-reports': {
            'task': 'email_service.tasks.send_daily_reports',
            'schedule': 86400.0,  # Daily
        },
        'cleanup-old-logs': {
            'task': 'store.tasks.cleanup_old_logs',
            'schedule': 86400.0,  # Daily
        },
    },
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,

    # Task retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery signal handlers
from celery.signals import worker_ready, worker_shutting_down
import logging

logger = logging.getLogger(__name__)

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready signal."""
    logger.info('Celery worker is ready')

@worker_shutting_down.connect
def worker_shutting_down_handler(sender=None, **kwargs):
    """Handle worker shutdown signal."""
    logger.info('Celery worker is shutting down')

# Task failure handler
from celery.signals import task_failure

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Handle task failure."""
    logger.error(f'Task {task_id} failed: {exception}', exc_info=einfo)

# Debug task for testing
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return 'Debug task completed'
