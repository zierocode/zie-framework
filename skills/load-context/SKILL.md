---
name: zie-framework:load-context
description: Load shared context bundle (ADRs + project context) once per session. Returns context_bundle for downstream reviewers.
user-invocable: false
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
argument-hint: "[keywords]"
model: haiku
effort: low
---

<!-- FAST PATH -->
**Purpose:** Load ADR + project context bundle once per session for downstream reviewers.
**Fast path:** context_bundle provided → return it immediately. Else: cache → disk → return bundle.
<!-- DETAIL: load only if fast path insufficient -->

# load-context — Shared Context Bundle

Load ADRs and project context once. Returns `context_bundle` for downstream reviewers.

## Arguments

| Pos | Var | Description | Default |
| --- | --- | --- | --- |
| 0 | `$ARGUMENTS[0]` | Comma-separated keywords for ADR relevance filter | absent → load all ADRs |

## Steps

**Fast-path:** `context_bundle` provided as argument → return immediately. Skip below.

**Step 0: Load ADRs via cache (with keyword filter)**
- Import `get_cache_manager` from `hooks/utils_cache.py`.
- `cache = get_cache_manager(cwd)` where `cwd` is project root.
- If `keywords` argument provided:
  - Parse: split on commas, strip whitespace, lowercase.
  - `adrs_content = cache.get_or_compute("adrs:kw:{keywords_hash}", session_id, compute_fn, ttl=3600)` where compute_fn calls `read_adrs_unified(cwd, keywords=keywords_list)`
- If no keywords → current behavior: `adrs_content = cache.get_or_compute("adrs", session_id, compute_fn, ttl=3600)`
- Cache hit → skip disk. Miss → compute → cache result.

**Step 1: Load project context via cache**
- `context_content = cache.get_or_compute("project_md", session_id, compute_fn, ttl=300)`
- Reads `zie-framework/project/context.md`; empty string if missing.
- Cache hit → skip disk. Miss → compute → cache.

**Step 2: Assemble bundle**
- Return `{ adrs: adrs_content, context: context_content }`