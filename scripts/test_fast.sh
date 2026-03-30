#!/usr/bin/env bash
# scripts/test_fast.sh
# Run pytest on changed files only. Falls back to full suite when a .py
# source file has no matching test file.
#
# Environment overrides (for tests):
#   _FAST_DRY_RUN=1        Print resolved args instead of running pytest
#   _FAST_CHANGED="a b c"  Override git diff output (space-separated paths)

set -uo pipefail

TESTS_UNIT="tests/unit"
FULL_SUITE_CMD="make test-unit"

# ── Discover changed files ────────────────────────────────────────────────────
if [[ -n "${_FAST_CHANGED:-}" ]]; then
  # Test override: space-separated list
  IFS=' ' read -r -a CHANGED <<< "${_FAST_CHANGED}"
elif git rev-parse --verify HEAD >/dev/null 2>&1; then
  CHANGED=()
  while IFS= read -r line; do [[ -n "$line" ]] && CHANGED+=("$line"); done \
    < <(git diff --name-only HEAD 2>/dev/null)
  while IFS= read -r line; do [[ -n "$line" ]] && CHANGED+=("$line"); done \
    < <(git diff --name-only --cached 2>/dev/null)
else
  echo "[test-fast] No HEAD ref found — falling back to full suite"
  exec ${FULL_SUITE_CMD}
fi

# ── Map changed files → test files ───────────────────────────────────────────
# Mapping rules:
#   hooks/*.py  → test_hooks_<base>.py (preferred) | test_<base>.py | fallback
#   *.py        → test_<base>.py | fallback
#   *.md        → skip (no unit tests for Markdown)
#   other       → skip gracefully (not a .py source file — no fallback)

TEST_PATHS=()
NEEDS_FULL_FALLBACK=0

for f in "${CHANGED[@]:-}"; do
  [[ -z "$f" ]] && continue

  case "$f" in
    *.md)
      echo "[test-fast] skip (markdown): $f"
      continue
      ;;
    hooks/*.py)
      base=$(basename "$f" .py | tr '-' '_')
      candidate1="${TESTS_UNIT}/test_hooks_${base}.py"
      candidate2="${TESTS_UNIT}/test_${base}.py"
      if [[ -f "$candidate1" ]]; then
        TEST_PATHS+=("$candidate1")
        echo "[test-fast] mapped: $f → $candidate1"
      elif [[ -f "$candidate2" ]]; then
        TEST_PATHS+=("$candidate2")
        echo "[test-fast] mapped: $f → $candidate2"
      else
        echo "[test-fast] no test match for $f — fallback to full suite"
        NEEDS_FULL_FALLBACK=1
      fi
      ;;
    *.py)
      base=$(basename "$f" .py)
      candidate="${TESTS_UNIT}/test_${base}.py"
      if [[ -f "$candidate" ]]; then
        TEST_PATHS+=("$candidate")
        echo "[test-fast] mapped: $f → $candidate"
      else
        echo "[test-fast] no test match for $f — fallback to full suite"
        NEEDS_FULL_FALLBACK=1
      fi
      ;;
    *)
      # Non-.py, non-.md (VERSION, .env, config files) — skip gracefully
      echo "[test-fast] skip (unmapped type): $f"
      continue
      ;;
  esac
done

# ── Execute ───────────────────────────────────────────────────────────────────
if [[ "$NEEDS_FULL_FALLBACK" -eq 1 ]]; then
  echo "[test-fast] Running full suite (fallback triggered)"
  if [[ "${_FAST_DRY_RUN:-0}" == "1" ]]; then
    echo "DRY_RUN: ${FULL_SUITE_CMD}"
    exit 0
  fi
  exec ${FULL_SUITE_CMD}
fi

PYTEST_ARGS=("--lf" "-q" "--tb=short" "--no-header")
if [[ "${#TEST_PATHS[@]}" -gt 0 ]]; then
  PYTEST_ARGS+=("${TEST_PATHS[@]}")
fi

if [[ "${_FAST_DRY_RUN:-0}" == "1" ]]; then
  echo "DRY_RUN: python3 -m pytest ${PYTEST_ARGS[*]}"
  exit 0
fi

# Run pytest; treat exit code 5 (no tests collected) as success for fast loop
python3 -m pytest "${PYTEST_ARGS[@]}"; rc=$?
[[ $rc -eq 5 ]] && exit 0  # "no tests collected" is OK in fast loop
exit $rc
