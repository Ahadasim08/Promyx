"""Step 5: reasoning agent for hard-case promises (ambiguous ticket link,
missing deadline, or vague wording) that the rule-based pipeline in
store.py/check.py can't resolve cleanly. Additive only - never touches
the `promises` table.

Usage:
    python src/agent_review.py
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Add src to path to allow relative imports within this module
_src_path = Path(__file__).resolve().parent
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from store import DB_PATH, EVAL_DATE, load_tickets

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"

VAGUE_MARKERS = ["soon", "eventually", "at some point", "take care of", "get to it", "sometime"]

MODEL = "llama-3.3-70b-versatile"

AGENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    promise_id INTEGER NOT NULL,
    hard_case_reasons TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    suggested_ticket TEXT,
    suggested_deadline TEXT,
    suggested_verdict TEXT NOT NULL
);
"""

SYSTEM_PROMPT = """You are a careful reviewer investigating a promise made in a meeting that a rule-based system could not confidently process (missing deadline, missing ticket link, or vague wording).

You are given: the promise, the speaker, the full meeting transcript for context, the full list of known Jira tickets (key, summary, status), and the ticket/deadline the rule-based system currently has linked (if any).

Investigate:
1. Is the currently-linked ticket correct? Check every ticket in the list for a better topical match. If the current link is right, keep it.
2. Based on the transcript context, is there a deadline the speaker implied even if not an exact date (e.g. relative time, a date mentioned elsewhere in the conversation)? If genuinely no clue exists, leave it null.
3. Given the ticket's status and your inferred deadline versus the evaluation date, what is your verdict: "kept" (ticket done), "broken" (not done and deadline has passed), or "open" (not done, deadline not yet passed or no reliable deadline exists)?

Explain your reasoning in plain language a human reviewer can follow and judge - state what you checked and why you landed on your answer, not just the answer.

Respond with ONLY a JSON object of this exact shape, no prose, no markdown fences:
{
  "reasoning": "plain-language explanation of what you checked and why",
  "suggested_ticket": "PROM-4" or null,
  "suggested_deadline": "YYYY-MM-DD" or null,
  "suggested_verdict": "kept" or "broken" or "open"
}
"""


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


def build_agent_table(conn):
    conn.execute("DROP TABLE IF EXISTS agent_reviews")
    conn.execute(AGENT_SCHEMA)


def build_user_prompt(row: dict, transcript_text: str, tickets: dict) -> str:
    ticket_lines = "\n".join(
        f"- {key}: {t['summary']} (status: {t['status']})" for key, t in tickets.items()
    )
    return f"""Evaluation date: {EVAL_DATE}

Promise:
  speaker: {row['speaker']}
  text: {row['promise_text']}
  currently linked ticket: {row['ticket'] or 'none'}
  currently linked ticket status: {row['ticket_status'] or 'unknown'}
  currently parsed deadline: {row['deadline'] or 'none'}

Known Jira tickets:
{ticket_lines}

Full meeting transcript ({row['meeting']}):
{transcript_text}
"""


def investigate(client: Groq, row: dict, transcript_text: str, tickets: dict) -> dict:
    user_prompt = build_user_prompt(row, transcript_text, tickets)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print(f"WARNING: agent returned invalid JSON for promise {row['id']}", file=sys.stderr)
        print(content, file=sys.stderr)
        return {
            "reasoning": "Agent returned invalid JSON; no reasoning available.",
            "suggested_ticket": row.get("ticket"),
            "suggested_deadline": row.get("deadline"),
            "suggested_verdict": "open",
        }
