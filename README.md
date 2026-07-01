# Promyx

AI tool that listens to meeting transcripts, extracts promises people made, and checks against Jira whether each promise was actually kept.

## How it works

1. **Extract** — an LLM reads meeting transcripts and pulls out promises (speaker, text, ticket, deadline).
2. **Store + link** — promises are saved to a local database and linked to their Jira ticket.
3. **Check** — each promise is marked `kept`, `broken`, or `open` by comparing the linked ticket's status and deadline against an evaluation date.
4. **Review UI** — a dashboard (Django API + React frontend) lets a human review the decisions and override any of them.
5. **Hard-case agent** — for promises the rule-based checker can't resolve cleanly (ambiguous ticket, no deadline, vague wording like "soon"), an LLM investigates and writes plain-language reasoning next to the automatic decision. Advisory only — never overrides the automatic decision.

## Folder layout

```
/data
  /jira_tickets.json     - PROM-N -> summary mapping (ticket status comes from live Jira, not this file)
  /transcripts/           - meeting transcripts (.txt)
  /answer_key.csv         - hand-written ground truth used for grading
  /promises.db            - built by src/store.py (gitignored, generated)
/src                       - pipeline scripts (extraction, storage, checking, Jira client, grading)
/backend                   - Django API: serves promises.db + stores human review overrides
/frontend                  - React/Vite review dashboard
```

## Setup

1. `pip install -r requirements.txt`
2. `cd frontend && npm install`
3. Create a `.env` file in the project root with:
   ```
   GROQ_API_KEY=...
   JIRA_SITE_URL=https://your-site.atlassian.net
   JIRA_EMAIL=...
   JIRA_API_TOKEN=...
   JIRA_PROJECT_KEY=...
   ```
   - `GROQ_API_KEY` — from [Groq](https://console.groq.com), used for promise extraction and the hard-case agent.
   - Jira vars — an API token can be created at https://id.atlassian.com/manage-profile/security/api-tokens.

## Running the pipeline

From the project root, in order:

```bash
python src/extract.py --all      # extract promises from transcripts -> data/extracted/
python src/store.py              # build data/promises.db, link tickets, compute status
python src/check.py              # print kept/broken/open decisions
python src/agent_review.py       # run the hard-case reasoning agent (optional, after store.py)
python src/check.py              # re-run to see the agent's advisory notes alongside decisions
```

## Grading (against `data/answer_key.csv`)

```bash
python src/grade.py            # promise-finding: recall + precision
python src/grade_linking.py    # ticket-linking accuracy
python src/grade_checking.py   # kept/broken/open accuracy + false-accusation rate
python src/grade_agent.py      # hard-case count + agent suggested_verdict accuracy
```

## Running the review dashboard

Requires `python src/store.py` to have been run first.

```bash
cd backend && python manage.py migrate && python manage.py runserver 8000
cd frontend && npm run dev   # http://localhost:5173
```
