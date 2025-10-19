"""
GitHub Issues Deployment Script.

This module provides functionality to deploy GitHub issues in batch from JSON
files with support for milestone assignment and repository management.
"""

import json
import os
import sys

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv is optional, environment variables can be set directly
    pass
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO")

# Only validate environment variables if this module is run directly
# This allows for testing without requiring environment variables
if __name__ == "__main__" and (not GITHUB_TOKEN or not REPO):
    raise ValueError("Missing env vars: GITHUB_TOKEN, GITHUB_REPO")

REQUEST_TIMEOUT = 30  # seconds


def get_base_url():
    """Get the base URL for GitHub API calls."""
    repo = os.getenv("GITHUB_REPO") or "test/repo"
    return f"https://api.github.com/repos/{repo}"


def get_headers():
    """Get headers for GitHub API calls."""
    token = os.getenv("GITHUB_TOKEN") or "test-token"
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }


def fetch_milestones():
    """Fetch all milestones from the GitHub repository."""
    milestone_url = f"{get_base_url()}/milestones?state=all"
    response = requests.get(
        milestone_url, headers=get_headers(), timeout=REQUEST_TIMEOUT
    )
    if response.status_code != 200:
        print("Failed to fetch milestones:", response.json())
        sys.exit(1)
    return response.json()


def display_milestones(milestones):
    """
    Display available milestones to the user.

    Args:
        milestones (list): List of milestone dictionaries.
    """
    print("\nAvailable Milestones in this repo:")
    for milestone in milestones:
        print(
            f"[{milestone['number']}]: {milestone['title']} "
            f"(open issues: {milestone['open_issues']})"
        )


def load_issues_from_json(json_file_path):
    """
    Load issues from JSON file.

    Args:
        json_file_path (str): Path to the JSON file containing issues.

    Returns:
        tuple: (milestone_name, issues_list)
    """
    with open(json_file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    if isinstance(json_data, dict) and "milestone_name" in json_data:
        milestone_name = json_data["milestone_name"]
        issues = json_data["issues"]
    else:
        milestone_name = "<not specified in json>"
        issues = json_data

    return milestone_name, issues


def get_milestone_assignment():
    """
    Get milestone assignment from user input.

    Returns:
        int or None: Milestone ID if provided, None otherwise.
    """
    prompt = (
        "Enter milestone number to assign (see above list) " "or press Enter to skip: "
    )
    milestone_input = input(prompt)
    return int(milestone_input) if milestone_input.isdigit() else None


def confirm_deployment(milestone_id):
    """
    Get user confirmation for deployment.

    Args:
        milestone_id (int or None): Milestone ID to assign.

    Returns:
        bool: True if user confirms, False otherwise.
    """
    prompt = (
        f"Are you sure you want to assign ALL ISSUES to milestone "
        f"[{milestone_id}]? Type YES to continue: "
    )
    proceed = input(prompt)
    return proceed.strip().upper() == "YES"


def deploy_issues(issues, milestone_id):
    """
    Deploy issues to GitHub repository.

    Args:
        issues (list): List of issue dictionaries.
        milestone_id (int or None): Milestone ID to assign to issues.
    """
    api_url = f"{get_base_url()}/issues"
    for issue in issues:
        if milestone_id:
            issue["milestone"] = milestone_id
        response = requests.post(
            api_url, json=issue, headers=get_headers(), timeout=REQUEST_TIMEOUT
        )
        title = issue.get("title", "No title")
        status = response.status_code
        result = response.json()
        print(f"{title}: {status} | {result}")


def main():
    """Orchestrate the issue deployment process."""
    # Fetch and display milestones
    milestones = fetch_milestones()
    display_milestones(milestones)

    # Get batch info from JSON
    if len(sys.argv) < 2:
        print("Usage: python issue_deployer.py path/to/issues.json")
        sys.exit(1)

    json_input_file = sys.argv[1]
    milestone_name, issues = load_issues_from_json(json_input_file)

    # Display batch information
    print(f"\nJSON Batch file: {json_input_file}")
    print(f"Milestone for batch (as written in json): {milestone_name}")

    # Get milestone assignment
    milestone_id = get_milestone_assignment()

    # Confirm deployment
    if not confirm_deployment(milestone_id):
        sys.exit("Aborted by user.")

    # Deploy issues
    deploy_issues(issues, milestone_id)


if __name__ == "__main__":
    main()
