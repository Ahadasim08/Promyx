# CLAUDE.md — Promise Tracker

## What this is
Tool that listens to meeting transcripts, extracts promises people made, and checks against Jira whether each promise was actually kept.

## Tech stack
- Backend: Python (Django from Step 4 onward — `backend/`, app `tracker`)
- Frontend: React (Step 4+ — `frontend/`, Vite; distinctive, not generic AI-template look; used `design-taste-frontend` skill, which correctly flagged this as a dashboard, out of that skill's marketing-page scope, so styling was done by hand instead)
- Jira: real Jira Cloud REST API (`src/jira_client.py`), wired up this session. Live site: `ahadasim.atlassian.net`, project key `KAN`. `data/jira_tickets.json` is kept only as the `PROM-N -> summary` mapping (extraction still produces `PROM-N` ticket refs); live ticket status is joined in by matching summary text, since real Jira keys (`KAN-N`) don't match the mock `PROM-N` keys.

## Folder layout
```
/data
  /jira_tickets.json     - PROM-N -> summary mapping only now (status comes from live Jira, not this file)
  /transcripts/           - fake meeting transcripts (.txt)
  /answer_key.csv         - hand-written ground truth (see rules below)
  /promises.db            - built by src/store.py; read-only from backend/tracker
/src                       - code (extraction, store, check, jira_client.py for real Jira API, seed_jira.py one-off seeding script)
/backend                   - Django API (tracker app): serves promises.db + stores human review overrides in its own db.sqlite3
/frontend                  - React/Vite review page (Step 4)
```

## Jira setup
Needs these in `.env`: `JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`. Get an API token at https://id.atlassian.com/manage-profile/security/api-tokens.

## How to run
- Step 1 (extract): `python src/extract.py --all` (or a single transcript path). Needs `GROQ_API_KEY` in `.env`. Writes `data/extracted/<meeting>.json`.
- Step 2 (store + link): `python src/store.py`. Rebuilds `data/promises.db` from `data/extracted/*.json`, links each promise to its Jira ticket, computes status (open/done/overdue).
- Step 4 (review page): `cd backend && python manage.py runserver 8000` and, separately, `cd frontend && npm run dev` (http://localhost:5173). Run `store.py` first so `data/promises.db` exists.

## How to test
- Step 1 grading: `python src/grade.py` — recall/precision of promise-finding vs `data/answer_key.csv`.
- Step 2 grading: `python src/grade_linking.py` — linking accuracy (correct ticket) and status accuracy vs `data/answer_key.csv`. Run `store.py` first.

## Hard rules
1. **Always grade against the answer key** (`data/answer_key.csv`). Never trust the tool's own output as ground truth.
2. **Never delete or silently edit the answer key.** It's hand-written ground truth. Changes must be deliberate and reviewed.
3. **Keep the 3 metrics visible and updated** every time extraction/linking/checking logic changes:
   - Promise-finding: recall + precision
   - Linking: % promises matched to correct ticket
   - Checking: kept/not-kept accuracy + false-accusation rate (tracked separately — this one must stay very low)
4. Do Steps in order. Don't jump ahead to Step 5 (agent) until Steps 0-4 are proven.
5. Frontend: no generic AI-template look. Use `design-taste-frontend` skill (it may correctly say a given screen is out of its scope, e.g. dashboards — in that case follow its judgment rather than forcing marketing-page patterns onto it).

## Session habit
- Start of session: read this file + `progress.md`, then read the actual current files for the part being worked on (progress.md goes stale, code doesn't).
- End of session: update `progress.md` — what got done, what's half-done, what's next, surprises found, latest metric values.
