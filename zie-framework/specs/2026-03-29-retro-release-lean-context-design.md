---
approved: true
approved_at: 2026-03-29
backlog: backlog/retro-release-lean-context.md
---

# Retro + Release Context Lean — Design Spec

**Problem:** `/zie-retro` reads ROADMAP.md twice and `/zie-release` has a blocking fallback for parallel docs-sync-check, both adding unnecessary latency to the heaviest post-sprint commands.

**Approach:** Pre-extract ROADMAP sections in `/zie-retro` and pass them to background agents to eliminate the second read, and replace the blocking fallback in `/zie-release` with a graceful skip message plus standalone manual target. This keeps the parallel gate design intact while removing sequential bottlenecks.

**Components:**
- `commands/zie-retro.md` — Pre-extract Done section, pass to agents, remove inline re-read
- `commands/zie-release.md` — Replace blocking fallback with skip message, add `make docs-sync` target
- `Makefile` — Add `docs-sync` target (manual hook for users to run separately)

**Data Flow:**

1. **zie-retro.md flow:**
   - Main flow reads Now + Done sections (targeted, ~40 lines)
   - Extract Done section text into `done_section_current` JSON field
   - Launch two background agents with `run_in_background=true`:
     - Agent 1: receive `done_section_current`, write ADRs (no re-read of ROADMAP)
     - Agent 2: receive `done_section_current` + new items to append, write full ROADMAP
       using regex replace of the Done section block (pattern: `## Done\n` to next `---`)
   - Agent 2 does a single full-file rewrite with section replacement — no offset arithmetic,
     no seek; simple and safe since retro runs serially (one retro at a time)
   - Both agents proceed concurrently without blocking main flow

2. **zie-release.md flow:**
   - Quality Checks section launches docs-sync-check Agent with `run_in_background=true`
   - Bash TODOs/secrets scan runs in parallel
   - Await both to complete
   - **If Agent tool unavailable (fallback):**
     - Print: `[zie-framework] docs-sync-check unavailable — skipping (manual check: make docs-sync)`
     - Continue to next gate without blocking
   - Release never blocks waiting for non-critical checks

3. **Makefile addition:**
   - Add `make docs-sync` target: `claude --print "Run /docs-sync-check"` or equivalent
     CLI invocation — documents the manual path; exact implementation is a comment/note
     since Skill tool is not available in Makefile context
   - Primary purpose: document the manual check path in a discoverable location

**Edge Cases:**

- Agent tool becomes unavailable mid-release: graceful skip with clear message; user can run `make docs-sync` manually later
- ROADMAP.md changes between extract and agent write: Agent 2 re-reads full file immediately before writing, applies regex section replace — avoids stale content
- Done section formatting changes (missing trailing `---`): regex pattern falls back to end-of-file as section boundary
- Parallel agents both attempt to write ROADMAP: retro runs serially so Agent 1 and Agent 2 are the only writers; both background but Agent 1 writes ADRs only (different files) — no ROADMAP write conflict
- User cancels release after quality checks start: background agents may still run; acceptable (quality checks are side-effect-safe)

**Out of Scope:**

- Full refactor of ROADMAP structure (remains text-based)
- Transaction/locking mechanism for concurrent ROADMAP writes (serial retro execution makes this unnecessary)
- Retry logic if Agent tool temporarily unavailable (graceful skip is preferred)
- Changes to ADR or CHANGELOG writing flow (only Done section updated)
- Changes to other commands that read ROADMAP (only /zie-retro and /zie-release are optimized)
