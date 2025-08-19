#!/bin/bash

# Script to run tests for the RAG Chatbot Backend
# Usage: ./run_tests.sh [options]

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VERBOSE=false
COVERAGE=false
COVERAGE_HTML=false
SPECIFIC_TEST=""
MARKERS=""
FAILED_FIRST=false
PARALLEL=false

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -v, --verbose           Run tests in verbose mode"
    echo "  -c, --coverage          Run with coverage report"
    echo "  -ch, --coverage-html    Generate HTML coverage report"
    echo "  -t, --test TEST         Run specific test file or test case"
    echo "  -m, --marker MARKER     Run tests with specific marker"
    echo "  -f, --failed-first      Run failed tests first"
    echo "  -p, --parallel          Run tests in parallel (requires pytest-xdist)"
    echo "  -q, --quick             Quick test run (no coverage, minimal output)"
    echo "  -a, --all               Run all tests with full coverage and reports"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run all tests"
    echo "  $0 -v                   # Run tests in verbose mode"
    echo "  $0 -c                   # Run with coverage report"
    echo "  $0 -t test_document_processor.py  # Run specific test file"
    echo "  $0 -t TestChunkText     # Run specific test class"
    echo "  $0 -a                   # Run all tests with full reports"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -ch|--coverage-html)
            COVERAGE=true
            COVERAGE_HTML=true
            shift
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -m|--marker)
            MARKERS="$2"
            shift 2
            ;;
        -f|--failed-first)
            FAILED_FIRST=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -q|--quick)
            VERBOSE=false
            COVERAGE=false
            shift
            ;;
        -a|--all)
            VERBOSE=true
            COVERAGE=true
            COVERAGE_HTML=true
            shift
            ;;
        *)
            print_color "$RED" "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_color "$YELLOW" "Warning: pyproject.toml not found. Are you in the project root?"
    print_color "$YELLOW" "Attempting to find project root..."
    
    # Try to find project root
    if [ -f "../pyproject.toml" ]; then
        cd ..
        print_color "$GREEN" "Found project root in parent directory"
    elif [ -f "../../pyproject.toml" ]; then
        cd ../..
        print_color "$GREEN" "Found project root two directories up"
    else
        print_color "$RED" "Error: Cannot find project root with pyproject.toml"
        exit 1
    fi
fi

# Ensure we're in the backend directory for running tests
if [ -d "backend" ]; then
    cd backend
elif [ ! -d "tests" ]; then
    print_color "$RED" "Error: Cannot find tests directory"
    exit 1
fi

print_color "$BLUE" "========================================="
print_color "$BLUE" "     Running RAG Chatbot Backend Tests  "
print_color "$BLUE" "========================================="
echo ""

# Build pytest command
PYTEST_CMD="uv run pytest"

# Add test path or specific test
if [ -n "$SPECIFIC_TEST" ]; then
    # Check if it's a file, class, or function
    if [[ "$SPECIFIC_TEST" == *".py" ]]; then
        PYTEST_CMD="$PYTEST_CMD tests/$SPECIFIC_TEST"
    elif [[ "$SPECIFIC_TEST" == *"::"* ]]; then
        PYTEST_CMD="$PYTEST_CMD tests/$SPECIFIC_TEST"
    else
        PYTEST_CMD="$PYTEST_CMD -k $SPECIFIC_TEST"
    fi
else
    PYTEST_CMD="$PYTEST_CMD tests/"
fi

# Add verbose flag
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage flags
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=term-missing"
    if [ "$COVERAGE_HTML" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html"
    fi
fi

# Add markers
if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m $MARKERS"
fi

# Add failed first flag
if [ "$FAILED_FIRST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --failed-first"
fi

# Add parallel flag
if [ "$PARALLEL" = true ]; then
    # Check if pytest-xdist is installed
    if uv run python -c "import pytest_xdist" 2>/dev/null; then
        PYTEST_CMD="$PYTEST_CMD -n auto"
    else
        print_color "$YELLOW" "Warning: pytest-xdist not installed. Installing..."
        uv add --dev pytest-xdist
        PYTEST_CMD="$PYTEST_CMD -n auto"
    fi
fi

# Show test statistics at the end
PYTEST_CMD="$PYTEST_CMD --tb=short"

# Display the command being run
print_color "$BLUE" "Running command: $PYTEST_CMD"
echo ""

# Run the tests
if $PYTEST_CMD; then
    echo ""
    print_color "$GREEN" "========================================="
    print_color "$GREEN" "         All tests passed! ✓            "
    print_color "$GREEN" "========================================="
    
    # Show coverage report location if HTML was generated
    if [ "$COVERAGE_HTML" = true ]; then
        echo ""
        print_color "$BLUE" "HTML coverage report generated at: htmlcov/index.html"
        print_color "$BLUE" "Open with: open htmlcov/index.html (Mac) or xdg-open htmlcov/index.html (Linux)"
    fi
else
    EXIT_CODE=$?
    echo ""
    print_color "$RED" "========================================="
    print_color "$RED" "         Some tests failed ✗            "
    print_color "$RED" "========================================="
    echo ""
    print_color "$YELLOW" "Tips for debugging:"
    print_color "$YELLOW" "  • Run with -v for verbose output"
    print_color "$YELLOW" "  • Run with -f to run failed tests first"
    print_color "$YELLOW" "  • Use -t to run specific failing test"
    exit $EXIT_CODE
fi