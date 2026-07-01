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

## Ground truth mix (sanity check)
- Kept: 8 (P01, P02, P03, P07, P11, P14, P18, P19)
- Broken: 6 (P04, P05, P06, P10, P12, P16)
- Open: 5 (P08, P09, P13, P15, P17)

Total 19. Matches all 18 tickets + 1 extra vague promise reusing PROM-4.
