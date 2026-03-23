# safety-check regex patterns bypassed by whitespace variations

**Severity**: Critical | **Source**: audit-2026-03-24

## Problem

`safety-check.py` regex patterns can be evaded with simple whitespace tricks:
- `rm  -rf  ./` (double spaces) passes through `rm\s+-rf\s+\.`
- `git push -u origin main` passes through the push guard
- Core safety hook fails at its own stated job

## Motivation

The safety hook is the only mechanism blocking dangerous Bash commands from
Claude. If it can be bypassed trivially, all downstream protection is gone.
Users trust it to catch `rm -rf` variants and force-push attempts. Pattern
normalization (collapse whitespace before matching) and broader patterns are
needed.
