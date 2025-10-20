#!/bin/bash
# Quality checks runner for automotive DevOps platform
# This script runs all static analysis tools and unit tests on ALL Python files in the repository

set -e  # Exit on first error

echo "=================================================="
echo "  Automotive DevOps Platform - Quality Checks"
echo "    Analyzing ALL Python files in repository"
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

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found. Using system Python."
fi

# Define Python source directories to check
PYTHON_DIRS=(
    "projects/can_data_platform/scripts/"
    "projects/can_data_platform/src/"
    ".github/issue_deployment/"
    "tests/"
)

# Check if Python directories exist and have Python files
VALID_DIRS=()
echo "🔍 Discovering Python files..."
for dir in "${PYTHON_DIRS[@]}"; do
    if [ -d "$dir" ] && find "$dir" -name "*.py" -type f | grep -q .; then
        VALID_DIRS+=("$dir")
        py_count=$(find "$dir" -name "*.py" -type f | wc -l)
        echo "  📁 $dir ($py_count Python files)"
    fi
done

if [ ${#VALID_DIRS[@]} -eq 0 ]; then
    echo "${RED}❌ No Python files found in expected directories${NC}"
    exit 1
fi

echo ""
echo "📊 Running quality checks on: ${VALID_DIRS[*]}"
echo "🔧 Quality tools: Flake8, Pylint, Pydocstyle, Lizard, Bandit, Black, MyPy"
echo "🧪 Testing: Unit tests with coverage (≥80%)"
echo ""

# Run Flake8
run_check "Flake8 (PEP 8 Compliance)" \
    "flake8 ${VALID_DIRS[*]}"

# Run Pylint
run_check "Pylint (Code Quality)" \
    "pylint ${VALID_DIRS[*]}"

# Run Pydocstyle
run_check "Pydocstyle (Docstring Conventions)" \
    "pydocstyle ${VALID_DIRS[*]}"

# Run Lizard
run_check "Lizard (Complexity Analysis)" \
    "lizard ${VALID_DIRS[*]}"

# Run Bandit (Security Analysis)
run_check "Bandit (Security Scan)" \
    "bandit -r ${VALID_DIRS[*]} --skip B101,B311"

# Run Black (Code Formatting Check)
run_check "Black (Code Formatting)" \
    "black --check --diff ${VALID_DIRS[*]}"

# Run MyPy (Type Checking)
run_check "MyPy (Type Checking)" \
    "mypy ${VALID_DIRS[*]} --ignore-missing-imports"

# Run Unit Tests with Coverage
run_check "Unit Tests with Coverage" \
    "pytest tests/ --cov=projects/can_data_platform/scripts --cov=projects/can_data_platform/src --cov=.github/issue_deployment --cov-report=term-missing --cov-report=html --cov-report=xml --cov-report=json --cov-fail-under=80"

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
