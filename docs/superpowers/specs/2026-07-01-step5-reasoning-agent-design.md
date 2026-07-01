# Step 5 — Hard-Case Reasoning Agent

## Goal
Add a small reasoning agent that activates only for promises the existing rule-based pipeline (`extract.py` -> `store.py` -> `check.py`) can't handle cleanly. It writes plain-language reasoning a human reviewer can read and judge, alongside a suggested verdict. It is purely additive: nothing in Steps 1-4 changes, and the rule-based decision remains authoritative.

## Non-goals
- Not replacing or overriding `check.py`'s rule-based kept/broken/open decision.
- Not re-processing every promise — only ones flagged hard.
- Not changing `extract.py`'s prompt/schema to add confidence scores.
- Not wiring into the frontend (Step 4) in this pass.

## Hard-case detection
Rule-based, computed from data already in `promises.db` (no new LLM call needed to detect). A promise is "hard" if any of:
- `ticket` is null (no ticket link at all)
- `deadline` is null
- `promise_text` contains a vague-language marker (case-insensitive substring match): `soon`, `eventually`, `at some point`, `take care of`, `get to it`, `sometime`

This runs in a new function `is_hard_case(row) -> list[str]` (returns the matched reasons, or empty list) in `src/agent_review.py`.

## Investigation (LLM call, Groq — same pattern as extract.py)
For each hard case:
1. Look up the original transcript text via `promises.meeting` -> `data/transcripts/<meeting>`.
2. Fetch the full live ticket list via `jira_client.fetch_live_tickets()` (not just the one linked ticket).
3. Send the LLM: the promise text + speaker, the transcript (for surrounding context), the full ticket list, and the currently-linked ticket/deadline/status (if any).
4. Ask it to reason step-by-step in plain language: is the current ticket link correct or is there a better match in the full list? what's the most likely intended deadline, if any, based on context? given ticket status + inferred deadline, what's the verdict (kept/broken/open)?
5. Response format: JSON with `reasoning` (string, plain language), `suggested_ticket` (string or null), `suggested_deadline` (YYYY-MM-DD or null), `suggested_verdict` (kept/broken/open).

## Storage
New table in `data/promises.db`, created/rebuilt by `agent_review.py` only (never touches the existing `promises` table):

```sql
CREATE TABLE IF NOT EXISTS agent_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    promise_id INTEGER NOT NULL,
    hard_case_reasons TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    suggested_ticket TEXT,
    suggested_deadline TEXT,
    suggested_verdict TEXT NOT NULL
);
```

`agent_review.py` does `DROP TABLE IF EXISTS agent_reviews` then repopulates on each run, same pattern as `store.py` does for `promises`.

## CLI display
`check.py` gets an optional section: for any row with a matching `agent_reviews` entry (joined by `promise_id`), print the agent's suggested verdict + reasoning next to the rule-based decision. The rule-based `decision` value returned by `check_all()` is unchanged — this is print-only, informational.

## Grading (4th metric)
New `src/grade_agent.py`, reusing the speaker + promise-text pairing logic from `grade_checking.py`. Reports:
- How many of the 19 answer-key promises were flagged as hard cases.
- Of those, how many the agent's `suggested_verdict` matched the answer key's `ground_truth`.

This is a 4th number, reported separately from — not replacing — the 3 metrics CLAUDE.md already requires (promise-finding, linking, checking).

## Files touched
- New: `src/agent_review.py`, `src/grade_agent.py`
- Modified (additive only): `src/check.py` (optional display section), `progress.md` (update after implementation)
- Untouched: `src/extract.py`, `src/store.py`, `src/jira_client.py`, `data/answer_key.csv`, `backend/`, `frontend/`

## Known hard case from answer key
P10 (Maria, "I'll take care of that thing with the checkout tests soon", null deadline) — currently mislabeled "open" by the rule-based pipeline because `compute_status` treats a null deadline as never-overdue. Ground truth is "broken". This is the primary case Step 5 should demonstrate improvement on.
