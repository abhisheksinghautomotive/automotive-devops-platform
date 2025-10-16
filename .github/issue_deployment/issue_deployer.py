from dotenv import load_dotenv
import os
import requests
import sys
import json

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO")

if not GITHUB_TOKEN or not REPO:
    raise ValueError("Missing env vars: GITHUB_TOKEN, GITHUB_REPO")
BASE_URL = f"https://api.github.com/repos/{REPO}"

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {GITHUB_TOKEN}"
}

# 1. Fetch and print all milestones
milestone_url = f"{BASE_URL}/milestones?state=all"
response = requests.get(milestone_url, headers=HEADERS)
if response.status_code != 200:
    print("Failed to fetch milestones:", response.json())
    sys.exit(1)
milestones = response.json()
print("\nAvailable Milestones in this repo:")
for ms in milestones:
    print(f"[{ms['number']}]: {ms['title']} (open issues: {ms['open_issues']})")

# 2. Get batch info from JSON
if len(sys.argv) < 2:
    print("Usage: python issue_deployer.py path/to/issues.json")
    sys.exit(1)
JSON_INPUT_FILE = sys.argv[1]
with open(JSON_INPUT_FILE, "r") as f:
    json_data = json.load(f)
if isinstance(json_data, dict) and "milestone_name" in json_data:
    milestone_name = json_data["milestone_name"]
    ISSUES = json_data["issues"]
else:
    milestone_name = "<not specified in json>"
    ISSUES = json_data

# 3. Prompt for milestone id by showing the list
print(f"\nJSON Batch file: {JSON_INPUT_FILE}")
print(f'Milestone for batch (as written in json): {milestone_name}')
milestone_input = input(
    "Enter milestone number to assign (see above list) or press Enter to skip: "
)
MILESTONE_ID = int(milestone_input) if milestone_input.isdigit() else None

proceed = input(
    f"Are you sure you want to assign ALL ISSUES to milestone [{MILESTONE_ID}]? Type YES to continue: "
)
if proceed.strip().upper() != "YES":
    sys.exit("Aborted by user.")

# 4. Upload issues
API_URL = f"{BASE_URL}/issues"
for issue in ISSUES:
    if MILESTONE_ID:
        issue["milestone"] = MILESTONE_ID
    response = requests.post(API_URL, json=issue, headers=HEADERS)
    print(f"{issue.get('title', 'No title')}: {response.status_code} | {response.json()}")
