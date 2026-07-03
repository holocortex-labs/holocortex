#!/usr/bin/env bash
# p5-weekly.sh — the P5 review runs itself (v0.6).
# Gathers the week's routing report + capture inventory, drafts the review
# capture via hcd. Output is a .draft — the human skim IS still the review;
# this script just kills the blank-page cost.
# Cron (Mondays 07:00): 0 7 * * 1 <repo-path>/scripts/review/p5-weekly.sh
set -euo pipefail

str_repo="$(cd "$(dirname "$0")/../.." && pwd)"
file_log="${HCR_LOG_FILE:-${str_repo}/scripts/router/data/routing.jsonl}"
str_date="$(date -u +%F)"

fn_gather() {
    echo "# P5 weekly review material — ${str_date}"
    echo ""
    echo "## Routing report (7 days)"
    "${str_repo}/scripts/router/hcr-report" --log "${file_log}" --days 7 2>&1 || true
    echo ""
    echo "## Captures this week"
    find "${str_repo}/captures" -name '*.md' -mtime -7 -exec basename {} \; | sort
    echo ""
    echo "## Unreviewed drafts (G7 debt — should be zero)"
    find "${str_repo}/captures" -name '*.draft' -exec basename {} \; | sort
    echo ""
    echo "## Backlog open items"
    grep -c '^\- \[ \]' "${str_repo}/BACKLOG.md" | xargs echo "open items:"
    echo ""
    echo "## Container health"
    docker ps --filter name=holocortex --format '{{.Names}} {{.Status}}' 2>/dev/null || echo "docker unavailable"
}

fn_gather | "${str_repo}/scripts/capture/hcd" --topic weekly-review --input - --date "${str_date}"
