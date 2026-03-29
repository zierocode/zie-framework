---
approved: false
approved_at: ""
backlog: backlog/adr-session-cache.md
---

# ADR Session Cache — Design Spec

**Problem:** The three reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) each read all `zie-framework/decisions/*.md` on every invocation, loading the same read-only ADR files repeatedly within a single session, inflating context overhead as the ADR count grows.

**Approach:** Add two helpers to `hooks/utils.py` — `get_cached_adrs` and `write_adr_cache` — that store ADR content as a single JSON blob at `<tmp_dir>/zie-<session_id>/adr-cache.json`, keyed by the max mtime of all ADR files so the cache self-invalidates if any ADR changes. Each reviewer skill checks the cache first and falls back to a direct disk read if the cache is absent or stale; zie-implement passes only the cache path reference to impl-reviewer rather than the full ADR bundle. This mirrors the existing `get_cached_roadmap` / `write_roadmap_cache` pattern already established in `utils.py` (ADR-024), keeping the codebase consistent and requiring no new architectural concepts.

**Components:**
- Modify: `hooks/utils.py` — add `get_cached_adrs(session_id)` and `write_adr_cache(session_id, content)` helpers
- Modify: `skills/spec-reviewer/SKILL.md` — replace direct ADR directory read with cache-first load using new helpers
- Modify: `skills/plan-reviewer/SKILL.md` — same cache-first ADR load
- Modify: `skills/impl-reviewer/SKILL.md` — same cache-first ADR load; update Phase 1 context_bundle handling to accept `adr_cache_path` in lieu of full `adrs` content
- Create: `tests/unit/test_adr_cache.py` — unit tests for the two new helpers

**Data Flow:**

1. First reviewer invoked in session reads `zie-framework/decisions/` directory; computes `max_mtime` across all `*.md` files.
2. Cache miss: helpers concatenate all ADR file contents into a JSON payload `{"mtime": <max_mtime>, "content": "<concatenated text>"}` and write to `<tempfile.gettempdir()>/zie-<sanitized_session_id>/adr-cache.json` via `safe_write_tmp` (owner-only 0o600, symlink-safe).
3. Cache returned to reviewer as `adrs_content` string; Phase 2 review proceeds normally.
4. Second reviewer invoked in same session: `get_cached_adrs` reads cache file, compares stored `mtime` against current `max_mtime` of decisions directory. Equal → return cached content; no disk scan of individual ADR files.
5. zie-implement — at task-loop start, reads ADR cache path (does not re-read content) and passes `adr_cache_path` string to each impl-reviewer invocation via the context_bundle field.
6. impl-reviewer receives `adr_cache_path`; reads the single JSON file to obtain `adrs_content`. Total ADR reads across N impl-reviewer invocations: 1 initial write + N cheap single-file reads instead of N × 24 file reads.
7. On session end, `session-cleanup.py` deletes `<tmp_dir>/zie-<session_id>/` including `adr-cache.json` — no orphan files.

**Edge Cases:**

- **decisions/ directory empty or missing** — `get_cached_adrs` returns `None`; reviewer falls back to "No ADRs found" path with no error. Cache not written.
- **ADR file added or modified mid-session** — `max_mtime` changes; cache comparison fails; helpers re-read directory and overwrite cache. Reviewer sees fresh content.
- **`/tmp` write fails** (disk full, permissions) — `safe_write_tmp` returns `False`; helpers return `None`; reviewer falls back to direct directory read. No crash, no reviewer block.
- **Cache file is a symlink** — `safe_write_tmp` refuses write and returns `False`; helpers fall back to direct read. Consistent with existing `safe_write_tmp` behavior (ADR-010).
- **session_id contains special characters** — sanitized via `re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)` before path construction, matching `get_cached_git_status` pattern (ADR-024).
- **Two parallel sessions with same project** — session_id is session-scoped; cache paths are distinct. No cross-session sharing.
- **`context_bundle` absent in reviewer call** — existing fallback path reads ADR directory directly (no regression for callers that don't pass bundle).
- **`adr_cache_path` points to stale or missing file** — impl-reviewer falls back to direct directory read, matching the absent-bundle path.

**Out of Scope:**

- ADR summarization or compression before caching — that is a separate backlog item (adr-auto-summarization); the cache layer is designed as the future insertion point but does not implement it.
- Changing reviewer checklist logic, Phase 2/3 content, or output format.
- Caching any artifact other than ADR content (spec files, plan files, context.md).
- Exposing cache TTL or cache path as a user-facing `.config` key — invalidation is mtime-based, not time-based; no TTL needed.
- Parallelising reviewer invocations or changing invocation protocol beyond the context_bundle field update.
- Modifying `session-cleanup.py` — it already removes the entire `zie-<session_id>/` directory on Stop; no change needed.
