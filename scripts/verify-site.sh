#!/usr/bin/env bash
# The test harness for the self-hosted site. Builds, then asserts invariants.
# Every assertion here corresponds to a success criterion in
# docs/superpowers/specs/2026-07-28-selfhost-migration-design.md
set -uo pipefail

FAILED=0
pass() { echo "  PASS  $1"; }
fail() { echo "  FAIL  $1" >&2; FAILED=1; }
check() { if [ "$1" = "0" ]; then pass "$2"; else fail "$2"; fi }

echo "Building..."
if hugo --quiet --destination public; then
  pass "hugo build exits 0"
else
  fail "hugo build exits 0"
  echo "Build failed, cannot run further assertions." >&2
  exit 1
fi

echo
echo "Results:"
if [ "$FAILED" -eq 0 ]; then echo "ALL ASSERTIONS PASSED"; else echo "THERE WERE FAILURES" >&2; fi
exit "$FAILED"
