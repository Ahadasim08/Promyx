"""Step 5 grading: how many answer-key promises were flagged as hard cases,
and of those, how accurate the agent's suggested_verdict is vs ground truth.
Reported as a 4th metric, separate from grade.py/grade_linking.py/grade_checking.py.

Pairing logic (speaker + near-identical promise text) copied from
grade_checking.py so this grades independently.

Usage:
    python src/grade_agent.py
"""

import csv
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANSWER_KEY = ROOT / "data" / "answer_key.csv"
DB_PATH = ROOT / "data" / "promises.db"


def load_answer_key():
    with open(ANSWER_KEY, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_stored_with_reviews():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    promises = [dict(r) for r in conn.execute("SELECT * FROM promises")]
    reviews = {}
    try:
        for r in conn.execute("SELECT * FROM agent_reviews"):
            reviews[r["promise_id"]] = dict(r)
    except sqlite3.OperationalError as e:
        if "no such table" not in str(e):
            raise
    conn.close()
    for p in promises:
        p["agent_review"] = reviews.get(p["id"])
    return promises


def norm_text(s):
    s = (s or "").strip().lower()
    s = re.sub(r"[.,!?]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def norm(s):
    s = (s or "").strip().lower()
    return "" if s == "null" else s


def pair(gt_rows, stored_rows):
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
    stored_rows = load_stored_with_reviews()
    pairs = pair(gt_rows, stored_rows)

    hard_paired = [(gt, item) for gt, item in pairs if item["agent_review"]]
    correct = 0
    print(f"{'promise_id':<12}{'speaker':<9}{'hard_reasons':<40}{'gt_decision':<12}{'agent_verdict':<14}{'correct':<9}")
    for gt, item in hard_paired:
        review = item["agent_review"]
        want = gt["ground_truth"]
        got = review["suggested_verdict"]
        ok = want == got
        if ok:
            correct += 1
        print(f"{gt['promise_id']:<12}{gt['speaker']:<9}{review['hard_case_reasons']:<40}{want:<12}{got:<14}{str(ok):<9}")

    total_gt = len(gt_rows)
    total_paired = len(pairs)
    total_hard = len(hard_paired)
    print("-" * 100)
    print(f"Paired {total_paired}/{total_gt} answer-key promises to stored records.")
    print(f"Hard cases flagged (of paired): {total_hard}/{total_paired}")
    if total_hard:
        print(f"Agent suggested_verdict accuracy on hard cases: {correct}/{total_hard} = {correct / total_hard:.2f}")
    else:
        print("Agent suggested_verdict accuracy on hard cases: n/a (no hard cases flagged)")


if __name__ == "__main__":
    grade()
