---
id: ADR-062
title: Once-per-session behavior via /tmp flags
status: accepted
date: 2026-04-12
---

## Context

Multiple Sprint B features (compact-hint tiers, design-tracker, stop-capture) need to fire once per session and suppress on repeat invocations. Options: persistent config, in-memory state, or `/tmp` flags.

## Decision

Use `/tmp` flags with session-scoped names (`zie-<project>-<feature>-<session_id>`) for once-per-session guards. Session-level flags get no TTL (cleared by OS). Cross-run flags (subagent-context session cache) get a 2h TTL to prevent stale contamination.

## Consequences

- Zero persistence overhead: no DB, no config writes
- Auto-cleared on reboot / OS `/tmp` cleanup
- Test isolation requires explicit flag cleanup at test start (consistent pattern across test files)
- Pattern proven across: compact-hint 3 tiers, design-tracker, stop-capture, subagent-context cache, reviewer-pass marker
