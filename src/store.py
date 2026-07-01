"""Step 2: store extracted promises in SQLite, with status (open/done/overdue)
computed from the linked Jira ticket's status + deadline.

Usage:
    python src/store.py
"""

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TICKETS_PATH = ROOT / "data" / "jira_tickets.json"
EXTRACTED_DIR = ROOT / "data" / "extracted"
DB_PATH = ROOT / "data" / "promises.db"

# Same evaluation date used in data/answer_key_notes.md, so status here
# lines up with the answer key's kept/broken/open judgments.
EVAL_DATE = "2026-07-01"

SCHEMA = """
CREATE TABLE IF NOT EXISTS promises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting TEXT NOT NULL,
    speaker TEXT NOT NULL,
    promise_text TEXT NOT NULL,
    ticket TEXT,
    deadline TEXT,
    ticket_status TEXT,
    status TEXT NOT NULL
);
"""


def load_tickets():
    data = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))
    return {t["key"]: t for t in data["tickets"]}


def norm(s):
    s = (s or "").strip().lower()
    return "" if s == "null" else s


def compute_status(ticket_status, deadline):
    if ticket_status is None:
        return "open"
    if ticket_status == "Done":
        return "done"
    if deadline and deadline < EVAL_DATE:
        return "overdue"
    return "open"


def load_all_extracted():
    records = []
    for path in sorted(EXTRACTED_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("promises", []):
            records.append((path.stem + ".txt", item))
    return records


def build_db():
    tickets = load_tickets()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS promises")
    conn.execute(SCHEMA)

    rows = []
    for meeting, item in load_all_extracted():
        ticket_key = norm(item.get("ticket")).upper() or None
        ticket = tickets.get(ticket_key)
        ticket_status = ticket["status"] if ticket else None
        deadline = norm(item.get("deadline")) or None
        status = compute_status(ticket_status, deadline)
        rows.append((
            meeting,
            item.get("speaker"),
            item.get("promise_text"),
            ticket_key,
            deadline,
            ticket_status,
            status,
        ))

    conn.executemany(
        "INSERT INTO promises (meeting, speaker, promise_text, ticket, deadline, ticket_status, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)


if __name__ == "__main__":
    n = build_db()
    print(f"Stored {n} promises -> {DB_PATH}")
