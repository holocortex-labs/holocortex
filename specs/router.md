# Router Specification

**Status: implemented v0.2 — scripts/router/ (ADR-0002)**

Local-first LLM router. Purpose: spend cloud tokens only when the reflex tier
demonstrably can't do the job (GUARDRAILS G6).

## Contract

```
route(str_query, str_context) -> { str_tier, str_answer, str_reason, int_tokens_cloud }
```

Deterministic given the same inputs and policy version. Every call appends one
line to a routing log (JSONL) — tier, reason, timestamp, cloud tokens spent.

## Tiers

| Tier | Backend | Selected when |
|---|---|---|
| `reflex` | ollama on the GPU host (phi3 / qwen), fallback CPU on the always-on host | default |
| `planner` | Claude / GPT-4.1 via API | reflex emits escalation |
| `human` | the human | guard-rail conflict, >2 escalations, irreversible action |

## Escalation reasons (closed set)

`complexity` — multi-step reasoning beyond reflex capability (reflex self-assesses,
then a cheap heuristic double-checks: query length, code presence, tool-call need).
`context` — required context exceeds reflex window.
`tooling` — task needs MCP tools the reflex harness doesn't expose.
`quality` — reflex answered but confidence below threshold; planner verifies.

Escalation without one of these reasons is a policy violation and is logged as such.

## Budget

Per-day cloud token budget, set in `router.env` (not committed). At 80% the router
warns; at 100% it returns reflex-only answers plus the refusal reason. Budget resets
daily; overrides are explicit (`--force-planner`) and logged.

## Placement

Router daemon on the always-on host, reachable over the mesh at
the mesh name of the always-on host. Inference backends addressed by mesh name so the GPU host
can sleep without breaking reflex service (falls back to the always-on host CPU model, slower
but alive).

## Non-goals (v0.2)

No streaming, no multi-turn state in the router itself (sessions own their context),
no automatic model download. Additions go through an ADR.

## Naming

Scripts follow repo bash convention: `str_`, `b_`, `int_`, `file_`, `fn_` prefixes.
