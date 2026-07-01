"""Step 5: reasoning agent for hard-case promises (ambiguous ticket link,
missing deadline, or vague wording) that the rule-based pipeline in
store.py/check.py can't resolve cleanly. Additive only - never touches
the `promises` table.

Usage:
    python src/agent_review.py
"""

VAGUE_MARKERS = ["soon", "eventually", "at some point", "take care of", "get to it", "sometime"]


def is_hard_case(row: dict) -> list:
    reasons = []
    if not row.get("ticket"):
        reasons.append("no ticket linked")
    if not row.get("deadline"):
        reasons.append("no deadline")
    text = (row.get("promise_text") or "").lower()
    for marker in VAGUE_MARKERS:
        if marker in text:
            reasons.append(f"vague wording: '{marker}'")
    return reasons
