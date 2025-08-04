"""
Development URL configuration for india_oasis_project project.

This file contains simplified URLs for development environment
without health checks that require additional dependencies.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import JsonResponse
import time

def simple_health_check(request):
    """Simple health check for development"""
    return JsonResponse({
        'status': 'healthy',
        'environment': 'development',
        'timestamp': int(time.time())
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('payment/', include('payment_processing.urls')),
    # Simple health check for development
    path('health/', simple_health_check, name='health_check'),
]

# Serve static files during development
urlpatterns += staticfiles_urlpatterns()

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Add debug toolbar if available
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
