# ADR Session Cache — Eliminate Redundant ADR Loading in Reviewers

## Problem

Three reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) each call
"read all `zie-framework/decisions/*.md`" on every invocation. In a single
`/zie-plan` session with 3 slugs and 3 reviewers each, the same 24 ADR files
are loaded 9 times. As ADR count grows (currently 24 → projected 50+ in 3 months),
this becomes the dominant context overhead in review-heavy commands.

Additionally, zie-implement passes the full context bundle (ADRs + context.md) to
every impl-reviewer invocation, even though the bundle was already loaded once at
the start of the task loop.

## Motivation

Context window tokens are the scarcest resource during complex SDLC sessions. ADRs
are read-only reference material that doesn't change during a session — there's no
reason to re-read them from disk more than once. A session-scoped cache cuts ADR
loading overhead to a single read regardless of how many reviewers are spawned.

Also enables the future ADR summarization feature (adr-auto-summarization) to work
efficiently — the cache layer is the right place to apply summarization logic.

## Rough Scope

**Session cache mechanism:**
- Write `hooks/adr-cache.py` (or add to utils.py): reads all `decisions/*.md` once,
  writes compact JSON to `/tmp/zie-{session_id}/adr-cache.json` with mtime of newest
  ADR file as cache key
- Cache is valid for the session; invalidated if any ADR file is newer than cache mtime

**Reviewer skills update:**
- spec-reviewer, plan-reviewer, impl-reviewer: replace "read all decisions/*.md" step
  with "read `/tmp/zie-{session_id}/adr-cache.json` if exists, else read decisions/
  directly and write cache"
- If `/tmp/zie-{session_id}/` doesn't exist (non-session context) → fall back to
  direct read, no cache

**zie-implement context bundle:**
- Stop re-passing full ADR bundle to each impl-reviewer invocation
- Pass only the cache path reference; reviewer reads from cache
- Reduces per-task context by ~900 lines (current ADR total)

**Tests:**
- Cache written on first ADR read, reused on second
- Cache invalidated when ADR file is newer
- Reviewer falls back gracefully when cache missing
- Session ID isolation (two parallel sessions don't share cache)
