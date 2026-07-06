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

## How Holocortex services it  *(internal — omit from public flag-planting copy)*

Decision debt is the problem statement; Holocortex is how you pay it down at organisational scale.
The four failure modes Holocortex targets are decision debt made concrete:

1. **Retained reasoning** — the "why" is captured as decisions happen, not reconstructed after the
   person leaves. (Directly the decision-debt principal.)
2. **Token accountability** — the spend behind AI-made decisions is attributable, not a black hole.
3. **Governance keeping pace with adoption** — decisions are made *inside* a governed boundary.
4. **Vendor independence** — an open exit, so the record isn't hostage to one provider.

Sequencing: **own the concept in public first, name the product second.** The concept is the
category; the product is the answer to "so how do I pay it down?" — a question people bring to you
once the term is yours. Public copy below names no product on purpose.

---

## Content kit

### A. LinkedIn comment — flag-plant (no product name)

> The CodeHealth-over-perplexity result is the part people will underrate — "code that confuses
> humans confuses LLMs" is the thesis in a line.
>
> Structure is one foundation the agent stands on. The other is the reasoning behind it — the
> constraints and trade-offs a maintainability score can't see, that walk out the door when people
> move on. Call it decision debt: technical debt's sibling, measuring the "why" you didn't keep.
> Clean codebase, no record of why, and an agent optimises away a constraint nobody wrote down.
> Fast, and wrong.
>
> "Where would you not point an agent today?" has a twin: where would you point one, but it can't
> see why the last call was made? Discipline beats intelligence — applied to the decisions, not
> just the code.

### B. Standalone post — claim the term (no product name)

> **Your codebase has a second debt, and it isn't in the code.**
>
> There's a study going round showing healthy code is also AI-friendly code: LLMs break fewer tests
> refactoring clean code than messy code. Discipline beats intelligence. Correct, and underrated.
>
> But code health is only one of two foundations an agent stands on. The other shows up in no
> maintainability score: the reasoning behind the code. Why this pattern, why that constraint, what
> got rejected and what it cost. When that lives only in people's heads, it leaves when they do.
>
> Technical debt has a sibling. Call it **decision debt** — the accumulated cost of decisions made
> with no recorded rationale. You've always paid interest on it. In a codebase shared with agents
> the rate jumps: an agent on clean code with no record of *why* will confidently refactor straight
> through a constraint nobody documented.
>
> Engineers already have the instrument — the architecture decision record. Decision debt is just
> the name for what you owe when you don't keep them. Most orgs measure code health now. Almost none
> can tell you whether they could reconstruct why they are where they are.
>
> Before your next agent rollout: where in your system can no one tell you *why*? That's not a
> documentation gap. That's your decision debt — and it's the part of your AI strategy nobody's
> pricing.

### C. Follow-up post — pivot to Holocortex (publish ~T+1–2 weeks, once the term has traction)

> A couple of weeks ago I put a name to something: **decision debt** — the cost of decisions made
> with no recorded rationale, the "why" that leaves when people do. The response told me it's a
> live nerve.
>
> Here's what I didn't say then. Naming a debt is easy; servicing it is the work. And the orgs I
> talk to fail it the same three ways: the rationale lives in people's heads, the spend behind AI
> decisions is unaccountable, and the whole thing quietly depends on one vendor they can't leave.
>
> That's what we've been building **Holocortex** to fix: capture the reasoning as it happens,
> account for every token, keep governance in step with adoption, and keep the exit open. Decision
> debt is the problem. Holocortex is how you service it.
>
> [CTA / link]

---

## Positioning map

The category bet, stated plainly:

> technical debt : CodeScene  ::  **decision debt : Holocortex**

CodeScene owns *measuring code health*. The open category is *governing decision health*. Own the
word "decision debt" and Holocortex is the default answer to it — category ownership, not feature
competition.

## Tags

`#DecisionDebt #TechnicalDebt #AIGovernance #AIAugmentedDelivery #ArchitectureDecisionRecords #AgenticAI`

## Prior art referenced (so the boundary is defensible)

- Technical debt — Ward Cunningham, 1992.
- Cognitive debt — getDX, 2026.
- Intent debt — arXiv 2603.22106, 2026.
- Prompt/retrieval/evaluation debt — VentureBeat, 2026.
- Code-health ↔ AI-refactoring-success — CodeScene / Lund University, 2026.