# Router deployment (always-on host)

```bash
cd holocortex/scripts/router
cp ../../holocortex.env.example router.env && vi router.env && chmod 600 router.env   # key + hostnames; 600 per G5
docker compose up -d --build
curl -s http://127.0.0.1:8377/health
```

Client (any mesh host): copy `hcr` into PATH.
`hcr "question"` · `hcr --context notes.md "summarise"` · `hcr --stats`

Tests: `python3 -m unittest test_router -v` (no network or keys needed).

Rollback (G2): `docker compose down` — routing log in `data/` is the only state.
