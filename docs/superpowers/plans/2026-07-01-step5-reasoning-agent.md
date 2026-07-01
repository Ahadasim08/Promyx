# Step 5 Reasoning Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone Step 5 script that flags rule-based-pipeline "hard case" promises (missing ticket, missing deadline, or vague wording), investigates each with an LLM using full transcript + ticket context, and writes plain-language reasoning + a suggested verdict to a new `agent_reviews` table — without touching Steps 1-4.

**Architecture:** `src/agent_review.py` reads the already-built `data/promises.db` (via `store.py`'s `DB_PATH`, `EVAL_DATE`, `load_tickets`), flags hard cases with a pure-Python heuristic, and for each one calls Groq (same client pattern as `extract.py`) with the promise, the full original transcript, and the full Jira ticket list. Results land in a new `agent_reviews` table that `agent_review.py` owns exclusively (drop+recreate each run, like `store.py` does for `promises`). `check.py` gets an additive, print-only section that joins in agent reviews for hard cases without changing its returned `decision` values. `src/grade_agent.py` reports the 4th metric: hard-case count and suggested-verdict accuracy vs `data/answer_key.csv`.

**Tech Stack:** Python, `groq` SDK (Chat Completions, JSON mode), `sqlite3` (stdlib), existing `src/store.py` / `src/jira_client.py` helpers.

## Global Constraints

- Never modify `src/extract.py`, `src/store.py`'s `promises` table logic, `src/check.py`'s `check_all()` return value, `data/answer_key.csv`, `backend/`, or `frontend/`.
- Grade all new decisions against `data/answer_key.csv` (CLAUDE.md hard rule #1).
- Report the 4th metric (hard-case count + accuracy) separately from the existing 3 metrics — don't overwrite or fold them together.
- `EVAL_DATE = "2026-07-01"` (from `store.py`) is the evaluation date to reason about, matching the answer key.
- Model: `llama-3.3-70b-versatile` via Groq, `temperature=0`, `response_format={"type": "json_object"}` — same pattern as `extract.py`.
- Requires `GROQ_API_KEY` in `.env` (already present per CLAUDE.md).

---

### Task 1: Hard-case detection heuristic

**Files:**
- Create: `src/agent_review.py` (heuristic portion only this task)

**Interfaces:**
- Produces: `is_hard_case(row: dict) -> list[str]` — takes a dict with keys `ticket`, `deadline`, `promise_text` (matching a row from the `promises` table) and returns a list of human-readable reasons (empty list means not a hard case). Later tasks call this directly.

- [ ] **Step 1: Write `src/agent_review.py` with the heuristic**

```python
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
```

- [ ] **Step 2: Smoke-test against the known P10 case and a clean case**

Run:
```bash
python -c "
from src.agent_review import is_hard_case
p10 = {'ticket': 'PROM-4', 'deadline': None, 'promise_text': \"I'll take care of that thing with the checkout tests soon\"}
clean = {'ticket': 'PROM-1', 'deadline': '2026-06-05', 'promise_text': \"I'll close the login bug ticket by Friday, June 5.\"}
print('P10:', is_hard_case(p10))
print('clean:', is_hard_case(clean))
"
```

Expected output:
```
P10: ['no deadline', "vague wording: 'soon'", "vague wording: 'take care of'"]
clean: []
```

(Note: run this from the project root so `src` resolves as a package, or `cd src && python -c "..."` adjusting the import to `from agent_review import is_hard_case`.)

- [ ] **Step 3: Commit**

```bash
git add src/agent_review.py
git commit -m "feat: add Step 5 hard-case detection heuristic"
```

---

### Task 2: agent_reviews table + investigation prompt

**Files:**
- Modify: `src/agent_review.py` (append schema + LLM investigation)

**Interfaces:**
- Consumes: `is_hard_case` from Task 1 (same file).
- Consumes (existing, from `src/store.py`): `DB_PATH: Path`, `EVAL_DATE: str`, `load_tickets() -> dict[str, dict]` (dict keyed by mock `PROM-N` key, each value has `key`, `summary`, `status`, `assignee`).
- Produces: `build_agent_table(conn: sqlite3.Connection) -> None`, `build_user_prompt(row: dict, transcript_text: str, tickets: dict) -> str`, `investigate(client: Groq, row: dict, transcript_text: str, tickets: dict) -> dict` (returns dict with keys `reasoning`, `suggested_ticket`, `suggested_deadline`, `suggested_verdict`).

- [ ] **Step 1: Append schema, prompt, and investigation functions**

Add to `src/agent_review.py` (below the existing heuristic code):

```python
import json
import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from store import DB_PATH, EVAL_DATE, load_tickets

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"

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
```

- [ ] **Step 2: Smoke-test `build_agent_table` creates the table correctly**

Run (requires `data/promises.db` to already exist — run `python src/store.py` first if not):
```bash
python -c "
import sqlite3
from src.agent_review import build_agent_table
from src.store import DB_PATH
conn = sqlite3.connect(DB_PATH)
build_agent_table(conn)
conn.commit()
cur = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='agent_reviews'\")
print(cur.fetchall())
conn.close()
"
```

Expected output: `[('agent_reviews',)]`

- [ ] **Step 3: Smoke-test `investigate` on the real P10 case**

Run:
```bash
python -c "
import os, sqlite3
from dotenv import load_dotenv
from groq import Groq
from src.agent_review import investigate
from src.store import load_tickets
load_dotenv()
client = Groq(api_key=os.environ['GROQ_API_KEY'])
tickets = load_tickets()
conn = sqlite3.connect('data/promises.db')
conn.row_factory = sqlite3.Row
row = dict(conn.execute(\"SELECT * FROM promises WHERE speaker='Maria' AND promise_text LIKE '%checkout tests soon%'\").fetchone())
conn.close()
transcript = open('data/transcripts/' + row['meeting'], encoding='utf-8').read()
result = investigate(client, row, transcript, tickets)
print(result)
"
```

Expected: a dict with non-empty `reasoning` string and `suggested_verdict` one of `kept`/`broken`/`open` (no crash, valid JSON parsed). Inspect the reasoning text manually — it should reference the checkout-test ticket and explain the "soon" deadline judgment.

- [ ] **Step 4: Commit**

```bash
git add src/agent_review.py
git commit -m "feat: add Step 5 agent_reviews schema and LLM investigation"
```

---

### Task 3: Orchestration (`run()` + CLI entry point)

**Files:**
- Modify: `src/agent_review.py` (append orchestration)

**Interfaces:**
- Consumes: everything from Tasks 1-2 in the same file, plus `store.load_promises`-equivalent inline query.
- Produces: `run() -> int` (returns count of agent reviews written), executable as `python src/agent_review.py`.

- [ ] **Step 1: Append orchestration to `src/agent_review.py`**

```python
def load_promises(conn):
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute("SELECT * FROM promises")]


def run():
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not set. Put it in .env at project root.", file=sys.stderr)
        sys.exit(1)

    client = Groq(api_key=api_key)
    tickets = load_tickets()

    conn = sqlite3.connect(DB_PATH)
    promises = load_promises(conn)
    build_agent_table(conn)

    hard_rows = [(row, is_hard_case(row)) for row in promises]
    hard_rows = [(row, reasons) for row, reasons in hard_rows if reasons]

    print(f"Flagged {len(hard_rows)}/{len(promises)} promises as hard cases.")

    inserted = []
    for row, reasons in hard_rows:
        transcript_path = TRANSCRIPTS_DIR / row["meeting"]
        transcript_text = transcript_path.read_text(encoding="utf-8") if transcript_path.exists() else ""
        result = investigate(client, row, transcript_text, tickets)
        inserted.append((
            row["id"],
            "; ".join(reasons),
            result.get("reasoning", ""),
            result.get("suggested_ticket"),
            result.get("suggested_deadline"),
            result.get("suggested_verdict", "open"),
        ))
        print(f"  promise {row['id']} ({row['speaker']}): {reasons} -> suggested {result.get('suggested_verdict')}")

    conn.executemany(
        "INSERT INTO agent_reviews (promise_id, hard_case_reasons, reasoning, suggested_ticket, suggested_deadline, suggested_verdict) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        inserted,
    )
    conn.commit()
    conn.close()
    return len(inserted)


if __name__ == "__main__":
    n = run()
    print(f"Wrote {n} agent reviews -> {DB_PATH}")
```

- [ ] **Step 2: Run end-to-end**

Run:
```bash
python src/store.py
python src/agent_review.py
```

Expected: `store.py` prints `Stored 19 promises -> ...`. `agent_review.py` prints `Flagged 1/19 promises as hard cases.` (P10 is the only one — verified in Task 1's analysis: all 19 promises have ticket links per the answer key, only P10 has a null deadline / vague wording), one line for promise P10 showing its suggested verdict, then `Wrote 1 agent reviews -> ...`.

- [ ] **Step 3: Verify the row landed correctly**

Run:
```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/promises.db')
conn.row_factory = sqlite3.Row
rows = [dict(r) for r in conn.execute('SELECT * FROM agent_reviews')]
conn.close()
for r in rows:
    print(r)
"
```

Expected: exactly one row, `hard_case_reasons` containing `no deadline` and a vague-wording reason, non-empty `reasoning`, `suggested_verdict` one of kept/broken/open.

- [ ] **Step 4: Commit**

```bash
git add src/agent_review.py
git commit -m "feat: wire up Step 5 agent_review.py end-to-end orchestration"
```

---

### Task 4: `check.py` advisory display (additive)

**Files:**
- Modify: `src/check.py:1-49` (full current file shown below for exact context)

**Interfaces:**
- Consumes: `agent_reviews` table (Task 3), `DB_PATH` (already imported in `check.py`).
- Produces: `load_agent_reviews() -> dict[int, dict]` (keyed by `promise_id`). Does NOT change `check_all()`'s return value or the `decision` field.

- [ ] **Step 1: Add `load_agent_reviews()` and extend the `__main__` block only**

Current `src/check.py` end (lines 39-49):
```python
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
```

Replace with (adds a new function above `if __name__`, and appends a display block at the end — `check_all()` itself is untouched):

```python
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
```

- [ ] **Step 2: Run and verify decisions are unchanged, new section appears**

Run:
```bash
python src/check.py
```

Expected: the existing `meeting/speaker/ticket/...` table and `Decisions: {...}` line print exactly as before (compare decision counts to the pre-Step-5 baseline — unchanged), followed by a new "Hard-case agent reviews" section showing promise P10 (Maria) with its rule-based decision, the agent's suggested verdict, flagged reasons, and reasoning text.

- [ ] **Step 3: Commit**

```bash
git add src/check.py
git commit -m "feat: show Step 5 agent reasoning alongside check.py decisions (advisory only)"
```

---

### Task 5: `grade_agent.py` — 4th metric

**Files:**
- Create: `src/grade_agent.py`

**Interfaces:**
- Consumes: `data/answer_key.csv`, `promises` + `agent_reviews` tables in `data/promises.db`.
- Produces: CLI report; no functions consumed by later tasks.

- [ ] **Step 1: Write `src/grade_agent.py`**

```python
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
    except sqlite3.OperationalError:
        pass
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
```

- [ ] **Step 2: Run and record the 4th metric**

Run:
```bash
python src/grade_agent.py
```

Expected: table with exactly one data row for `P10` (speaker `Maria`), `gt_decision=broken`, `agent_verdict=<whatever the LLM suggested in Task 3>`, then `Paired 19/19...`, `Hard cases flagged (of paired): 1/19`, and the accuracy line. Record whatever value actually prints — this is the 4th metric to report to the user (don't assume it's 1/1; report the real result).

- [ ] **Step 3: Commit**

```bash
git add src/grade_agent.py
git commit -m "feat: add Step 5 grading script (hard-case count + accuracy)"
```

---

### Task 6: Update `progress.md`

**Files:**
- Modify: `progress.md`

**Interfaces:** None (documentation only).

- [ ] **Step 1: Update `progress.md`** per CLAUDE.md's session-end habit: add a note under "This session" describing Step 5 (`src/agent_review.py` + `src/grade_agent.py`, additive, hard-case heuristic, 1 hard case found in current data — P10), update "Current phase" to reflect Step 5 done, and add the 4th metric's actual value (from Task 5 Step 2) to the "Metrics" section as a new numbered line (do not renumber or alter the existing 3 metrics).

- [ ] **Step 2: Commit**

```bash
git add progress.md
git commit -m "docs: record Step 5 completion and 4th metric in progress.md"
```
