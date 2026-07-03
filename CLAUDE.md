# CLAUDE.md — operating manual for any model working on Holocortex

You are working on Holocortex: a versioned methodology + toolkit for
LLM-assisted work. This file is binding. It exists so the project survives
model changes — you are replaceable; the repo is not.

## Session ritual

**Start:** read `docs/GUARDRAILS.md` (binding), `docs/PROCESSES.md`,
`BACKLOG.md`, and the most recent 2–3 files in `captures/` (they carry the
live context — including the most recent `weekly-review`). Do not start work
without this; re-deriving context that captures already hold wastes the
session.

**End:** every session producing a decision, fix, or dead end ends in a
capture (G7). Draft it with `hcd --topic <slug> --input -` fed from session
notes, or from `templates/capture.md` by hand. Architectural decisions get an
ADR (`templates/adr.md`, numbered, immutable — reversals supersede, never
edit). Dead ends are first-class findings; record them.

## Working with the maintainer

Direct, no filler. Options with trade-offs, not single answers — and when
you recommend one, say why in one line. Challenge over compliance: if the
request conflicts with the guard rails or good sense, say so before
building. Debugging is one step at a time: one command, branch on its
output; evidence beats reasoning. Never narrate ceremony.

## Conventions (non-negotiable)

- **Bash:** Hungarian notation — `str_`, `b_`, `int_`, `file_`, `fn_`,
  `lst_`, `dict_`. `set -euo pipefail`. Beware `[[ cond ]] && cmd` under
  `set -e` (it has bitten twice).
- **Python:** stdlib only, single-file tools, `fn_` function prefixes, same
  Hungarian for variables. Tools must work standalone — no shared libraries;
  small duplication (e.g. the config loader) is the accepted price.
- **Config:** precedence is process env > `~/.config/holocortex/env` >
  localhost. NEVER a site hostname in code or defaults —
  `scripts/test_portability.sh` enforces this and runs before any release.
  Config files are parsed, never sourced/executed. Values may carry inline
  ` #` comments; loaders strip them.
- **Drafts:** anything a model writes into `captures/` is `.md.draft` until
  a human reviews and renames. Drafts never commit. No exceptions.
- **Secrets:** G5. The pre-commit hook scans staged blobs; `.example` files
  and `hcr-allow-secret` are the only escapes. Never weaken the hook.
- **Versioning:** semver-ish; each version = one coherent slice + ADR +
  capture + tests. Commit messages: what changed, what testing found.

## The toolchain (all on PATH via scripts/install-clients.sh)

- `hcr "query"` — local-first router client. `--force-planner` (logged),
  `--context file`, `--stats`, `--health`.
- `hca --scope "..." --output-file plan.md [--capture f]` — auditor gate
  (P3/G4). Exit 0 PASS, 1 FAIL, 2 error. Fail-closed everywhere.
- `hcd --topic slug --input -` — capture drafter. Emits `.md.draft` only.
- `hcr-report [--days 7]` — routing-log analysis; feeds P5.
- Eval: `scripts/auditor/eval/run_eval <model> [...]` — auditor model
  baseline is gemma4:latest 12/12, 0 false-PASS, ~15s/verdict (2026-07-02).
  False-PASS is disqualifying regardless of accuracy.

## Testing discipline

Before any release: all unit suites (router 16, hca 14, eval 4, hcd 6) plus
`scripts/test_portability.sh`. But know the record: live-fire testing found
5 bugs in v0.6 that 40 green units missed, every one in a seam between
components (shell↔config grammar, symlink↔auto-locate, client↔error-detail).
When you fix a bug, extend the test that should have caught it, and prefer
testing through the production pipeline (run_eval imports hca; imitate that).

## Current state (update this section each session)

Maintainers: record here what is deployed where, what was last tested, and
open threads. A model starting a session reads this first; stale content
here is drift and gets fixed before new work starts.

## What Holocortex is for (do not drift from this)

Capture the thought process, spend cloud tokens only when local can't cope,
and keep every guard rail mechanical where possible. When in doubt between
adding capability and increasing adoption/enforcement of what exists, choose
the latter — a system that is built, healthy, and unused is the failure mode
this project exists to avoid.
