"""One-off: create real Jira issues matching data/jira_tickets.json's 18 mock
tickets (same summaries + statuses), so store.py can be pointed at the real
Jira API instead of the fixture. Run once per fresh Jira project.

Usage:
    python src/seed_jira.py
"""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SITE = os.environ["JIRA_SITE_URL"].rstrip("/")
AUTH = (os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"])
PROJECT_KEY = os.environ["JIRA_PROJECT_KEY"]
TASK_ISSUE_TYPE_ID = "10007"

TICKETS_PATH = ROOT / "data" / "jira_tickets.json"


def create_issue(summary):
    body = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "issuetype": {"id": TASK_ISSUE_TYPE_ID},
        }
    }
    r = requests.post(f"{SITE}/rest/api/3/issue", auth=AUTH, json=body)
    r.raise_for_status()
    return r.json()["key"]


def get_transitions(issue_key):
    r = requests.get(f"{SITE}/rest/api/3/issue/{issue_key}/transitions", auth=AUTH)
    r.raise_for_status()
    return {t["name"]: t["id"] for t in r.json()["transitions"]}


def transition_issue(issue_key, target_status):
    transitions = get_transitions(issue_key)
    transition_id = transitions.get(target_status)
    if not transition_id:
        print(f"  ! no transition to '{target_status}' for {issue_key}, skipping (still To Do)")
        return
    r = requests.post(
        f"{SITE}/rest/api/3/issue/{issue_key}/transitions",
        auth=AUTH,
        json={"transition": {"id": transition_id}},
    )
    r.raise_for_status()


def main():
    data = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))
    for t in data["tickets"]:
        key = create_issue(t["summary"])
        print(f"created {key}  <-  {t['key']}  {t['summary']!r}")
        if t["status"] != "To Do":
            transition_issue(key, t["status"])
            print(f"  -> transitioned to {t['status']}")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
