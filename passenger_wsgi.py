"""
WSGI config for india_oasis_project - cPanel Passenger compatible

This module contains the WSGI application used by Passenger on cPanel hosting.
It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
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
