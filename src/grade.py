"""Step 1 grading: compare extracted promises against data/answer_key.csv.

Usage:
    python src/grade.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANSWER_KEY = ROOT / "data" / "answer_key.csv"
EXTRACTED_DIR = ROOT / "data" / "extracted"


def load_answer_key():
    rows = []
    with open(ANSWER_KEY, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def load_extracted(transcript_file: str):
    path = EXTRACTED_DIR / (Path(transcript_file).stem + ".json")
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("promises", [])


def norm(s):
    s = (s or "").strip().lower()
    return "" if s == "null" else s


def grade():
    key_rows = load_answer_key()
    by_file = {}
    for row in key_rows:
        by_file.setdefault(row["transcript_file"], []).append(row)

    total_gt = 0
    total_matched_gt = 0
    total_extracted = 0
    total_matched_extracted = 0

    print(f"{'file':<16}{'gt':>4}{'extracted':>11}{'matched':>9}{'recall':>9}{'precision':>11}")

    for transcript_file, gt_rows in sorted(by_file.items()):
        extracted = load_extracted(transcript_file)
        unmatched_gt = list(gt_rows)
        matched_extracted = 0

        for item in extracted:
            hit = None
            for gt in unmatched_gt:
                if norm(gt["speaker"]) == norm(item.get("speaker")) and norm(gt["ticket"]) == norm(item.get("ticket")):
                    hit = gt
                    break
            if hit:
                unmatched_gt.remove(hit)
                matched_extracted += 1

        matched_gt = len(gt_rows) - len(unmatched_gt)
        recall = matched_gt / len(gt_rows) if gt_rows else 0
        precision = matched_extracted / len(extracted) if extracted else 0

        print(f"{transcript_file:<16}{len(gt_rows):>4}{len(extracted):>11}{matched_gt:>9}{recall:>9.2f}{precision:>11.2f}")

        total_gt += len(gt_rows)
        total_matched_gt += matched_gt
        total_extracted += len(extracted)
        total_matched_extracted += matched_extracted

    overall_recall = total_matched_gt / total_gt if total_gt else 0
    overall_precision = total_matched_extracted / total_extracted if total_extracted else 0

    print("-" * 60)
    print(f"OVERALL  recall={overall_recall:.2f} ({total_matched_gt}/{total_gt})   precision={overall_precision:.2f} ({total_matched_extracted}/{total_extracted})")


if __name__ == "__main__":
    grade()
