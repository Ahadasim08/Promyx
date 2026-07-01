# Product

## Register

product

## Users
A single reviewer (the project owner) checking whether the tool's kept/broken/open decisions about meeting promises are correct, using linked Jira ticket evidence. Used briefly, session by session, alongside the Django/React dev servers on localhost. Not multi-tenant, no auth layer.

## Product Purpose
Human-in-the-loop review screen for the Promise Tracker pipeline (Steps 1-3: extract, link, check). Shows every tracked promise grouped by decision, its evidence (linked ticket, ticket status, deadline), and lets the reviewer confirm or override the tool's call. The human's decision is always final; the tool's output is a draft, not an answer.

## Brand Personality
Calm, precise, authoritative. Reads like an audit tool, not a SaaS product: no persuasion, no delight-for-its-own-sake. Every visual choice should make a decision easier to verify, never decorate.

## Anti-references
No strong anti-reference beyond standard anti-slop defaults (no gradient cards, no decorative eyebrows, no chart-heavy analytics look). This is a plain review list, not a metrics dashboard.

## Design Principles
- Evidence before verdict: ticket, status, and deadline must be visible before or alongside the decision, never hidden behind a click.
- The human's override is never lesser than the tool's call. No visual demotion of overridden rows.
- Boring is correct. Resist adding visual interest that doesn't serve faster, more confident review.
- One accent per semantic state (kept/broken/open), used consistently, never for decoration.

## Accessibility & Inclusion
WCAG AA. Standard contrast and keyboard operability are sufficient; no additional stated requirements.
