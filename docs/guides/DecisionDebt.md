# Decision Debt

> **Decision debt** — the accumulated cost of decisions made without a recorded rationale:
> the context, the alternatives weighed, and the constraints they satisfied. You have always
> paid interest on it. In a system shared with AI agents, the rate jumps — an agent will
> confidently refactor straight through a constraint that only ever lived in someone's head.

| | |
|---|---|
| **Term** | Decision debt |
| **Named by** | Marc Loftus |
| **Date** | 2026-07-06 |
| **Status** | Public coinage — definition of record |
| **Canonical record** | This file's git commit (see repo history) |
| **Related project** | Holocortex |

---

## Why now

Technical debt was always a cost-of-delivery problem: it slowed *humans* down. Decision debt
used to behave the same way — mild, deferred, tolerable. AI agents change its character.

An agent acting on a clean codebase with no record of *why* the code is the way it is does not
slow down. It acts — fast, and sometimes confidently wrong — reversing constraints nobody wrote
down. Technical debt taxed velocity. Decision debt, in an agent-shared system, taxes correctness.
Low code health makes more-AI-more-risk (CodeScene/Lund, 2026). Low *decision* health does the
same, one layer up, and no maintainability score can see it.

## What it is NOT (defensible boundary)

The 2026 vocabulary is crowded. Decision debt earns its place by being the most operational,
business-legible member of the family — and by mapping onto an instrument engineers already use.

- **Technical debt** (Cunningham, 1992) — not-quite-right *code* deferred. Decision debt is about
  the *choices*, not the code they produced.
- **Cognitive debt** (getDX, 2026) — *humans* losing understanding of AI-generated components.
  That's a comprehension problem. Decision debt is a *record* problem: it exists even if everyone
  currently understands the system, because understanding is not durable and does not transfer.
- **Intent debt** (arXiv 2603.22106) — the *forward* spec: goals/constraints you never articulated
  for how the system *should* evolve. Decision debt is the *backward* trail: the choices you already
  made and did not capture.

> **One-line defence** (for the "isn't that intent/cognitive debt?" reply):
> Cognitive debt is humans losing understanding. Intent debt is the spec you never wrote.
> Decision debt is the choices you *did* make and didn't record. Same balance sheet, different
> liability. ADRs are the instrument; decision debt is what you owe when you don't keep them.

## The instrument

The architecture decision record already exists to prevent this. Decision debt is simply the
name for the liability an org carries when it doesn't keep them — or keeps them for code and
nowhere else. Naming the liability is what lets leadership *price* it; "write more ADRs" never
made it onto a board slide, "what is our decision debt?" can.
