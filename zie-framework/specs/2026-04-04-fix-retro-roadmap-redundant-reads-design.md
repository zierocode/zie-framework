# Fix Retro ROADMAP Redundant Reads

## Problem

The `/retro` command reads `ROADMAP.md` three separate times, each consuming 100–200 lines of context:
1. Pre-flight step 3 (targeted section reads for Now/Done/Next lanes, cached as local vars)
2. "Update ROADMAP Done inline" section (full file re-read to move shipped items to Done)
3. "Done-rotation" section (another read of Done section for archival logic)

The pre-flight read already extracts the full file content, which should be reused downstream.

## Approach

Thread the `roadmap_raw` binding (full file content read at pre-flight) through the command flow:

1. **Pre-flight**: capture `roadmap_raw ← read(ROADMAP.md)` at step 3 (where targeted section reads happen)
2. **Done-write section**: use `roadmap_raw` instead of re-reading; apply edits and write atomically
3. **Done-rotation section**: use `roadmap_raw` instead of re-reading; parse archived candidates and rewrite Done section
4. **No behavior change** — output and ROADMAP updates remain identical

## Components

**Modified files:**
- `/retro.md` — command markdown

**No new files or deletions needed.**

## Data Flow

1. Pre-flight step 3: bind `roadmap_raw` variable to full ROADMAP content
2. Pass `roadmap_raw` context binding to "Update ROADMAP Done inline" section → edit and write
3. Pass updated content forward to "Done-rotation" section → parse, filter, archive, rewrite
4. Final state: ROADMAP.md matches pre-change behavior, but with single read

## Edge Cases

- **Empty ROADMAP**: handled by existing guards (≤10 items skip in Done-rotation)
- **Malformed sections**: parsing logic unchanged; existing error handling applies
- **Git write failures**: non-blocking, already handled by existing retry/warn logic

## Out of Scope

- Optimizing other commands' file I/O patterns (separate backlog items)
- Caching ROADMAP between sessions (addressed by ADR-045: mtime-gate)
- Parsing efficiency improvements (beyond deduplication)

## Acceptance Criteria

1. Spec and plan approved by reviewers
2. `/retro` reads ROADMAP.md exactly once per execution
3. All three sections (Done-write, Done-rotation, docs) use single cached binding
4. No behavior change: output, ROADMAP structure, archival logic, git push identical
5. All existing tests pass
6. Test coverage for `roadmap_raw` binding flow added
