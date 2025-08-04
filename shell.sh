#!/bin/bash
# Start India Oasis Django Shell

echo "🐚 Starting India Oasis Django Shell..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup-dev.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Set Django settings for development
export DJANGO_SETTINGS_MODULE=india_oasis_project.settings_development

echo "🔧 Environment: Development"
echo "📁 Database: SQLite (db.sqlite3)"
echo ""
echo "💡 Useful commands:"
echo "   from store.models import *"
echo "   from django.contrib.auth.models import User"
echo "   from payment_processing.models import *"
echo "   User.objects.all()"
echo ""

# Start Django shell
python manage.py shell
