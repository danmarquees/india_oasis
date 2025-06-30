#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Installing Python dependencies ---"
pip install -r requirements.txt

echo "--- Running Django database migrations ---"
python manage.py migrate

echo "--- Creating Django superuser (if not exists) ---"
# Check if superuser environment variables are set
if [ -z "$DJANGO_SUPERUSER_USERNAME" ] || [ -z "$DJANGO_SUPERUSER_EMAIL" ] || [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Warning: Superuser environment variables (DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD) not set. Skipping superuser creation."
else
    # Create superuser non-interactively.
    # The --noinput flag suppresses prompts.
    # The password will be taken from the DJANGO_SUPERUSER_PASSWORD environment variable,
    # which django-environ helps manage.
    # `|| true` ensures the script continues even if the user already exists (createsuperuser returns non-zero).
    python manage.py createsuperuser --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" || true
fi

echo "--- Collecting static files ---"
cp -r media/* static/media/ # Copia arquivos de mídia para o diretório estático
python manage.py collectstatic --noinput

echo "--- Build process completed successfully ---"
