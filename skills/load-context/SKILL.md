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

1. **ADRs** — read all `zie-framework/decisions/*.md` → concatenate →
   `adrs_content` (empty string if directory missing or empty).

2. **Cache** — call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`:
   - Returns `(True, adr_cache_path)` → save path
   - Returns `(False, None)` → set `adr_cache_path = None`

3. **Design context** — read `zie-framework/project/context.md` →
   `context_content` (empty string if file missing).

4. **Assemble** bundle:
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
