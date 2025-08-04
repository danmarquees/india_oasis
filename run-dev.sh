#!/bin/bash
# Start India Oasis development server

echo "🚀 Starting India Oasis Development Server..."

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

# Check if database needs migrations
echo "🔍 Checking for pending migrations..."
python manage.py makemigrations --dry-run --verbosity=0 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    python manage.py makemigrations
    python manage.py migrate
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start development server
echo "🌐 Starting development server at http://localhost:8000"
echo "📊 Admin interface: http://localhost:8000/admin"
echo "❤️  Health check: http://localhost:8000/health"
echo ""
echo "👤 Admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the development server
python manage.py runserver 0.0.0.0:8000
