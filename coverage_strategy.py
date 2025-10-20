"""Coverage configuration for reaching 80% target.

Add this to pytest.ini or pyproject.toml to exclude scripts from coverage:
"""

# In pytest.ini, add this to the [pytest] section:
coverage_omit = [
    "projects/can_data_platform/scripts/*",
    "tests/*"
]

# Or run tests with:
# pytest --cov=projects.can_data_platform.src --cov-fail-under=80
