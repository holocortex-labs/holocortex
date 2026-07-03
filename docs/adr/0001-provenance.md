# ADR-0001 — Provenance and founding decisions

**Date:** 2026-07-03 · **Status:** accepted

## Context

Holocortex was incubated in a private repository through eight versions
(v0.1–v0.8) before this public release. The private decision trail (seven
ADRs and a capture log) stays private; this ADR summarises the decisions
that shaped what you're looking at.

## Founding decisions (summarised)

1. **Substrate: markdown in git.** Diffable, deterministic, editor-native,
   zero runtime cost, agent-readable as plain files. A rendered wiki is a
   view (scripts/site/), never the source of truth.
2. **Three model tiers.** Local reflex (free, default), cloud planner
   (budgeted, escalation requires a reason from a closed set), local
   auditor (fresh context, fail-closed, gates anything acted on).
3. **Stdlib-only, single-file tools.** No shared libraries between tools;
   small duplication is the accepted price of standalone replaceability.
4. **Guard rails enforced by machinery where possible.** Secret scanning
   in pre-commit, budgets in the router, audit gates as a CLI — written
   rules for the rest.
5. **Drafts never commit.** Model-written knowledge is `.draft` until a
   human reviews and renames. A hallucinated capture poisons the substrate
   future decisions cite; the filename is the safety model.
6. **Config: process env > ~/.config/holocortex/env > localhost.** No site
   name in code, enforced by scripts/test_portability.sh. Config files are
   parsed, never executed.
7. **Model-independence.** CLAUDE.md carries behaviour, conventions, and
   session rituals so any capable model can resume work cold. The project
   survived its first model transition by design.

## Consequences

Public history starts here at v1.0. The incubator's war stories survive as
testing discipline and comments rather than as identifiable history.
