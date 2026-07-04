# Why Holocortex — use cases

Holocortex is a methodology plus a small toolkit for working with LLMs. The
value isn't any single tool; it's what the tools enforce together. Below are
concrete situations it's built for. Each is a real class of problem, not a
hypothetical.

## 1. You're bleeding cloud tokens on questions a local model could answer

**The situation.** You ask an LLM dozens of small things a day — summarise
this, is this regex right, what's the flag for that. Most need no frontier
model, but they all hit your paid API because that's what's wired up. You
have no idea how much of the bill is trivia.

**What Holocortex does.** Every query goes to the local reflex tier first
(`hcr "..."`, or pipe it in with `hcr -` — the stdin path is never
shell-parsed, so pasted text can't smuggle command substitutions past you).
It answers directly and free, or escalates to the cloud
planner *only* with a reason from a closed set (complexity, context size,
tooling, quality) — and every decision is logged. A daily token budget caps
cloud spend; at the limit the router degrades to local answers rather than
surprising you with a bill.

**The payoff.** `hcr-report` shows exactly where tokens went and why anything
escalated. The first time you run it you usually find the reflex tier is
handling 80%+ of traffic for nothing — and you can *see* the exceptions
instead of guessing.

## 2. You solved a hard problem months ago and can't remember how

**The situation.** Late one night you diagnose a gnarly outage, fix it, and
move on. Twelve weeks later it recurs and the fix — and worse, the three dead
ends you ruled out getting there — are gone.

**What Holocortex does.** Every working session that produces a decision, a
fix, or a dead end ends in a capture: a dated markdown note. A local model
drafts it from your session notes (`hcd`), you review and commit. Dead ends
are first-class content, because the cheapest guard rail against repeating a
mistake is the record that you already made it.

**The payoff.** The knowledge base is plain markdown in git — diffable,
searchable, and browsable as a rendered site. Your reasoning outlives the
session it happened in, and future decisions cite it as fact.

## 3. You want an agent to touch real infrastructure without renegotiating trust every time

**The situation.** You'd let an LLM propose config changes, container
restarts, DNS edits — but every session you're re-explaining what it may and
may not do, and you're trusting its own judgement that a plan is safe.

**What Holocortex does.** Guard rails are written once (read-only by default,
reversibility before action, dry-run first, no secrets in the repo) and
referenced everywhere. Planner output that will be *acted on* passes through
a separate auditor (`hca`) that checks it against those rules in a fresh
context and is fail-closed: unparseable verdicts, oversized input, and dead
backends all resolve to FAIL, never a blind pass. Content under review is
fenced as untrusted data so a plan can't talk the auditor into approving it.

**The payoff.** Agent behaviour is bounded and reviewable. The rules are the
same every session because they live in the repo, and the enforcement is
mechanical where it can be — a pre-commit hook that blocks secrets, a
portability check that blocks private hostnames from shippable code.

## 4. Your model changes — or you come back after six months

**The situation.** The model you've been working with is replaced, or
deprecated, or you simply return to a project cold. All the context that
lived in the chat history is gone.

**What Holocortex does.** A binding operating manual (`CLAUDE.md`) plus a
session-bootstrap prompt carry everything a capable model needs to resume:
the guard rails, the conventions, the current deployed state, and the open
threads. The manual is read first; the model states the current state back
to you before doing any work, so you catch a bad handover immediately.

**The payoff.** The project survives losing the specific model that built it.
This is not theoretical — Holocortex was incubated with one model and handed
to another mid-flight, through exactly this mechanism, without a seam.

## 5. The system tells you when something's wrong — and degrades instead of dying

**The situation.** Your GPU box goes to sleep, or a network link drops, or a
service overheats. You want to know *which* thing broke, and you'd rather a
slow answer than no answer.

**What Holocortex does.** `hcr --health` reports each tier independently —
primary reflex, fallback reflex, planner. When the primary GPU backend is
unreachable, an optional CPU fallback — if you choose to deploy one — carries
reflex traffic (slower, but alive), and the health check tells you you're on
it. With no fallback configured, the same health view names the missing tier
instead of leaving you guessing. Errors name the specific backend and its
specific failure rather than a generic "something's down."

**The payoff.** Diagnosis is one command, and failures are graceful. In
practice this surfaced a real hardware finding — a fallback host running hot
under sustained inference, since retired from inference duty — precisely
because the health view made the degraded state visible instead of silent.
Deciding *against* redundancy is a valid outcome too, when the routing log
shows the failure mode isn't costing you anything.

---

New here? Read `CLAUDE.md` at the repo root (the operating manual),
`GUARDRAILS.md` (the rules), and `PROCESSES.md` (the workflows). To verify a
running deployment, see `guides/troubleshooting.md`.