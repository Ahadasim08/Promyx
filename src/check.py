"""Step 3: decide kept/broken/open for each stored promise from its linked
ticket's status + deadline, per the rules in CLAUDE.md:

    ticket Done                          -> kept
    ticket not done AND deadline passed  -> broken
    ticket not done AND deadline not yet -> open

Reuses store.py's `status` field (open/done/overdue), computed with the
same logic, and just relabels it to the kept/broken/open vocabulary.

Usage:
    python src/check.py
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "promises.db"

DECISION_MAP = {"done": "kept", "overdue": "broken", "open": "open"}


def load_promises():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM promises")]
    conn.close()
    return rows


def check_all():
    rows = load_promises()
    for row in rows:
        row["decision"] = DECISION_MAP[row["status"]]
    return rows


def load_agent_reviews():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute("SELECT * FROM agent_reviews")]
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return {r["promise_id"]: r for r in rows}


if __name__ == "__main__":
    rows = check_all()
    print(f"{'meeting':<14}{'speaker':<9}{'ticket':<9}{'ticket_status':<15}{'deadline':<12}{'decision':<9}")
    for r in rows:
        print(f"{r['meeting']:<14}{r['speaker']:<9}{str(r['ticket']):<9}{str(r['ticket_status']):<15}{str(r['deadline']):<12}{r['decision']:<9}")
    counts = {}
    for r in rows:
        counts[r["decision"]] = counts.get(r["decision"], 0) + 1
    print("-" * 68)
    print(f"Decisions: {counts}")

    reviews = load_agent_reviews()
    if reviews:
        print()
        print("Hard-case agent reviews (advisory only, does not change decisions above):")
        for r in rows:
            review = reviews.get(r["id"])
            if review:
                print(f"  promise {r['id']} ({r['speaker']}): rule-based={r['decision']} | agent suggests={review['suggested_verdict']}")
                print(f"    reasons flagged: {review['hard_case_reasons']}")
                print(f"    reasoning: {review['reasoning']}")
