# Build Plan — "Promise Tracker" (Jira version)

A tool that listens to meetings, pulls out the promises people made, and checks against Jira whether each promise was actually kept.

**How to use this plan:** Do the steps in order. Only take Step 0 and Step 1 into Claude Code first. Do NOT try to plan Steps 4–6 in detail yet — you'll understand them much better once Steps 0–3 are working. This plan is the map; Claude Code fills in the exact roads as you go.

---

## How to work in phases (across separate Claude Code sessions)

You'll build one phase per session: open a session, build a phase, save state, exit. Next phase = new session. Two files make this work so a new session doesn't start from zero.

### The two memory files

**CLAUDE.md — the rules of the house (rarely changes).**
Stable facts true in every session. Write it once; only update it when something structural changes. Put in it:
- What the project is (2 lines).
- Tech stack: Django, React, Jira REST API.
- How the folders are organized.
- How to run the app and how to run the tests.
- The hard rules: always grade against the answer key; keep the 3 metrics updated; never delete the answer key.

**progress.md — today's status (changes every session).**
The living log of where things stand. Put in it:
- Which phase you're on.
- What's done, what's half-done, what's next.
- Decisions made and surprises found last session (e.g. "extractor misses vague promises — needs work").
- The latest values of the 3 metrics.

One-line difference: **CLAUDE.md = the rules; progress.md = the status.**

### The session habit

- **End of every session (before exit):** "Update progress.md — what we did, what's left, what you learned."
- **Start of every session:** "Read CLAUDE.md and progress.md first. Then look at the actual files for the part we're working on."

### Important correction

Do NOT let a new session read *only* progress.md. progress.md tells Claude Code **where things stand and where to look** — but the real code is the truth. A summary is always a little out of date; if Claude trusts it blindly it will build on wrong assumptions. So: read progress.md to get oriented, then read the actual files for whatever you're about to change.

---

## The one rule that makes this project serious

The impressive part is not "find promises in a meeting." Anyone can do that.
The impressive part is **checking whether the promise really happened.**
So the plan is built around proving that the checking works — with real numbers, not opinions.

---

## Step 0 — Build your test data and your "answer key" (do this first, no code)

Everything depends on this. Do not skip it.

**a) Make a free Jira project.**
- Create a free Jira Cloud account (free plan, up to 10 users — enough).
- Create one project with about 15–20 tickets ("Fix login bug", "Add export button", etc.).
- Put them in different states on purpose: some **Done**, some still **In Progress**, some **To Do**.

**b) Make 5–10 fake meeting transcripts (just text files).**
- In each meeting, have people make promises that point at those tickets.
  Example: "Ali: I'll close the login bug ticket by Friday."
- Make some promises that were kept (the matching ticket is Done) and some that were not (the ticket is still open). You want a mix.

**c) Write the ANSWER KEY (the most important part).**
- Make a simple table. For every promise in your transcripts, write down the truth **by hand**:
  - who promised it
  - which ticket it points to
  - was it kept? (yes / no)
- This table is what you'll grade your tool against later. Without it, you can never prove your tool is right.

**Why this step matters:** This is your ground truth. Later, when your tool says "this promise was kept," you check it against this table to see if the tool was correct.

---

## Step 1 — Find the promises (the AI part)

Build the piece that reads one transcript and pulls out the promises as clean records.

**Input:** a meeting transcript (text).
**Output:** a list of promises, each with: who / what / which ticket it seems to point at / by when.

**How to check it worked:** Compare your tool's promises against your answer key from Step 0.
- Did it catch the real promises? (recall)
- Did it invent promises that weren't really there? (precision)

Get a first number, then improve the prompt until the numbers get better. Write the numbers down each time.

**This is the step to fully detail inside Claude Code.** Take just this step there and let it break it into tasks.

---

## Step 2 — Store the promises and link each one to a real ticket

- Save each promise in a small database, with a status: **open / done / overdue**.
- Link each promise to the correct Jira ticket. "The login bug" → ticket PROJ-42. This matching is its own tricky job — sometimes the promise is vague and you have to pick the right ticket.

**How to check it worked:** For each promise, did it link to the *correct* ticket? (Grade against your answer key.)

---

## Step 3 — Check reality (the heart of the project)

For each promise, look up its linked Jira ticket's current status and decide:
- Ticket is **Done** → promise **kept**.
- Ticket not done and the deadline passed → promise **broken / overdue**.
- Ticket not done, deadline not here yet → **still open**.

**How to check it worked (two numbers — write both down):**
1. Overall: how often did it correctly say kept vs. not kept?
2. **False accusations:** how often did it say "broken" when the promise was actually kept? This number must be very low. Telling someone they broke a promise they kept is the mistake that destroys trust — measure it on its own.

---

## Step 4 — The screen (your web-stack part)

A simple web page (React / Django) showing:
- promises grouped by status (done / open / overdue)
- for each one, the evidence: which ticket, what its status is
- a button for a human to confirm or override the tool's decision

The human always makes the final call. Say this out loud in your demo — it's a strength, not a weakness.

*(Keep this light for now. Detail it when you get here.)*

---

## Step 5 — The "smart investigator" (stretch, do last)

Some promises won't link cleanly or won't verify cleanly. For those hard cases, add a small reasoning agent that investigates and writes down *why* it decided what it decided, so a human can see its reasoning.

This is the part that makes you look senior. But it only matters after Steps 0–4 work. Do not start here.

*(Detail this only when you reach it.)*

---

## The 3 numbers that prove the project works

Keep these visible from Step 1 onward. These are what a recruiter or client will ask about:

1. **Promise-finding:** how many real promises caught, how many invented (recall + precision).
2. **Linking:** % of promises matched to the correct ticket.
3. **Checking:** accuracy of kept/not-kept — and the false-accusation rate, kept separately.

A project with these numbers looks like engineering. A project without them looks like a school assignment, no matter how good the code is.

---

## Order of attack (short version)

1. Step 0 — test data + answer key (no code)
2. Step 1 — find promises → get your first numbers
3. Step 2 — store + link to tickets
4. Step 3 — check against Jira → get your checking numbers
5. Step 4 — the web page
6. Step 5 — the smart investigator (only if time)

Take Steps 0 and 1 into Claude Code now. Nothing else yet.
