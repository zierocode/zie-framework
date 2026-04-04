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

# load-context — Shared Context Bundle

Load ADRs and project context once. Returns `context_bundle` for every
downstream reviewer call in the session.

## Steps

**Fast-path:** If `context_bundle` is provided as an argument to this skill
invocation → return `context_bundle` immediately. Skip all steps below.

**Step 0: Cache check**
- Call `get_cached_adrs(session_id, "zie-framework/decisions/")`.
  - Cache hit → `adrs_content` ← returned value; skip Step 1.
  - Cache miss → proceed to Step 1.

**Step 1: ADRs (disk fallback — cache miss only)**
- Read all `zie-framework/decisions/*.md` → concatenate →
  `adrs_content` (empty string if directory missing or empty).

**Step 2: Cache write**
- Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`:
  - Returns `(True, adr_cache_path)` → save path
  - Returns `(False, None)` → set `adr_cache_path = None`

**Step 3: Design context**
- Read `zie-framework/project/context.md` →
  `context_content` (empty string if file missing).

**Step 4: Assemble bundle**
- Build and return:
  ```
  context_bundle = {
    adr_cache_path: <path or None>,
    adrs: adrs_content,
    context: context_content
  }
  ```

## Output

`context_bundle` is available in the calling context. Pass it to every
reviewer invocation to skip per-reviewer disk reads.
