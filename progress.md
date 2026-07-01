# progress.md — Promise Tracker

## Current phase
Step 2 (store + link) — DONE. Linking accuracy 19/19 = 1.00. Ready for Step 3 next session.

## Done
- CLAUDE.md written.
- progress.md created (this file).
- Step 0a: `data/jira_tickets.json` — 18 tickets (PROM-1..18), mix of Done(7)/In Progress(5)/To Do(6).
- Step 0b: `data/transcripts/meeting1.txt`..`meeting6.txt` — 6 fake standup transcripts.
- Step 0c: `data/answer_key.csv` — 19 hand-written ground-truth promises (P01-P19), plus `data/answer_key_notes.md` (eval date, distractor lines, vague case, sanity counts).
- Repo pushed to GitHub: https://github.com/Ahadasim08/Promyx (main branch). `.env` correctly gitignored, never committed.
- Step 1: `src/extract.py` — reads a transcript (or `--all`), calls Groq (`llama-3.3-70b-versatile`), outputs `data/extracted/<meeting>.json` per transcript. Prompt includes known ticket list so model can infer ticket from context, not just exact name match.
- `src/grade.py` — grades extracted output against `data/answer_key.csv` (matches by speaker+ticket), prints per-file and overall recall/precision.
- Ran full pipeline on all 6 transcripts. **First-pass numbers: recall=0.95 (18/19), precision=0.95 (18/19).** Correctly ignored all 5 distractor (non-promise) lines — zero false positives from those. Correctly caught the vague no-deadline promise (P10, Maria/meeting3).

- Step 2: `src/store.py` — SQLite DB `data/promises.db`, one `promises` table. Rebuilds from scratch each run (drop+recreate) from `data/extracted/*.json`. Persists the ticket link extraction already made, joins against `data/jira_tickets.json` for ticket status, computes `status` (open/done/overdue) from ticket status + deadline vs eval date `2026-07-01`.
- `src/grade_linking.py` — pairs each answer-key promise to a stored row by speaker + near-identical promise text (independent of ticket, so ticket correctness is graded on its own axis), reports linking accuracy and a bonus status accuracy.
- Linking accuracy: **19/19 = 1.00** (extraction's ticket inference from Step 1 held up perfectly once persisted).
- Status accuracy (bonus, not an official Step 2 metric but cheap to compute): 18/19 = 0.95. Miss is P10 (Maria's vague "soon" promise) — no explicit deadline extracted, so `store.py` can't tell it's overdue and defaults to open. Expected limitation, not a Step 2 bug — deadline inference for vague promises is a Step 1/prompt problem.

## Half-done / in progress
- (none — Step 2 fully done)

## Next
- Step 3 (new session): check each promise's linked ticket status against reality, decide kept/broken/still-open, and measure the two Step 3 numbers (accuracy + false-accusation rate). Note: Step 2's "status" field already computes open/done/overdue — Step 3 should reuse or fold into it rather than re-deriving the same logic twice.

## Decisions
- Jira simulated locally via `data/jira_tickets.json` for Step 0-1 (no real Jira account needed yet). Real Jira REST API wired in from Step 3.
- Backend language: Python.
- LLM: Groq free tier, model `llama-3.3-70b-versatile`, `response_format={"type":"json_object"}` for structured output. Key lives in `.env` (gitignored), loaded via `python-dotenv`.
- Frontend (Step 4+) explicitly deferred. User wants a distinctive, non-generic-AI look — use `design-taste-frontend` skill when that step starts, not before.

## Surprises / learnings
- Groq JSON-mode occasionally returns the string `"null"` instead of real `null` for missing fields — normalized this in `grade.py`'s `norm()` and told the model explicitly not to do it in the prompt. Worth remembering for Step 2's linking/storage code too.
- Extraction handled the deliberately vague promise (P10) and all 5 distractor lines correctly on the very first prompt attempt — didn't need iteration for those.
- The one miss (Maria/PROM-11) was a near-verbatim match ("fix the broken password reset email" vs. ticket summary "Fix broken password reset email") that the model still skipped — not a hard case at all. Fixed by explicitly instructing it to check every promise against every ticket before defaulting to null, rather than assuming obvious matches don't need reinforcement.

## Decisions
- Jira simulated locally via `data/jira_tickets.json` for Step 0-1 (no real Jira account needed yet). Real Jira REST API wired in from Step 3.
- Backend language: Python.
- Frontend (Step 4+) explicitly deferred. User wants a distinctive, non-generic-AI look — use `design-taste-frontend` skill when that step starts, not before.

## Surprises / learnings
- (none yet)

## Metrics (fill in from Step 1 onward)
1. Promise-finding: recall = 1.00 (19/19), precision = 1.00 (19/19) — after one prompt iteration, `llama-3.3-70b-versatile` via Groq. First pass was 0.95/0.95 (18/19); fixed by telling the model to explicitly check every promise against every ticket summary before giving up, and to use real JSON null instead of the string "null".
2. Linking: % correct ticket = 19/19 = 1.00 (`src/grade_linking.py`, Step 2, graded independently of promise-finding this time — pairs by speaker+text, checks ticket separately).
3. Checking: kept/not-kept accuracy = - (Step 3, not started).
