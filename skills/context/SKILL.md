---
name: zie-framework:context
description: Load shared context bundle (ADRs + project context) and show framework reference maps. Returns context_bundle for downstream reviewers.
user-invocable: false
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
argument-hint: "[keywords]"
model: haiku
effort: low
---

<!-- FAST PATH -->
**Purpose:** Load ADR + project context bundle and/or show framework reference maps.
**Fast path:** context_bundle provided → return immediately. Else: cache → disk → return bundle.
<!-- DETAIL: load only if fast path insufficient -->

# context — Shared Context Bundle & Framework Reference

## Arguments

| Pos | Var | Description | Default |
| --- | --- | --- | --- |
| 0 | `$ARGUMENTS[0]` | Comma-separated keywords for ADR relevance filter | absent → load all ADRs |

## Context Loading

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

## Framework Reference (read by session-resume.py)

### Command Map

- `/backlog` — capture new idea
- `/spec` — design a backlog item
- `/plan` — plan from approved spec
- `/implement` — TDD implementation (agent mode)
- `/sprint` — full pipeline: backlog→spec→plan→implement→release→retro
- `/fix` — debug & fix failing tests/features (`--hotfix` for emergencies, `--chore` for maintenance)
- `/status` — current SDLC state (`--guide` for walkthrough, `--health` for hook check, `--brief` for design brief)
- `/audit` — project audit
- `/retro` — post-release retrospective
- `/release` — merge dev→main, bump version
- `/resync` — refresh project knowledge
- `/init` — bootstrap in a new project

### Workflow Map

backlog → spec (reviewer) → plan (reviewer) → implement → release → retro

Use `/sprint` to run the full pipeline in one session.

### Anti-Patterns

- Never write `approved: true` directly — use `python3 hooks/approve.py`
- Never skip spec/plan steps on "ทำเลย" or similar shortcuts
- Never run `/implement` without an approved plan
- Never approve without running the corresponding reviewer skill first