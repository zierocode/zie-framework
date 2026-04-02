# ADR-040: Input Validation — Bare Brace Guard in Compound Regex

## Status
Accepted

## Context
`input-sanitizer.py` blocked shell injection metacharacters (`;`, `&&`, `||`, backtick, `$()`) via `_DANGEROUS_COMPOUND_RE`. Bare braces `{` and `}` were not included, allowing potential bypass through brace expansion (e.g., `{cmd,arg}` in bash). The omission was discovered during audit item audit-brace-guard.

## Decision
Extend `_DANGEROUS_COMPOUND_RE` pattern to include `[{}]` alongside existing metacharacter guards. This prevents wrapping commands containing bare braces in the confirmation prompt — they fall through to the block path instead.

## Consequences
**Positive:** Eliminates brace-expansion bypass vector. Consistent with principle of denying all shell metacharacters not explicitly permitted.
**Negative:** May block legitimate use of braces in rare JSON-in-command scenarios (acceptable; those should not reach input-sanitizer).
**Neutral:** Two tests added (test_brace_close_not_wrapped, test_brace_open_not_wrapped) to prevent regression.

## Alternatives
Considered: allowlist approach (only permit alphanumeric + safe punctuation). Rejected — too broad a change for a targeted fix. Current denylist extended instead.
