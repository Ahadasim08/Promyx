"""Step 2 grading: linking accuracy (promise -> correct Jira ticket) and
status accuracy (open/done/overdue vs. the answer key's kept/broken/open),
graded against data/answer_key.csv and data/promises.db.

Usage:
    python src/grade_linking.py
"""

import csv
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANSWER_KEY = ROOT / "data" / "answer_key.csv"
DB_PATH = ROOT / "data" / "promises.db"

STATUS_MAP = {"kept": "done", "broken": "overdue", "open": "open"}


def load_answer_key():
    with open(ANSWER_KEY, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_stored():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM promises")]
    conn.close()
    return rows


def norm_text(s):
    s = (s or "").strip().lower()
    s = re.sub(r"[.,!?]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def norm(s):
    s = (s or "").strip().lower()
    return "" if s == "null" else s


def pair(gt_rows, stored_rows):
    """Match each answer-key promise to a stored promise by speaker + near-identical
    promise text (independent of ticket, so ticket correctness can be graded on its own)."""
    unmatched = list(stored_rows)
    pairs = []
    for gt in gt_rows:
        hit = None
        for item in unmatched:
            if norm(gt["speaker"]) == norm(item["speaker"]) and norm_text(gt["promise_text"]) == norm_text(item["promise_text"]):
                hit = item
                break
        if hit:
            unmatched.remove(hit)
            pairs.append((gt, hit))
    return pairs


def grade():
    gt_rows = load_answer_key()
    stored_rows = load_stored()
    pairs = pair(gt_rows, stored_rows)

    linked_correct = 0
    status_correct = 0
    print(f"{'promise_id':<12}{'speaker':<9}{'gt_ticket':<11}{'got_ticket':<12}{'link_ok':<9}{'gt_status':<11}{'got_status':<11}{'status_ok':<9}")
    for gt, item in pairs:
        link_ok = norm(gt["ticket"]) == norm(item["ticket"])
        want_status = STATUS_MAP[gt["ground_truth"]]
        status_ok = want_status == item["status"]
        if link_ok:
            linked_correct += 1
        if status_ok:
            status_correct += 1
        print(f"{gt['promise_id']:<12}{gt['speaker']:<9}{gt['ticket']:<11}{str(item['ticket']):<12}{str(link_ok):<9}{want_status:<11}{item['status']:<11}{str(status_ok):<9}")

    total_gt = len(gt_rows)
    total_paired = len(pairs)
    print("-" * 80)
    print(f"Paired {total_paired}/{total_gt} answer-key promises to stored records "
          f"(unpaired means Step 1 extraction missed or mis-quoted them; see grade.py).")
    print(f"Linking accuracy (correct ticket, of paired):        "
          f"{linked_correct}/{total_paired} = {linked_correct / total_paired:.2f}" if total_paired else "n/a")
    print(f"Status accuracy (open/done/overdue, of paired):      "
          f"{status_correct}/{total_paired} = {status_correct / total_paired:.2f}" if total_paired else "n/a")


if __name__ == "__main__":
    grade()
