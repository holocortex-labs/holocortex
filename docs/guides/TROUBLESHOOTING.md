# Guide: manual tests & troubleshooting

A catalogue of checks you can run by hand, what each one tells you, and what a
healthy result looks like. Most of these were born diagnosing a real problem
between versions — the "why" matters as much as the command, because the point
is knowing which layer is at fault, not just that something is wrong.

Paths and hosts use environment variables and placeholders (`<gpu-host>`,
`<always-on-host>`) — substitute your own, or rely on your configured
`~/.config/holocortex/env`.

## Reflex tier — is local inference alive?

**`hcr --health`**
Reports each tier independently. `b_reflex_primary` is your GPU backend,
`b_reflex_fallback` the optional CPU liferaft (false simply means you have
not deployed one), `b_planner_configured` the cloud key.
*Why:* the single most useful check. It distinguishes "primary down, running
slow on fallback" from "everything's fine" from "reflex tier entirely dead."
If primary is false but fallback true, `hcr` still works — just slowly.
*Healthy:* `b_ok: true` and at least one reflex backend true.

**`curl -sf --max-time 3 ${HCR_OLLAMA_PRIMARY}/api/tags`**
Hits ollama directly, bypassing the router. Returns the installed model list.
*Why:* separates "the host/mesh is down" from "ollama is up but the model the
router wants isn't installed." A router error of "no reflex backend reachable"
has been, in the past, actually a model-not-found 404 in disguise — this
tells them apart. Confirm the tag in `HCR_REFLEX_MODEL` appears in the output.
*Healthy:* JSON with your model listed.

**`curl -s ${HCR_OLLAMA_PRIMARY}/api/ps`**
Shows models currently resident in memory.
*Why:* distinguishes "up but cold" (first query will be slow while the model
loads) from "warm." Useful before timing anything.

## End-to-end — does routing actually work?

**`hcr "what is 2+2"`**
A trivial query that must stay local.
*Why:* proves the whole path — client, daemon, backend, log write — end to
end, at zero cost.
*Healthy:* the answer, then `tier=reflex reason=reflex_direct tokens_cloud=0`.

**`hcr --stats`**
Today's token spend against budget.
*Why:* catch anomalies. If it shows cloud tokens you can't account for,
something escalated that you didn't expect — investigate via the routing log.
*Healthy:* spend consistent with what you actually asked.

**`hcr-report --days 7`**
Tier split, escalation reasons, reflex ratio from the routing log.
*Why:* the weekly review input. A high reflex ratio means the local-first
policy is earning its keep; the escalation-reason breakdown shows whether
cloud spend is going where you'd expect.

## Security & degradation

**Auth enforced:** `curl -s -X POST ${HCR_ROUTER_URL}/route -H 'Content-Type: application/json' -d '{"str_query":"test"}'`
Raw POST with no auth token.
*Why:* if you've set `HCR_AUTH_TOKEN`, this confirms the router actually
rejects unauthenticated callers rather than just claiming to. A bare curl
getting through means auth isn't wired up.
*Healthy (with auth on):* `401 missing or bad X-HC-Token`. `hcr` itself still
works because it sends the token from config.

**Unknown-flag guard:** `hcr --status`
*Why:* `--status` is not a real flag. It should error, not silently become an
LLM query. (It once did the latter — "--status" got answered "Operational" by
the model, which looks like a status readout but is pure improvisation and can
even cost tokens if it escalates.)
*Healthy:* `hcr: unknown option: --status` and usage.

**Fallback failover (only if you deploy a fallback):**
`HCR_OLLAMA_PRIMARY=http://127.0.0.1:9 HCR_OLLAMA_FALLBACK=${real_fallback} hca --scope "edit BACKLOG.md only" --output-file /tmp/plan.md`
Points the primary at a dead port so the fallback must carry the request.
*Why:* proves the liferaft works while you're calm, not during an outage. On
CPU it will be slow. A fallback is optional — running without one is a valid
configuration, and one caution from real use: sustained CPU inference is a
poor fit for small passively-cooled hosts, especially ones carrying other
duties (a fanless box running your DNS should not also run your models).
*Healthy:* a verdict returns (exit 0/1), sourced from the fallback.

**Shell expansion in queries:** `hcr 'what does `ls -l /dev/null` do?'`
Note the SINGLE quotes.
*Why:* inside double quotes your shell executes `` `...` `` and `$(...)`
*before* hcr sees the string — with your privileges, and the expanded output
rides the query (and could reach the cloud planner on escalation). The
symptom: the answer describes your actual files or command output instead of
the command itself. Deliberate substitution is a feature
(`hcr "explain: $(tail -5 err.log)"`); for pasted or untrusted text use
single quotes, or feed stdin — `some-command | hcr -` or a quoted heredoc
(`hcr - <<'EOF'`) — which is never shell-parsed.
*Healthy:* the model discusses the literal command text, not its output.

**hcr-report finds no log:** `hcr-report` says `no log at .../.local/bin/data/routing.jsonl`
*Why:* versions before v1.2.4 resolved the default log path beside the
`~/.local/bin` symlink instead of the real script (fixed with `realpath`).
If you see a `.local/bin` path in the error, update; or point it explicitly
with `--log` or `HCR_LOG_FILE`.
*Healthy:* bare `hcr-report` finds the routing log beside the daemon's data
directory.

## Auditor quality

**`scripts/auditor/eval/run_eval ${HCR_REFLEX_MODEL}`**
Scores the auditor model against known-verdict cases.
*Why:* the auditor is only as good as its model's judgement. Re-run whenever
you change `HCA_AUDITOR_MODEL` or the model library updates. The number that
matters is **false-PASS** — a model that waves violations through is
disqualified regardless of overall accuracy.
*Healthy:* high correct count, **zero false-PASS**. The current baseline model
scores full marks with no false-PASS in roughly 15s per verdict.

## Enforcement gates (run before committing / exporting)

**`scripts/hooks/test_hook.sh`**
Exercises the pre-commit hook in a throwaway repo.
*Why:* confirms the secret scan and the draft-marker block both fire. This
harness once caught a real hook bug (a credential pattern beginning with
dashes was parsed by grep as options and silently skipped).
*Healthy:* all cases pass.

**`scripts/test_portability.sh`**
Greps shippable code and the example config for private hostnames.
*Why:* nothing site-specific should reach the public export. Run before any
export. It has caught real leaks on its first pass.
*Healthy:* "portability OK."

**Export dry-run:** `scripts/export/export-public.sh /tmp/export-check`
Produces the public tree and self-verifies.
*Why:* the export must exclude private-only material (internal reviews,
private ADRs) — a content scan for forbidden *terms* is not the same guarantee
as a *path* policy, and both are needed. The pipeline fails closed if a known
private path survives.
*Healthy:* "export ready"; and manually confirm `/tmp/export-check` contains
no internal review or private ADR files.

## Git & publishing safety

**`git ls-files | grep -E 'router\.env$|routing\.jsonl|\.key$'`**
*Why:* confirms no secrets or logs got tracked. Should never return anything.
*Healthy:* empty.

**`git log origin/main..HEAD --oneline`**
*Why:* shows commits made but not pushed. Before handing off or trusting the
remote as backup, this should be empty.
*Healthy:* empty (fully pushed).

**Verifying public-repo state (purges, leaks, or just "what does it serve?"):**
fresh `git clone`, then `git ls-remote`, `git rev-parse`, `git cat-file -e <ref>:<path>`
*Why:* HTTP surfaces — the hosting API *and* the raw CDN — have served state
more than a day stale, in both directions: showing a purged file as still
present, and equally capable of hiding a present one. They are hints, never
evidence. Only git-native commands against a real clone answer what the
remote actually serves. Check `rev-parse` output matches `ls-remote` before
trusting a `cat-file` verdict — `cat-file -e` also "fails" when the object
simply isn't fetched, which reads as a false "clean". Note that
`git push --force --tags` does *not* reliably move an existing remote tag —
push the tag ref explicitly (`git push origin <tag> --force`).
*Healthy:* refs match the remote's advertisement and `cat-file -e` agrees
with expectation on every advertised ref.

## Services

**`docker ps --filter name=holocortex --format '{{.Names}} {{.Status}}'`**
*Why:* are the router, site, and any fallback containers up.
Then `docker logs <name> --tail 20` for a crashing one — the daemon prints
`listening on :<port>` when healthy, or a specific startup error.