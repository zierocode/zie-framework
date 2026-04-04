# Spec: Extract Context-Bundle Load Pattern to Shared Skill

**status:** draft
**slug:** context-load-extract
**date:** 2026-04-04

---

## Problem

The identical "Load Context Bundle" block appears copy-pasted in three command files:

- `commands/zie-plan.md` (lines 73–88) — 16 lines
- `commands/zie-implement.md` (lines 44–49) — 6 lines (compressed form)
- `commands/zie-sprint.md` (lines 102–113) — 12 lines

Each copy performs: read `decisions/*.md` → call `write_adr_cache` → read `project/context.md` → assemble `context_bundle`. Any protocol change (new fallback level, new field, renamed path) requires synchronised edits to three files. The copies are already drifting — zie-implement's block is a compressed shorthand vs the canonical form in zie-plan and zie-sprint.

---

## Solution

Create `skills/load-context/SKILL.md` as a canonical invocable skill that executes the context-bundle load sequence and returns `context_bundle`. Replace the inline blocks in all three command files with a `Skill(zie-framework:load-context)` call plus a one-line note on the returned value.

**Skill output contract:**
```
context_bundle = {
  adr_cache_path: <absolute path | null>,
  adrs: <concatenated ADR content | "">,
  context: <project/context.md content | "">
}
```

The skill assigns the result to `context_bundle` in the calling context and exits. Callers pass `context_bundle` downstream unchanged.

**Test constraint:** Existing tests assert the inline pattern directly in the command files (`context-load` HTML comment marker, `write_adr_cache`, `adr_cache_path`, `decisions/`, `project/context.md` literals). The command files must retain these strings. Each command's inline block is replaced with a `Skill(zie-framework:load-context)` call **and** the HTML marker `<!-- context-load: adrs + project context -->` is preserved in-place so tests continue to pass without modification.

---

## Acceptance Criteria

1. `skills/load-context/SKILL.md` exists and contains the full canonical context-bundle load sequence (read ADRs → `write_adr_cache` → read context → assemble bundle).
2. `commands/zie-plan.md` context-bundle section is replaced with a `Skill(zie-framework:load-context)` call; the `<!-- context-load: adrs + project context -->` marker is retained.
3. `commands/zie-implement.md` context-bundle section is replaced with a `Skill(zie-framework:load-context)` call; the `<!-- context-load: adrs + project context -->` marker is retained.
4. `commands/zie-sprint.md` context-bundle section is replaced with a `Skill(zie-framework:load-context)` call; the `<!-- context-load: adrs + project context -->` marker is retained.
5. All existing tests pass without modification — no test file is changed.
6. The skill's SKILL.md contains: `write_adr_cache`, `adr_cache_path`, `decisions/`, `project/context.md` — so tests that scan skills/ also pass.
7. Each command file is 10–15 lines shorter after the replacement.

---

## Out of Scope

- Changing the context-bundle data shape or protocol.
- Modifying any test files.
- Extracting the `context_bundle` pass-through into reviewer skills (separate concern).
- Any Python / hook changes.
