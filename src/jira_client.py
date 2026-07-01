"""Real Jira REST API client. Replaces the data/jira_tickets.json fixture as
the source of ticket status for store.py.

Auth + site config come from .env: JIRA_SITE_URL, JIRA_EMAIL,
JIRA_API_TOKEN, JIRA_PROJECT_KEY.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SITE = os.environ["JIRA_SITE_URL"].rstrip("/")
AUTH = (os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"])
PROJECT_KEY = os.environ["JIRA_PROJECT_KEY"]


def fetch_live_tickets():
    """Returns {summary_lower: {"key": ..., "status": ..., "assignee": ...}}
    for every issue in the configured Jira project.
    """
    tickets = {}
    next_token = None
    while True:
        params = {
            "jql": f"project = {PROJECT_KEY}",
            "fields": "summary,status,assignee",
            "maxResults": 100,
        }
        if next_token:
            params["nextPageToken"] = next_token
        r = requests.get(f"{SITE}/rest/api/3/search/jql", auth=AUTH, params=params)
        r.raise_for_status()
        data = r.json()
        for issue in data["issues"]:
            fields = issue["fields"]
            assignee = fields.get("assignee")
            tickets[fields["summary"].strip().lower()] = {
                "key": issue["key"],
                "status": fields["status"]["name"],
                "assignee": assignee["displayName"] if assignee else None,
            }
        next_token = data.get("nextPageToken")
        if not next_token:
            break
    return tickets
