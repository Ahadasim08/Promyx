"""Step 3 grading: kept/broken/open decision accuracy, plus false-accusation
rate (said "broken" when the promise was actually kept), graded against
data/answer_key.csv.

Pairing logic (speaker + near-identical promise text) copied from
grade_linking.py so this grades independently of ticket-linking correctness.

Usage:
    python src/grade_checking.py
"""

import csv
import re
from pathlib import Path

from check import check_all

ROOT = Path(__file__).resolve().parent.parent
ANSWER_KEY = ROOT / "data" / "answer_key.csv"


def load_answer_key():
    with open(ANSWER_KEY, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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
    stored_rows = check_all()
    pairs = pair(gt_rows, stored_rows)

    correct = 0
    actually_kept = 0
    falsely_accused = 0
    print(f"{'promise_id':<12}{'speaker':<9}{'gt_decision':<12}{'got_decision':<13}{'correct':<9}")
    for gt, item in pairs:
        want = gt["ground_truth"]
        got = item["decision"]
        ok = want == got
        if ok:
            correct += 1
        if want == "kept":
            actually_kept += 1
            if got == "broken":
                falsely_accused += 1
        print(f"{gt['promise_id']:<12}{gt['speaker']:<9}{want:<12}{got:<13}{str(ok):<9}")

    total_gt = len(gt_rows)
    total_paired = len(pairs)
    print("-" * 60)
    print(f"Paired {total_paired}/{total_gt} answer-key promises to stored records.")
    if total_paired:
        print(f"Checking accuracy (kept/broken/open):     {correct}/{total_paired} = {correct / total_paired:.2f}")
    if actually_kept:
        print(f"False-accusation rate (kept called broken): {falsely_accused}/{actually_kept} = {falsely_accused / actually_kept:.2f}")
    else:
        print("False-accusation rate: n/a (no actually-kept promises)")


if __name__ == "__main__":
    grade()
