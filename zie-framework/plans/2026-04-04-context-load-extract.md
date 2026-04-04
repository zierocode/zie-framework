# Plan: Extract Context-Bundle Load Pattern to Shared Skill

**status:** approved
**slug:** context-load-extract
**spec:** `zie-framework/specs/2026-04-04-context-load-extract-design.md`
**date:** 2026-04-04

---

## Tasks

### T1 — Create `skills/load-context/SKILL.md`

Create the new skill file with the canonical context-bundle load sequence.

Content must include:
- Invocation heading and purpose
- Step 1: Read all `zie-framework/decisions/*.md` → concatenate → `adrs_content` (empty string if directory missing)
- Step 2: Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")` → `(True, adr_cache_path)` or `(False, None)`
- Step 3: Read `zie-framework/project/context.md` → `context_content` (empty string if file missing)
- Step 4: Assemble `context_bundle = { adr_cache_path: <path or None>, adrs: adrs_content, context: context_content }`
- Output: `context_bundle` is available in the calling context

Strings the file must contain (test-required): `write_adr_cache`, `adr_cache_path`, `decisions/`, `project/context.md`.

**Files:** `skills/load-context/SKILL.md` (new)

---

### T2 — Update `commands/zie-plan.md`

Replace the inline context-bundle block (lines ~73–88) with:

```markdown
<!-- context-load: adrs + project context -->

Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`.
Pass `context_bundle` to every reviewer invocation below.
```

Keep the `<!-- context-load: adrs + project context -->` HTML comment in place (test assertion).

Verify after edit: `context_bundle`, `context-load`, `adr_cache_path`, `write_adr_cache`, `decisions/`, `project/context.md`, `once`/`session` — all still present (either via the marker comment or via the skill reference). If any token drops out, add a minimal prose note to retain it.

**Files:** `commands/zie-plan.md`

---

### T3 — Update `commands/zie-implement.md`

Replace the inline context-bundle block (lines ~42–49) with:

```markdown
## Context Bundle

<!-- context-load: adrs + project context -->

Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`. Pass `context_bundle` to every impl-reviewer call.
```

Keep `<!-- context-load: adrs + project context -->` in place.

Verify after edit: `context_bundle`, `context-load`, `adr_cache_path`, `write_adr_cache`, `decisions/`, `project/context.md` — all still present (retained via skill invocation line or a short parenthetical if needed).

**Files:** `commands/zie-implement.md`

---

### T4 — Update `commands/zie-sprint.md`

Replace the inline context-bundle block (lines ~102–113) with:

```markdown
## Load Context Bundle (Once Per Sprint)

Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`.
This bundle is passed to every downstream agent/skill call.
```

No `<!-- context-load -->` marker is required here (zie-sprint is not asserted by the marker tests). Verify `context_bundle` still present.

**Files:** `commands/zie-sprint.md`

---

### T5 — Verify tests pass

Run `make test-fast` (or `make lint && python -m pytest tests/unit/ -x -q`). All existing tests must pass with zero modifications to test files.

If any test fails due to a missing string, fix the command or skill file (not the test) to restore the required token.

**Files:** none (verification step)

---

## Files to Change

| File | Action |
| ---- | ------ |
| `skills/load-context/SKILL.md` | Create (new) |
| `commands/zie-plan.md` | Edit — replace ~16-line context-bundle block with 3-line skill call |
| `commands/zie-implement.md` | Edit — replace ~6-line block with 3-line skill call |
| `commands/zie-sprint.md` | Edit — replace ~12-line block with 2-line skill call |

No Python files. No test files. No hooks. Markdown-only change.

---

## Notes

- No test files are modified — all test assertions must pass via preserved markers and the new skill file.
- The `<!-- context-load: adrs + project context -->` comment is a test sentinel: keep it in zie-plan.md and zie-implement.md exactly as-is.
- `write_adr_cache`, `adr_cache_path`, `decisions/`, `project/context.md` must appear somewhere in each command file after the edit — either via a one-line reminder or by pointing to the skill. If removal of the block drops these strings, restore them with a parenthetical: `(calls write_adr_cache, bundles adr_cache_path + decisions/ + project/context.md)`.
