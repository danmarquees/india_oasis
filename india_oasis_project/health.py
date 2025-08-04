"""
Health check views for monitoring application status.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import time

logger = logging.getLogger(__name__)


@require_GET
@never_cache
def health_check(request):
    """
    Basic health check endpoint that returns application status.
    """
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': int(time.time()),
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'environment': 'production' if not settings.DEBUG else 'development',
            'checks': {}
        }

        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health_data['checks']['database'] = {'status': 'healthy'}
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['status'] = 'unhealthy'

        # Cache check (Redis)
        try:
            cache.set('health_check', 'ok', 30)
            if cache.get('health_check') == 'ok':
                health_data['checks']['cache'] = {'status': 'healthy'}
            else:
                health_data['checks']['cache'] = {
                    'status': 'unhealthy',
                    'error': 'Cache write/read failed'
                }
                health_data['status'] = 'degraded'
        except Exception as e:
            health_data['checks']['cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['status'] = 'degraded'

        # Disk space check
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            disk_usage = (used / total) * 100

            if disk_usage > 90:
                health_data['checks']['disk'] = {
                    'status': 'unhealthy',
                    'usage_percent': round(disk_usage, 2),
                    'message': 'Disk usage is critical'
                }
                health_data['status'] = 'unhealthy'
            elif disk_usage > 80:
                health_data['checks']['disk'] = {
                    'status': 'warning',
                    'usage_percent': round(disk_usage, 2),
                    'message': 'Disk usage is high'
                }
                if health_data['status'] == 'healthy':
                    health_data['status'] = 'degraded'
            else:
                health_data['checks']['disk'] = {
                    'status': 'healthy',
                    'usage_percent': round(disk_usage, 2)
                }
        except Exception as e:
            health_data['checks']['disk'] = {
                'status': 'unknown',
                'error': str(e)
            }

        # Memory check
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            if memory_usage > 90:
                health_data['checks']['memory'] = {
                    'status': 'unhealthy',
                    'usage_percent': memory_usage,
                    'message': 'Memory usage is critical'
                }
                health_data['status'] = 'unhealthy'
            elif memory_usage > 80:
                health_data['checks']['memory'] = {
                    'status': 'warning',
                    'usage_percent': memory_usage,
                    'message': 'Memory usage is high'
                }
                if health_data['status'] == 'healthy':
                    health_data['status'] = 'degraded'
            else:
                health_data['checks']['memory'] = {
                    'status': 'healthy',
                    'usage_percent': memory_usage
                }
        except ImportError:
            health_data['checks']['memory'] = {
                'status': 'unknown',
                'message': 'psutil not available'
            }
        except Exception as e:
            health_data['checks']['memory'] = {
                'status': 'unknown',
                'error': str(e)
            }

        # Return appropriate status code
        if health_data['status'] == 'healthy':
            status_code = 200
        elif health_data['status'] == 'degraded':
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable

        return JsonResponse(health_data, status=status_code)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': int(time.time())
        }, status=503)


@require_GET
@never_cache
def readiness_check(request):
    """
    Readiness check to determine if the application is ready to serve traffic.
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Check if migrations are up to date
        from django.core.management import execute_from_command_line
        from django.core.management.base import BaseCommand
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        if plan:
            return JsonResponse({
                'status': 'not_ready',
                'message': 'Pending migrations detected',
                'timestamp': int(time.time())
            }, status=503)

        return JsonResponse({
            'status': 'ready',
            'timestamp': int(time.time())
        }, status=200)

    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': int(time.time())
        }, status=503)


@require_GET
@never_cache
def liveness_check(request):
    """
    Liveness check to determine if the application is alive.
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': int(time.time())
    }, status=200)
