#!/bin/bash
# Quality checks runner for automotive DevOps platform
# This script runs all static analysis tools and unit tests

set -e  # Exit on first error

echo "=================================================="
echo "  Automotive DevOps Platform - Quality Checks"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
FAILED=0

# Function to run check and track result
run_check() {
    echo ""
    echo "${YELLOW}=== $1 ===${NC}"
    if $2; then
        echo "${GREEN}✓ $1 passed${NC}"
    else
        echo "${RED}✗ $1 failed${NC}"
        FAILED=1
    fi
}

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Run Flake8
run_check "Flake8 (PEP 8 Compliance)" \
    "flake8 projects/can_data_platform/scripts/ tests/"

# Run Pylint
run_check "Pylint (Code Quality)" \
    "pylint projects/can_data_platform/scripts/ tests/"

# Run Pydocstyle
run_check "Pydocstyle (Docstring Conventions)" \
    "pydocstyle projects/can_data_platform/scripts/ tests/"

# Run Lizard
run_check "Lizard (Complexity Analysis)" \
    "lizard projects/can_data_platform/scripts/ tests/"

# Run Unit Tests with Coverage
run_check "Unit Tests with Coverage" \
    "pytest tests/unit/ --cov=projects/can_data_platform/scripts --cov-report=term-missing --cov-report=html --cov-fail-under=80"

echo ""
echo "=================================================="
if [ $FAILED -eq 0 ]; then
    echo "${GREEN}✅ All quality checks passed!${NC}"
    echo "=================================================="
    exit 0
else
    echo "${RED}❌ Some quality checks failed${NC}"
    echo "=================================================="
    exit 1
fi
