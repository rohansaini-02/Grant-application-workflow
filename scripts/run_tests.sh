#!/bin/bash
# Run all tests with coverage

echo "Running Grant Application Workflow Tests..."
echo "=========================================="

# Run pytest with coverage
python -m pytest --cov=apps --cov-report=term-missing --cov-report=html

echo ""
echo "=========================================="
echo "Coverage report generated in htmlcov/index.html"
echo "=========================================="
