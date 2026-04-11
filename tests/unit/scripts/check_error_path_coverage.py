#!/usr/bin/env python3
"""
Coverage gate: verify ≥1 @pytest.mark.error_path test exists per in-scope hook.

Usage (called from Makefile after pytest):
    pytest --collect-only -q -m error_path tests/unit/ 2>/dev/null \
        | python3 tests/unit/scripts/check_error_path_coverage.py

Reads test IDs from stdin (one per line, pytest -q format).
Exits 0 if all in-scope hooks have ≥1 error-path test.
Exits 1 if any hook has 0, printing a summary table.
"""
import sys

HOOKS_IN_SCOPE = [
    "intent-sdlc",
    "session-resume",
    "auto-test",
    "sdlc-compact",
    "safety-check",
    "subagent-context",
    "safety_check_agent",
    "failure-context",
    "session-cleanup",
    "notification-log",
    "reviewer-gate",
    "design-tracker",
    "stop-capture",
]

# Map hook name → keyword that would appear in a test ID covering that hook
_HOOK_KEYWORDS = {h: h.replace("-", "_").replace(".", "_") for h in HOOKS_IN_SCOPE}
# Override ambiguous mappings
_HOOK_KEYWORDS["safety-check"] = "safety_check"
_HOOK_KEYWORDS["safety_check_agent"] = "safety_check_agent"


def main():
    test_ids = sys.stdin.read().splitlines()
    counts = {h: 0 for h in HOOKS_IN_SCOPE}

    for tid in test_ids:
        tid_lower = tid.lower()
        for hook, keyword in _HOOK_KEYWORDS.items():
            if keyword in tid_lower:
                counts[hook] += 1

    missing = [h for h, c in counts.items() if c == 0]

    print("\n=== Hook Error-Path Coverage Gate ===")
    for hook in HOOKS_IN_SCOPE:
        status = "PASS" if counts[hook] > 0 else "FAIL"
        print(f"  [{status}] {hook}: {counts[hook]} error-path test(s)")

    if missing:
        print(f"\nFAIL: {len(missing)} hook(s) missing error-path tests: {', '.join(missing)}")
        sys.exit(1)
    else:
        print(f"\nPASS: all {len(HOOKS_IN_SCOPE)} hooks have ≥1 error-path test")
        sys.exit(0)


if __name__ == "__main__":
    main()
