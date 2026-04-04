---
adr: 041
title: Pre-commit Hook Simplified to Stub
status: Accepted
date: 2026-04-03
---

## Status

Accepted

## Context

The `.githooks/pre-commit` hook grew to 45 lines implementing three checks:
version-drift detection (plugin.json vs VERSION), bandit SAST scan, and
markdownlint validation. All three depend on optional tools (`bandit`, `npx`)
that are not guaranteed to be present in every developer environment. Absent
tools caused the hook to exit non-zero, blocking commits entirely. This defeated
the purpose of a local commit gate and added friction without a safety guarantee.

## Decision

Replace the 45-line pre-commit hook with a 2-line pass-through stub (`echo
"Pre-commit hook placeholder"; exit 0`). Version-drift, bandit SAST, and
markdownlint checks are relocated to CI (`make test-ci` / GitHub Actions), where
tool availability is controlled and guaranteed.

## Consequences

**Positive:**
- Commits are never blocked by missing optional tooling (`bandit`, `npx`).
- Local commit latency drops to near-zero; TDD RED/GREEN loop is unimpeded.
- CI remains the authoritative gate — checks still run, just not locally.
- Stub is explicit and honest: no silent skip logic, no conditional installs.

**Negative:**
- Version-drift, SAST, and lint violations are no longer caught at commit time;
  they surface in CI instead, adding a round-trip before feedback.
- Developers who push without running `make test-ci` locally may get CI failures
  they would have caught immediately before.

**Neutral:**
- ADR-002 (markdownlint pre-commit gate) is superseded by this decision for the
  zie-framework repo; the `.pre-commit-config.yaml` approach it introduced is
  similarly retired in favor of CI-only enforcement.
- The stub can be expanded again in the future if a zero-dependency pre-commit
  check is warranted (e.g., a pure-bash version check).

## Alternatives Considered

- **Conditional skip on missing tools** — check for `bandit`/`npx` and skip
  gracefully. Rejected: adds complexity, still silently omits checks without
  signaling anything to CI.
- **Install tools in setup target** — `make setup` pins bandit and npx.
  Rejected: forces optional tool installation on all contributors; npx requires
  Node, which is not a stated dependency of zie-framework.
- **Keep hook, move to `pre-push`** — run heavier checks only on push.
  Rejected: pre-push hooks have the same optional-tool availability problem and
  `make test-ci` already covers this case before a push.
