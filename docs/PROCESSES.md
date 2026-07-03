# Processes

The defined workflows. Each is small, composable, and file-based.

## P1 — Capture
**Trigger:** any session producing a decision, fix, insight, or dead end.
**Steps:** copy `templates/capture.md` → `captures/YYYY-MM-DD-topic.md`; fill
context / findings / decision / rollback / links; commit. Scripted (v0.5):
`scripts/capture/hcd --topic x --input transcript.txt` emits a .md.draft via
the reflex tier; review, edit, rename to .md, commit. Drafts never commit
as-is — see docs/guides/draft-review.md for the review checklist.
**Output:** one dated markdown file. The wiki is the accumulation of these.

## P2 — Route
**Trigger:** any LLM query.
**Steps:** query goes to the reflex tier first. Reflex either answers or emits an
escalation with a stated reason (complexity, context size, tool need). Only then
does the query reach a cloud planner. See `../specs/router.md` for the contract.
**Output:** answer + routing record (tier used, reason if escalated).

## P3 — Audit
**Trigger:** planner output that will be acted on (G4).
**Steps:** output + task scope + GUARDRAILS.md handed to a fresh context (local
model where sufficient). Auditor returns PASS, or FAIL with the violated rule.
FAIL → revise or escalate to human. Never self-audit in the same context.
Scripted (v0.3): `scripts/auditor/hca --scope "..." --output-file plan.md
--capture captures/x.md` — exit 0 PASS, else FAIL.
**Output:** audit verdict, attached to the capture.

## P4 — Decide (ADR)
**Trigger:** any choice with architectural consequence — technology, topology,
process change.
**Steps:** copy `templates/adr.md` → `docs/adr/NNNN-title.md`; record context,
options considered, decision, consequences. ADRs are immutable once merged;
reversals get a new ADR that supersedes.
**Output:** numbered ADR.

## P5 — Review (weekly, ~15 min)
**Trigger:** scheduled, weekly.
**Steps:** run `scripts/router/hcr-report` for the week's routing picture; skim
the week's captures; promote recurring themes into MINDMAP.md or an ADR; groom
BACKLOG.md; check for drift findings (G8) left unresolved.
**Output:** updated mind map / backlog; the repo stays a live system rather than
a write-only log.

## Composition

A typical working session: **P2** routes the queries → work happens → **P3** audits
anything actionable → **P1** captures the outcome → (if a real decision was made)
**P4** records it. **P5** keeps the whole thing coherent over time.
