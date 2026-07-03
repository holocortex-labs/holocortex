#!/usr/bin/env bash
# install-clients.sh — put the Holocortex CLI tools on PATH for this host.
# Usage:
#   scripts/install-clients.sh             install (idempotent)
#   scripts/install-clients.sh --uninstall remove symlinks, keep config (G2)
# Installs: hcr, hcr-report, hca, hcd → ~/.local/bin (symlinks into this repo)
# Seeds:    ~/.config/holocortex/env from holocortex.env.example if absent
set -euo pipefail

str_repo="$(cd "$(dirname "$0")/.." && pwd)"
str_bin_dir="${HCR_INSTALL_BIN:-${HOME}/.local/bin}"
file_site_cfg="${HOME}/.config/holocortex/env"
b_uninstall=false
[[ "${1:-}" == "--uninstall" ]] && b_uninstall=true

# tool name → repo path
declare -A dict_tools=(
    [hcr]="scripts/router/hcr"
    [hcr-report]="scripts/router/hcr-report"
    [hca]="scripts/auditor/hca"
    [hcd]="scripts/capture/hcd"
)

if ${b_uninstall}; then
    for str_tool in "${!dict_tools[@]}"; do
        if [[ -L "${str_bin_dir}/${str_tool}" ]]; then
            rm "${str_bin_dir}/${str_tool}"
            echo "removed ${str_bin_dir}/${str_tool}"
        fi
    done
    echo "config left in place: ${file_site_cfg}"
    exit 0
fi

mkdir -p "${str_bin_dir}"
for str_tool in "${!dict_tools[@]}"; do
    ln -sf "${str_repo}/${dict_tools[${str_tool}]}" "${str_bin_dir}/${str_tool}"
    echo "linked ${str_tool} -> ${dict_tools[${str_tool}]}"
done

if [[ ! -f "${file_site_cfg}" ]]; then
    mkdir -p "$(dirname "${file_site_cfg}")"
    cp "${str_repo}/holocortex.env.example" "${file_site_cfg}"
    chmod 600 "${file_site_cfg}"
    echo ""
    echo "seeded ${file_site_cfg} from example — EDIT IT NOW (real hostnames):"
    echo "  vi ${file_site_cfg}"
else
    echo "config exists: ${file_site_cfg} (left untouched)"
fi

case ":${PATH}:" in
    *":${str_bin_dir}:"*) ;;
    *) echo "WARNING: ${str_bin_dir} not on PATH — add it to your shell rc" ;;
esac

# reachability check, best effort
str_url="$(grep -E '^HCR_ROUTER_URL=' "${file_site_cfg}" 2>/dev/null | cut -d= -f2- || true)"
if [[ -n "${str_url}" && "${str_url}" != *example* ]]; then
    if curl -sf --max-time 3 "${str_url}/health" >/dev/null 2>&1; then
        echo "router reachable at ${str_url}"
    else
        echo "WARNING: router NOT reachable at ${str_url} (daemon down, or config wrong)"
    fi
else
    echo "NOTE: HCR_ROUTER_URL still the example value — reachability not checked"
fi
