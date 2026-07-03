# Guard Rails

Rules for every agent, model, and script operating under Holocortex. Written once,
referenced everywhere — session prompts link here rather than restating.

## G1 — Read-only by default
Agents start with read access only. Write/execute is granted per-task, explicitly,
and scoped to named paths or MCP tools. A task prompt that doesn't state its write
scope has none.

## G2 — Reversibility before action
No destructive operation without a documented rollback in the same breath.
Config change → prior state captured first. File mutation → git-tracked or backed up.
If rollback can't be stated, the action is escalated to a human, not performed.

## G3 — Dry-run first
Anything touching infrastructure (containers, DNS, NetBox, WoL targets) runs in
observe/plan mode first and presents the diff. Execution is a second, separate step.

## G4 — Auditor gate for planner output
Cloud-planner output that will be *acted on* (scripts, config, infra changes) passes
through the auditor tier — a separate context that checks the output against this
document and the task's stated scope. Chat/analysis output is exempt.

## G5 — No secrets in the substrate
No credentials, tokens, or keys in the repo, captures, or prompts. Secrets live in
the environment (`.env`, excluded by `.gitignore`) or a secret store. Agents caught
a secret in context → capture is redacted before commit.

## G6 — Token budget discipline
Reflex tier answers first. Escalation to cloud requires a routing reason
(see `../specs/router.md`). Sessions that loop >2 escalations on the same problem
stop and capture the blocker instead of burning tokens.

## G7 — Capture is not optional
A session that produced a decision, a fix, or a dead end produces a capture
(`templates/capture.md`) before it ends. Dead ends are captured too — they're the
cheapest guard rail against repeating them.

## G8 — Config drift is a finding
Any divergence observed between documented state (NetBox, ADRs, captures) and
reality is recorded as a finding at time of observation, even if fixing it is
out of scope for the current task.

## Enforcement

Mechanical: G6 via the router daemon (v0.2, `../scripts/router/`); G4 via the
auditor harness (v0.3, `../scripts/auditor/hca`); G5 via the pre-commit secret
scan (v0.3, `../scripts/hooks/` — install per clone with
`git config core.hooksPath scripts/hooks`). By reference: G1, G2, G3, G7, G8 —
every session prompt includes "operate under holocortex/docs/GUARDRAILS.md".
