---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-retro-git-log-quad-read.md
---

# Lean Retro Git Log Quad-Read — Design Spec

**Problem:** `retro.md` reads git log 4 separate times per invocation — two bang-injected reads at command load and two Bash subprocess calls mid-flow — causing ~200–500 tokens of redundant content and extra subprocess latency despite the injected context already being in scope.

**Approach:** Apply ADR-052 bind-once discipline to git log in retro.md. Consolidate the two bang injections into one, eliminate the `git log --oneline -50` Bash call in self-tuning step 5 by referencing the already-injected bang output, and extract the last commit subject from the injected log for docs-sync step 8 instead of spawning a new `git log -1 --format="%s"` subprocess. Net result: exactly one git log read per retro invocation.

**Components:**
- `commands/retro.md` — primary change target: banner section (bang injections), self-tuning step 5, docs-sync step 8

**Data Flow:**
1. Command load: one `!git log --oneline -50` bang injection (replaces two existing bangs: `!git log --oneline` and `!git log -20 --oneline`).
2. Pre-flight binds `git_log_raw` (the injected output) as a named variable.
3. Self-tuning step (was step 5): reference `git_log_raw` — scan it for `RED` cycle patterns and `BLOCK` matches instead of spawning `git log --oneline -50` or `-20` Bash calls.
4. Docs-sync guard (was step 8): parse first line of `git_log_raw` to extract last commit subject — no separate Bash call.
5. All downstream sections reference `git_log_raw`; no re-reads.

**Edge Cases:**
- Empty git log (new repo / no commits): `git_log_raw` is empty string; self-tuning scan produces 0 matches (no crash); docs-sync guard subject extraction yields empty string (guard skips — correct behavior since no `release:` prefix).
- Fewer than 20 commits total: single injection still covers both the `-20` window and the `-50` window (returns all available); behavior unchanged.
- `git describe --tags` fails (no tags): the commits-since-tag bang already handles this via `|| git rev-list --max-parents=0 HEAD`; that bang is separate (covers a different range) and is kept as-is.

**Out of Scope:**
- The commits-since-tag bang (`!git log $(git describe --tags...)..HEAD --oneline`) — different range, different purpose, kept unchanged.
- Any changes to hook files (`hooks/*.py`).
- Tests for bang injection count (bang output is not easily testable via pytest; verifiable by code inspection of `commands/retro.md`).
- Changes to any other command beyond `retro.md`.
