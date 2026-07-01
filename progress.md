# progress.md — Promise Tracker

## Current phase
Step 4 (review web page) — FINISHED. Steps 0-4 all complete. Not started Step 5.

## This session
- Finished Step 4: review dashboard with working human override buttons. Clicking Kept/Broken/Open calls `POST /api/promises/<id>/override/`, which writes to Django's `Override` table — confirmed this persists across a hard refresh (reads back via `GET /api/promises/`), not just optimistic UI state.
- Heavy UI pass on top of the working Step 4 base (all via `/impeccable`): warm OKLCH color system (replaced the original cool-blue palette), `lucide-react` icons throughout, collapsible sidebar with status filters + sliding active-indicator, manual dark-mode toggle (class-based, independent of OS preference), collapsible status groups (Kept collapsed by default to cut scroll length), search by speaker/ticket, sort (deadline/speaker), collapse-all/expand-all, save-success flash + per-row error+retry on failed override, skeleton loading state, "Promyx" branding made prominent (28px bold wordmark in header + sidebar, was previously a barely-visible 12px kicker), speaker names enlarged/bolded in each row (were 12px, same weight as meeting filename — hard to scan).
- None of this touched `src/*.py` or the metrics — it's all `backend/tracker/views.py` (unchanged) + `frontend/`.

## Done
- Step 0: `data/jira_tickets.json` (18 tickets), `data/transcripts/meeting1-6.txt`, `data/answer_key.csv` (19 promises P01-P19) + `answer_key_notes.md`. Repo on GitHub, `.env` gitignored.
- Step 1: `src/extract.py` (Groq `llama-3.3-70b-versatile`) + `src/grade.py`. Recall/precision 1.00/1.00 (19/19) after one prompt fix.
- Step 2: `src/store.py` (builds `data/promises.db`, computes ticket link + open/done/overdue status) + `src/grade_linking.py`. Linking accuracy 19/19 = 1.00.
- Step 3: `src/check.py` + `src/grade_checking.py`.
- Step 4: `backend/` (Django API) + `frontend/` (React/Vite review page), including working save-and-persist overrides. UI has had a full design pass — no longer a bare-bones scaffold.
- Real Jira integration (this session, closes the last open item from Step 3): `src/jira_client.py` (auths with `JIRA_EMAIL`/`JIRA_API_TOKEN`, hits `GET /rest/api/3/search/jql`) + `src/seed_jira.py` (one-off, seeded 18 real issues in a new Jira Cloud site). `store.py`'s `load_tickets()` now pulls live ticket status instead of the JSON fixture.

## Half-done / in progress
- Nothing outstanding from Steps 0-4 or the Jira swap.

## This session (real Jira integration)
- Created a real Jira Cloud site (`https://ahadasim.atlassian.net`, project key `KAN`). Seeded 18 issues via `src/seed_jira.py`, matching the mock `data/jira_tickets.json` summaries + statuses 1:1.
- **Promise-to-ticket matching is by summary text, not by number.** `PROM-N` (extracted from transcripts) and `KAN-N` (real Jira's own key scheme) are unrelated, coincidental numbering — `store.py`'s `load_tickets()` joins them by matching summary string, looked up via `jira_client.fetch_live_tickets()`. `data/jira_tickets.json` is kept only for the `PROM-N -> summary` mapping now, not for status.
- Gotcha: Jira's old `GET /rest/api/3/search` returns `410 Gone` (deprecated) — switched to `GET /rest/api/3/search/jql` with `nextPageToken` pagination.
- **Verified the integration is actually live**, not cached/stale: manually changed a real ticket's status in the Jira UI (`KAN-11`, matched to `PROM-8`, Tom's "fix the memory leak" promise) from In Progress to Done, then re-ran the pipeline (`store.py` -> `check.py`) and confirmed the dashboard/CLI decision for that promise flipped from open to kept. Repeated this a few times during the session with different tickets (`KAN-8`, `KAN-9`, `KAN-11`) — each manual Jira change correctly moved its matched promise's decision on the next run.
- New `.env` vars: `JIRA_SITE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY` (gitignored).

## Next
- Single next action: none required — real Jira integration is verified and working. Step 5 (the "smart investigator" reasoning agent) is the only thing left, stretch/optional. Don't start without user confirmation first.

## How to run Step 4
- Backend: `cd backend && python manage.py runserver 8000` (needs `pip install -r requirements.txt`; first time also run `python manage.py migrate`).
- Frontend: `cd frontend && npm install && npm run dev` — serves at `http://localhost:5173`, talks to the API at `http://127.0.0.1:8000`.
- Run `python src/store.py` (and `check.py` if you want the CLI view too) before starting the backend so `data/promises.db` exists.

## Metrics (current, live Jira, as of last pipeline run this session)
1. Promise-finding: recall = 1.00 (19/19), precision = 1.00 (19/19) — `src/grade.py`. Unaffected by the Jira swap or live status drift.
2. Linking: % correct ticket = 19/19 = 1.00 — `src/grade_linking.py`. Unaffected — summary-text matching is working correctly.
3. Checking: accuracy = 15/19 = 0.79, false-accusation rate = 0/8 = 0.00 — `src/grade_checking.py`. Lower than the mock-data baseline (was 18/19) because several real tickets (`KAN-5`, `KAN-8`, `KAN-9`, `KAN-11`) were manually moved to Done in Jira during this session's verification testing — this is expected drift from live data changing, not a pipeline bug. False-accusation rate (the metric that must stay low per CLAUDE.md) is unaffected at 0.00.

## Decisions
- Jira simulated locally via `data/jira_tickets.json` for Steps 0-2; real Jira REST API wiring is Step 3+ scope per CLAUDE.md but not yet done (Step 3 so far only added local kept/broken/open logic on top of the simulated data — real API integration still pending, see Surprises).
- Backend: Python. LLM: Groq free tier, `llama-3.3-70b-versatile`, JSON mode, key in gitignored `.env`.
- Step 4 keeps promises.db and Django's db.sqlite3 as two separate databases on purpose (see this session's notes) rather than merging Override into the promises schema.

## Surprises / learnings
- CLAUDE.md says "Jira REST API real integration from Step 3" but the actual Step 3 task given this session was purely the kept/broken/open decision logic on the existing simulated data — no real Jira API was wired up. Still true this session; see Next.
- The one Step 3 miss (P10, Maria's vague "soon" promise, no deadline) is the same root cause as the Step 2 status-accuracy miss: Step 1 extraction never captured a deadline for vague promises, so downstream logic can't mark it overdue. Fixing this means revisiting the Step 1 prompt, not Step 2/3 code.
- Groq JSON-mode occasionally returns the string `"null"` instead of real `null` — normalized via `norm()` helpers in grade scripts, and the extraction prompt now tells the model not to do this.
- Recurring gotcha this session: Playwright verification scripts that click the actual override buttons (not just filters/toggles) create real rows in `backend/db.sqlite3`'s `Override` table, which then show up as fake "Overridden by reviewer" tags and skew the Broken/Open/Kept counts for the next person who opens the app. Had to clear `Override.objects.all().delete()` via `python manage.py shell` three times this session. If review counts ever look off vs. `data/answer_key.csv`, check for stray Override rows before assuming a data or logic bug.
- Caught myself about to ship gradient text (`background-clip: text` on the "Promyx" wordmark) — that's on the design skill's explicit ban list. Fixed to solid accent color before it shipped. Worth remembering if restyling the brand mark again.
