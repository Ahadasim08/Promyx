# CLAUDE.md — Promise Tracker

## What this is
Tool that listens to meeting transcripts, extracts promises people made, and checks against Jira whether each promise was actually kept.

## Tech stack
- Backend: Python (Django later, from Step 2 onward)
- Frontend: React (Step 4+, NOT now — must be distinctive, not generic AI-template look; use `design-taste-frontend` skill when we get there)
- Jira: Jira REST API (real integration from Step 3; Step 0-1 use a local JSON fixture simulating Jira export)

## Folder layout
```
/data
  /jira_tickets.json     - simulated Jira export (key, summary, status, assignee)
  /transcripts/           - fake meeting transcripts (.txt)
  /answer_key.csv         - hand-written ground truth (see rules below)
/src                       - code (extraction scripts etc., grows from Step 1)
```

## How to run
- (fill in once Step 1 code exists)

## How to test
- (fill in once Step 1 code exists)

## Hard rules
1. **Always grade against the answer key** (`data/answer_key.csv`). Never trust the tool's own output as ground truth.
2. **Never delete or silently edit the answer key.** It's hand-written ground truth. Changes must be deliberate and reviewed.
3. **Keep the 3 metrics visible and updated** every time extraction/linking/checking logic changes:
   - Promise-finding: recall + precision
   - Linking: % promises matched to correct ticket
   - Checking: kept/not-kept accuracy + false-accusation rate (tracked separately — this one must stay very low)
4. Do Steps in order. Don't jump ahead to Step 4 (frontend) or Step 5 (agent) until Steps 0-3 numbers are proven.
5. Frontend, when we get there: no generic AI-template look. Use `design-taste-frontend` skill.

## Session habit
- Start of session: read this file + `progress.md`, then read the actual current files for the part being worked on (progress.md goes stale, code doesn't).
- End of session: update `progress.md` — what got done, what's half-done, what's next, surprises found, latest metric values.
