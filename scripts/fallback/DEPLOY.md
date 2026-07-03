# Reflex fallback deployment (always-on host)

```bash
cd holocortex/scripts/fallback
docker compose up -d
docker exec holocortex-ollama ollama pull <small-model>   # pick a <=4B model that
docker exec holocortex-ollama ollama list                 # your CPU can actually serve
curl -s http://127.0.0.1:11434/api/tags | head -c 120
```

Then wire it in (both places):
- `~/.config/holocortex/env`: `HCR_OLLAMA_FALLBACK=http://<this-host>:11434`
- router's `router.env`: same line, then `docker compose up -d --force-recreate`
  in `scripts/router/`.

Model note: the fallback model can differ from the primary (`HCR_REFLEX_MODEL`
is requested from whichever backend answers) — so the model you pull here MUST
be tagged identically to `HCR_REFLEX_MODEL`, or pulls of that exact tag will
404. Verify: `./hcr --health` shows `b_reflex_fallback: true`, then stop
ollama on the GPU host and run `hcr "test"` — slow answer beats no answer.

Sizing: expect tens of seconds per reply on CPU. This is a liferaft, not a
speedboat — if fallback latency starts mattering, that's demand evidence for
a second GPU, not for tuning the raft.

Rollback (G2): `docker compose down`; remove the env lines.
