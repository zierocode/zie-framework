---
name: load-context
description: Load shared context bundle (ADRs + project context) once per session. Returns context_bundle for downstream reviewers.
user-invocable: false
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
argument-hint: ""
model: haiku
effort: low
---

<!-- FAST PATH -->
**Purpose:** Load ADR + project context bundle once per session for downstream reviewers.
**When to use fast path:** context_bundle already provided → return it immediately.
**Quick steps:** (1) If context_bundle provided → return it. (2) Else: cache check → disk fallback → return bundle.
<!-- DETAIL: load only if fast path insufficient -->

# load-context — Shared Context Bundle

Load ADRs and project context once. Returns `context_bundle` for every
downstream reviewer call in the session.

## Steps

**Fast-path:** If `context_bundle` is provided as an argument to this skill
invocation → return `context_bundle` immediately. Skip all steps below.

**Step 0: Load unified cache**
- Import `get_cache_manager` from `hooks/utils_cache.py`.
- Call `cache = get_cache_manager(cwd)` where `cwd` is project root.
- Call `adrs_content = cache.get_or_compute("adrs", session_id, compute_fn, ttl=3600)` where:
  ```python
  def compute_fn():
      decisions_dir = cwd / "zie-framework" / "decisions"
      adr_files = sorted(decisions_dir.glob("*.md"))
      contents = [f.read_text() for f in adr_files if f.exists()]
      return "\n\n".join(contents) if contents else ""
  ```
- **Cache hit:** `get_or_compute()` returns cached value → skip disk read.
- **Cache miss:** `get_or_compute()` calls `compute_fn()` → reads ADRs from disk → caches result.

**Step 1: Design context**
- Read `zie-framework/project/context.md` →
  `context_content` (empty string if file missing).
  - Use `cache.get_or_compute("project_md", session_id, compute_fn, ttl=300)` for caching.
  - **Cache hit:** skip disk read. **Cache miss:** read from disk → cache.

**Step 2: Assemble bundle**
- Build and return:
  ```
  context_bundle = {
    adrs: adrs_content,
    context: context_content
  }
  ```

