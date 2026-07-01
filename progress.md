# progress.md — Promise Tracker

## Current phase
Step 3 (check kept/broken/open) — DONE. Steps 0-3 all complete. Not started Step 4.

## This session (Step 3)
- Verified code state matched progress.md before starting (checked git log, git status, extracted files) — no drift.
- Added `src/check.py`: reads `data/promises.db`, relabels store.py's `status` field (open/done/overdue, already computed in Step 2) to kept/broken/open via `DECISION_MAP`. Did not re-derive the Done/deadline logic — reused Step 2's field on purpose.
- Added `src/grade_checking.py`: pairs answer-key rows to stored rows (same speaker+text pairing as `grade_linking.py`, copied not imported), compares decision to `ground_truth`, reports accuracy + false-accusation rate.
- Ran `store.py` -> `check.py` -> `grade_checking.py` against the 19-promise answer key.
- Updated this file.

## Done
- Step 0: `data/jira_tickets.json` (18 tickets), `data/transcripts/meeting1-6.txt`, `data/answer_key.csv` (19 promises P01-P19) + `answer_key_notes.md`. Repo on GitHub, `.env` gitignored.
- Step 1: `src/extract.py` (Groq `llama-3.3-70b-versatile`) + `src/grade.py`. Recall/precision 1.00/1.00 (19/19) after one prompt fix.
- Step 2: `src/store.py` (builds `data/promises.db`, computes ticket link + open/done/overdue status) + `src/grade_linking.py`. Linking accuracy 19/19 = 1.00.
- Step 3: `src/check.py` + `src/grade_checking.py`. Accuracy 18/19 = 0.95, false-accusation rate 0/8 = 0.00.

## Half-done / in progress
- (none — Steps 0-3 fully done)

## Next
- Single next action: start Step 4 (React frontend). Before writing any component, invoke `design-taste-frontend` skill — user explicitly wants a distinctive, non-generic-AI look, not the default template feel. Don't start without user confirmation first.

## Metrics (current)
1. Promise-finding: recall = 1.00 (19/19), precision = 1.00 (19/19) — `src/grade.py`.
2. Linking: % correct ticket = 19/19 = 1.00 — `src/grade_linking.py`.
3. Checking: accuracy = 18/19 = 0.95, false-accusation rate = 0/8 = 0.00 — `src/grade_checking.py`. Unchanged this session's numbers are new (Step 3 just built).

## Decisions
- Jira simulated locally via `data/jira_tickets.json` for Steps 0-2; real Jira REST API wiring is Step 3+ scope per CLAUDE.md but not yet done (Step 3 so far only added local kept/broken/open logic on top of the simulated data — real API integration still pending, see Surprises).
- Backend: Python. LLM: Groq free tier, `llama-3.3-70b-versatile`, JSON mode, key in gitignored `.env`.
- Frontend (Step 4+) explicitly deferred, must use `design-taste-frontend` skill, not before.

## Surprises / learnings
- CLAUDE.md says "Jira REST API real integration from Step 3" but the actual Step 3 task given this session was purely the kept/broken/open decision logic on the existing simulated data — no real Jira API was wired up. Flag this gap to the user before calling Steps 0-3 fully done in the CLAUDE.md sense.
- The one Step 3 miss (P10, Maria's vague "soon" promise, no deadline) is the same root cause as the Step 2 status-accuracy miss: Step 1 extraction never captured a deadline for vague promises, so downstream logic can't mark it overdue. Fixing this means revisiting the Step 1 prompt, not Step 2/3 code.
- Groq JSON-mode occasionally returns the string `"null"` instead of real `null` — normalized via `norm()` helpers in grade scripts, and the extraction prompt now tells the model not to do this.
