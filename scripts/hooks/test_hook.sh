#!/usr/bin/env bash
# Test harness for the pre-commit secret scan. Builds a throwaway git repo.
# Fixture secrets are concatenated at runtime — this file never matches at rest.
set -euo pipefail
str_hook_src="$(cd "$(dirname "$0")" && pwd)/pre-commit"
str_tmp="$(mktemp -d)"
trap 'rm -rf "${str_tmp}"' EXIT
cd "${str_tmp}"
git init -q -b main
git config user.name t; git config user.email t@t
mkdir -p scripts/hooks && cp "${str_hook_src}" scripts/hooks/pre-commit
git config core.hooksPath scripts/hooks

int_pass=0; int_fail=0
fn_expect() { # str_name int_expected_rc
    local str_name="$1" int_expected="$2" int_rc=0
    git commit -qm "${str_name}" >/dev/null 2>&1 || int_rc=$?
    if [[ "${int_rc}" -eq "${int_expected}" ]]; then
        echo "PASS ${str_name}"; int_pass=$((int_pass+1))
        if [[ "${int_rc}" -ne 0 ]]; then git reset -q; fi  # unstage blocked content
    else
        echo "FAIL ${str_name} (rc=${int_rc}, wanted ${int_expected})"; int_fail=$((int_fail+1))
        git reset -q
    fi
}

str_fake_ant="sk-ant-""api03-abcdefghijklmnopqrstuvwx"
str_fake_aws="AKIA""ABCDEFGHIJKLMNOP"
str_fake_hdr="-----BEGIN ""PRIVATE KEY-----"

echo "nothing to see" > clean.txt; git add clean.txt
fn_expect "clean_file_commits" 0

echo "key=${str_fake_ant}" > leak.txt; git add leak.txt
fn_expect "anthropic_key_blocked" 1

echo "HCR_ANTHROPIC_API_KEY=${str_fake_ant}" > router.env.example; git add router.env.example
fn_expect "example_file_allowed" 0

echo "key=${str_fake_ant} # hcr-allow-secret" > doc.md; git add doc.md
fn_expect "inline_allow_marker" 0

echo "${str_fake_hdr}" > key.pem.txt; git add key.pem.txt
fn_expect "private_key_header_blocked" 1

echo "aws=${str_fake_aws}" > aws.txt; git add aws.txt
fn_expect "aws_key_blocked" 1

echo "GUARDRAILS.md talks about api_key patterns in prose" > prose.md; git add prose.md
fn_expect "prose_mention_not_flagged" 0

echo "----"
echo "${int_pass} passed, ${int_fail} failed"
exit "${int_fail}"
