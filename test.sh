#!/bin/bash
# Run India Oasis Tests

echo "🧪 Running India Oasis Tests..."

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

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🔧 Environment: Development"
echo "📁 Test Database: In-memory SQLite"
echo ""

# Parse command line arguments
TEST_APP=""
VERBOSE=""
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="--verbosity=2"
            shift
            ;;
        -c|--coverage)
            COVERAGE="yes"
            shift
            ;;
        --app)
            TEST_APP="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -v, --verbose    Run tests with verbose output"
            echo "  -c, --coverage   Run tests with coverage report"
            echo "  --app APP_NAME   Run tests for specific app only"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Run tests with coverage if requested
if [ "$COVERAGE" = "yes" ]; then
    echo "📊 Running tests with coverage analysis..."

    # Check if coverage is installed
    if ! python -c "import coverage" 2>/dev/null; then
        echo "⚠️  Coverage package not installed. Installing..."
        pip install coverage
    fi

    # Run tests with coverage
    if [ -n "$TEST_APP" ]; then
        echo "🎯 Testing app: $TEST_APP"
        coverage run --source='.' manage.py test $TEST_APP $VERBOSE
    else
        echo "🎯 Testing all apps"
        coverage run --source='.' manage.py test $VERBOSE
    fi

    # Generate coverage report
    echo ""
    echo "📈 Coverage Report:"
    coverage report --skip-covered

    # Generate HTML coverage report
    coverage html
    echo "📄 HTML coverage report generated in htmlcov/index.html"

else
    # Run tests without coverage
    if [ -n "$TEST_APP" ]; then
        echo "🎯 Testing app: $TEST_APP"
        python manage.py test $TEST_APP $VERBOSE
    else
        echo "🎯 Testing all apps"
        python manage.py test $VERBOSE
    fi
fi

# Check test result
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed!"
    exit 1
fi

echo ""
echo "💡 Test Tips:"
echo "   ./test.sh --app store           # Test only store app"
echo "   ./test.sh --verbose             # Verbose output"
echo "   ./test.sh --coverage            # With coverage report"
echo "   ./test.sh --app store --verbose # Combine options"
