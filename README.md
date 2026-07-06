Most organisations are adopting AI faster than they can govern it. The gap is where the risk lives.
Three questions for anyone shipping AI right now:
- Can anyone actually account for the tokens you're spending — by team, by task, by month?
- When the person who built your best AI workflow leaves, does the reasoning leave with them?
- And how hard would it be to fire your AI vendor? If the answer is "we can't," that's not a strategy — it's a dependency.
Governance, cost accountability, retained reasoning, an open exit. That's the job Holocortex was built to do.

# Holocortex

A local-first methodology + toolkit for working with LLMs: knowledge capture,
guard-railed agents, and a router that spends cloud tokens only when your
local models can't cope. Markdown in git is the single source of truth — the
repo *is* the system, and it works with zero services running.

Not a framework. A working method with enforcement.

## The idea

Working with LLMs ad hoc leaks value three ways: the thought process
evaporates at end-of-session, cloud models answer questions a 4B local model
handles free, and every session renegotiates what the agent may do.
Holocortex closes all three: capture is templated and cheap (a local model
drafts it, you review), routing is local-first by policy with a daily token
budget, and guard rails are written once, referenced everywhere, and — where
possible — enforced by machinery rather than good intentions.

## Architecture

| Tier | Runs on | Role |
|---|---|---|
| **Reflex** | your GPU box (ollama) + a CPU liferaft on an always-on host | fast, free: triage, summaries, capture drafts |
| **Planner** | cloud API, budgeted | design and multi-step reasoning, only on reasoned escalation |
| **Auditor** | local model, fresh context | reviews planner output against the guard rails before anything is acted on |

The router (`hcr`) enforces the escalation policy and logs every decision.
The auditor (`hca`) is fail-closed: unparseable verdicts, dead backends, and
missing guard rails all land on FAIL. The capture drafter (`hcd`) only ever
writes `.draft` files — a human review stands between any model and the
knowledge base. Weekly, the system reviews itself (`hcr-report` + a cron'd
P5 process) and tells you whether it's earning its keep.

## Quickstart

```bash
git clone https://github.com/holocortex-labs/holocortex && cd holocortex
scripts/install-clients.sh                  # tools on PATH, config seeded
vi ~/.config/holocortex/env                 # your endpoints
git config core.hooksPath scripts/hooks     # secret scan on every commit
cd scripts/router && cp ../../holocortex.env.example router.env && vi router.env
docker compose up -d --build                # router live
hcr "hello"                                 # routed locally, zero tokens
```

Read `CLAUDE.md` (binding manual for any model working on this repo),
`docs/GUARDRAILS.md` (the rules), and `docs/PROCESSES.md` (the workflows).

## Layout

```
holocortex/
├── CLAUDE.md            ← operating manual for any model working here
├── docs/                ← guard rails, processes, mind map, ADRs
├── specs/               ← router specification
├── templates/           ← capture, ADR, session-bootstrap templates
├── captures/            ← your knowledge grows here (starts empty)
└── scripts/
    ├── router/          ← local-first router daemon + hcr client + report
    ├── auditor/         ← hca audit gate + model eval harness
    ├── capture/         ← hcd capture drafter
    ├── hooks/           ← pre-commit secret scan
    ├── fallback/        ← CPU ollama liferaft
    ├── site/            ← mkdocs render layer
    └── review/          ← self-running weekly review
```

## Principles

Modular — every component standalone and replaceable. Reversible — nothing
destructive without a stated rollback. Deterministic — same inputs, same
outputs; agents write files, files are diffable. Local-first — cloud tokens
require a logged reason. Fail-closed — when enforcement machinery is unsure,
the answer is no.

## Provenance

Incubated privately through eight versions before this public release; see
`docs/adr/0001-provenance.md` for the decision trail summary. The private
incubator found five of its own bugs in component seams during live testing
with zero unit failures — that story shaped the testing discipline in
CLAUDE.md.

## License

Apache-2.0. See LICENSE.
