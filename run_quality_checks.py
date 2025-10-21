#!/usr/bin/env python3
"""
Automotive DevOps Platform - Quality Checks Script.

Unified quality checking tool for both local development and CI/CD.
Runs all code quality tools in a consistent manner.
"""

import subprocess  # nosec B404 - Required for running quality tools
import sys
import os
import logging


# Setup dual logging - both to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('quality_checks.log', mode='w'),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

QUALITY_TOOLS = [
    {"name": "Flake8 (PEP8)", "cmd": "flake8 {dirs}"},
    {"name": "Pylint", "cmd": "pylint {dirs}"},
    {"name": "Pydocstyle", "cmd": "pydocstyle {dirs}"},
    {"name": "Lizard (Complexity)", "cmd": "lizard {dirs}"},
    {"name": "Bandit (Security)", "cmd": "bandit -r {dirs} --skip B101,B311"},
    {"name": "Black (Format)", "cmd": "black --check --diff {dirs}"},
    {"name": "MyPy (Typechecking)", "cmd": "mypy {dirs} --ignore-missing-imports"},
    {
        "name": "Unit Tests/Coverage",
        "cmd": (
            "pytest tests/ --cov=projects/can_data_platform/scripts "
            "--cov=projects/can_data_platform/src --cov=.github/issue_deployment "
            "--cov-report=term-missing --cov-report=html --cov-report=xml "
            "--cov-report=json --cov-fail-under=95"
        ),
    },
    {"name": "Yamllint (Workflows)", "cmd": "yamllint .github/workflows/*.yml"},
    {
        "name": "Secret Scan (Workflows)",
        "cmd": (
            "grep -Ei '(secret|token|password|KEY=)' " ".github/workflows/*.yml || true"
        ),
    },
]

PYTHON_DIRS = [
    "projects/can_data_platform/scripts/",
    "projects/can_data_platform/src/",
    ".github/issue_deployment/",
    "tests/",
]


def find_valid_dirs(dirs):
    """Find directories containing Python files.

    Args:
        dirs: List of directory paths to check.

    Returns:
        List of valid directories containing Python files.
    """
    valid = []
    for d in dirs:
        if os.path.isdir(d):
            py_files = [f for f in os.listdir(d) if f.endswith('.py')]
            if py_files or any(
                os.path.isfile(os.path.join(root, f)) and f.endswith('.py')
                for root, _, files in os.walk(d)
                for f in files
            ):
                valid.append(d)
    return valid


def run_quality_check(name, cmd):
    """Run a single quality check command.

    Args:
        name: Human-readable name of the quality check.
        cmd: Shell command to execute.

    Returns:
        Tuple of (success_bool, stdout, stderr).
    """
    logging.info("\n=== %s ===\nCommand: %s", name, cmd)
    try:
        result = subprocess.run(  # nosec B602 - Controlled input from quality tools
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        logging.info("✓ %s passed\n%s", name, result.stdout)
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        logging.error("✗ %s failed\n%s\n%s", name, e.stdout, e.stderr)
        return False, e.stdout, e.stderr


def main():
    """Execute all quality checks for the automotive devops platform."""
    logging.info("=" * 50)
    logging.info(" Automotive DevOps Platform - Quality Checks (Python)")
    logging.info(" Running ALL repo checks locally or in CI/CD")
    logging.info("=" * 50)
    venv_dir = (
        '.venv' if os.path.isdir('.venv') else 'venv' if os.path.isdir('venv') else None
    )
    if venv_dir:
        activate = os.path.join(venv_dir, 'bin', 'activate_this.py')
        if os.path.exists(activate):
            import runpy

            runpy.run_path(activate, run_name="__main__")
        logging.info("Activated virtual environment: %s", venv_dir)
    valid_dirs = find_valid_dirs(PYTHON_DIRS)
    if not valid_dirs:
        logging.error("No Python files found in expected directories.")
        sys.exit(1)
    logging.info("Quality checks will be run on directories:")
    for d in valid_dirs:
        logging.info(" - %s", d)
    all_failures = []
    for tool in QUALITY_TOOLS:
        cmd = tool["cmd"].format(dirs=" ".join(valid_dirs))
        passed, out, err = run_quality_check(tool["name"], cmd)
        if not passed:
            all_failures.append((tool["name"], out, err))
    logging.info("\n%s", "=" * 50)
    if not all_failures:
        logging.info("✓ All quality checks passed!\n%s", "=" * 50)
        sys.exit(0)
    else:
        logging.error("✗ Some quality checks failed:\n%s", "=" * 50)
        for name, out, err in all_failures:
            logging.error(
                "\n----- %s Failure Report -----\n%s\n%s\n------------------------",
                name,
                out,
                err,
            )
        logging.error("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
