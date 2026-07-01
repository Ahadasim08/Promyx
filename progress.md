# progress.md — Promise Tracker

## Current phase
Step 0 complete. Step 1 (promise extraction) not started — next session.

## Done
- CLAUDE.md written.
- progress.md created (this file).
- Step 0a: `data/jira_tickets.json` — 18 tickets (PROM-1..18), mix of Done(7)/In Progress(5)/To Do(6).
- Step 0b: `data/transcripts/meeting1.txt`..`meeting6.txt` — 6 fake standup transcripts.
- Step 0c: `data/answer_key.csv` — 19 hand-written ground-truth promises (P01-P19), plus `data/answer_key_notes.md` (eval date, distractor lines, vague case, sanity counts).

## Half-done / in progress
- (none — Step 0 fully done)

## Next
- Step 1: build extraction script (Python) that reads one transcript, outputs promise records: who / what / which ticket it seems to point at / by when.
- Grade output against `data/answer_key.csv`: recall (caught real promises?) + precision (invented any?). Watch the 5 distractor lines in `answer_key_notes.md` specifically — extraction must not flag those as promises.
- Watch P10 (Maria, meeting3.txt) — vague promise, no explicit deadline, ticket must be inferred. Good stress test.
- Write first recall/precision numbers into Metrics section below, then iterate on the extraction prompt.

## Decisions
- Jira simulated locally via `data/jira_tickets.json` for Step 0-1 (no real Jira account needed yet). Real Jira REST API wired in from Step 3.
- Backend language: Python.
- Frontend (Step 4+) explicitly deferred. User wants a distinctive, non-generic-AI look — use `design-taste-frontend` skill when that step starts, not before.

## Surprises / learnings
- (none yet)

## Metrics (fill in from Step 1 onward)
1. Promise-finding: recall = -, precision = -
2. Linking: % correct ticket = -
3. Checking: kept/not-kept accuracy = -, false-accusation rate = -
