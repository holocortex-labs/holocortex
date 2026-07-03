#!/usr/bin/env bash
# test_portability.sh — scripts/ and example config must be site-agnostic.
# Docs describing the real deployment (README, MINDMAP, specs, captures, ADRs)
# are exempt by design: config != documentation (ADR-0006).
set -euo pipefail
str_repo="$(cd "$(dirname "$0")/.." && pwd)"
lst_forbidden='REPLACE-your-mesh-domain|REPLACE-your-hostnames'  # your private names here
int_hits=0
while IFS= read -r str_hit; do
    echo "PORTABILITY VIOLATION: ${str_hit}"
    int_hits=$((int_hits + 1))
done < <(grep -rniE "${lst_forbidden}" "${str_repo}/scripts" "${str_repo}/holocortex.env.example" \
         --exclude-dir=__pycache__ --exclude-dir=data --exclude-dir=models --exclude=test_portability.sh --exclude='*.env' 2>/dev/null || true)
if (( int_hits > 0 )); then
    echo "${int_hits} site-specific reference(s) in scripts/ or example config"
    exit 1
fi
echo "portability OK — scripts/ and example config are site-agnostic"
