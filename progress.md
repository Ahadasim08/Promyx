# progress.md — Promise Tracker

## Current phase
Step 1 (promise extraction) — first pass done, working well. Not yet iterated on the miss below.

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

## Half-done / in progress
- One known miss: meeting4.txt, Maria's "I'll fix the broken password reset email by June 22" — model returned `ticket: "null"` (literal string, not real null) instead of linking to PROM-11. Ticket-linking failure on this one line, not a script bug. Not yet fixed — next step is to tighten the prompt (maybe stronger instruction to match on symptom/problem wording, not just noun overlap) and rerun.

## Next
- Iterate extraction prompt to fix the PROM-11 miss, rerun `python src/extract.py --all && python src/grade.py`, confirm recall/precision improves or stays at least 0.95.
- Once Step 1 numbers are solid, move to Step 2 (store promises in DB, link to tickets) — new session.

## Decisions
- Jira simulated locally via `data/jira_tickets.json` for Step 0-1 (no real Jira account needed yet). Real Jira REST API wired in from Step 3.
- Backend language: Python.
- LLM: Groq free tier, model `llama-3.3-70b-versatile`, `response_format={"type":"json_object"}` for structured output. Key lives in `.env` (gitignored), loaded via `python-dotenv`.
- Frontend (Step 4+) explicitly deferred. User wants a distinctive, non-generic-AI look — use `design-taste-frontend` skill when that step starts, not before.

## Surprises / learnings
- Groq JSON-mode occasionally returns the string `"null"` instead of real `null` for missing fields — worth normalizing/handling in the grading and later linking code (Step 2).
- Extraction handled the deliberately vague promise (P10) and all 5 distractor lines correctly on the very first prompt attempt — didn't need iteration for those.

## Decisions
- Jira simulated locally via `data/jira_tickets.json` for Step 0-1 (no real Jira account needed yet). Real Jira REST API wired in from Step 3.
- Backend language: Python.
- Frontend (Step 4+) explicitly deferred. User wants a distinctive, non-generic-AI look — use `design-taste-frontend` skill when that step starts, not before.

## Surprises / learnings
- (none yet)

## Metrics (fill in from Step 1 onward)
1. Promise-finding: recall = 0.95 (18/19), precision = 0.95 (18/19) — first pass, `llama-3.3-70b-versatile` via Groq, no prompt iteration yet.
2. Linking: % correct ticket = not measured separately yet (folded into recall/precision above since grading matches on speaker+ticket together). Split out properly in Step 2.
3. Checking: kept/not-kept accuracy = - (Step 3, not started).
