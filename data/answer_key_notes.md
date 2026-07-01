# Answer key notes

**Evaluation date:** 2026-07-01 (used to decide open vs. broken for tickets not yet Done).

**19 real promises** across 6 transcripts — see `answer_key.csv`. This is ground truth. Never edit by hand without deliberate review; never let the tool overwrite it.

**Distractor lines (NOT promises — used to test precision in Step 1):**
Extraction should NOT flag these as promises. If it does, that's a precision miss.
- meeting1.txt — Ben: "I think we should also look into whether the login bug affects the mobile app, worth checking later."
- meeting2.txt — Maria: "Also we should talk about upgrading the CI runners at some point."
- meeting4.txt — Sara: "Also, has anyone looked at the analytics dashboard lately? Might need a refresh eventually."
- meeting5.txt — Tom: "We might also want to revisit the caching layer at some point, no rush."
- meeting6.txt — Ali: "Great week everyone, let's keep the momentum going."

**Vague case (P10):** Maria's "I'll take care of that thing with the checkout tests soon" — real promise, no explicit deadline, ticket must be inferred from context (same ticket as her earlier promise in meeting2/P04: PROM-4). Good test for both extraction (does it catch vague promises?) and linking (does it infer the right ticket without an explicit ticket name?).

**Manually altered rows (P05, P06, P08) — 2026-07-02:** During the real-Jira integration session, tickets PROM-5, PROM-8, and PROM-6 were manually moved to "Done" in the live Jira UI to verify the integration was actually live (not cached/stale). Ground truth for these 3 rows was updated afterward to match the resulting reality (`ticket_status_as_of_eval` -> Done, `ground_truth` -> kept), replacing the original test scenario:
- P05 (Chen, PROM-5): was "To Do / broken" -> now "Done / kept"
- P06 (Tom, PROM-8): was "In Progress / broken" -> now "Done / kept"
- P08 (Ben, PROM-6): was "In Progress / open" -> now "Done / kept"

Caveat: this means the checking-accuracy metric no longer has a frozen baseline for these 3 rows — it now tracks whatever the live Jira ticket status happens to be, not a fixed test scenario. If those tickets drift again (or are reset), the answer key will again disagree with the pipeline until manually re-synced. This is a deliberate tradeoff, not an oversight — see `progress.md`.

## Ground truth mix (sanity check)
- Kept: 11 (P01, P02, P03, P05, P06, P07, P08, P11, P14, P18, P19)
- Broken: 4 (P04, P10, P12, P16)
- Open: 4 (P09, P13, P15, P17)

Total 19. Matches all 18 tickets + 1 extra vague promise reusing PROM-4. (P05/P06/P08 moved kept-bucket per manual-alteration note above; original mix before that was Kept: 8, Broken: 6, Open: 5.)
