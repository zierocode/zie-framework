# Plan: Reviewer Skills Phase 1 Boilerplate Extraction

status: approved
backlog: zie-framework/backlog/reviewer-skills-boilerplate.md
spec: zie-framework/specs/2026-04-04-reviewer-skills-boilerplate-design.md

## Goal

Extract the identical "Phase 1 — Load Context Bundle" block from all three reviewer skills
into a new shared `reviewer-context` skill. Replace inline copies with a compact invocation
stub that retains all strings asserted by the test suite.

## Architecture

- New skill: `skills/reviewer-context/SKILL.md` — canonical Phase 1 protocol
- Modified: `skills/spec-reviewer/SKILL.md` — Phase 1 replaced with stub
- Modified: `skills/plan-reviewer/SKILL.md` — Phase 1 replaced with stub
- Modified: `skills/impl-reviewer/SKILL.md` — Phase 1 replaced with stub (retains `adr_cache_path`)
- New test: `tests/unit/test_sdlc_pipeline.py` — existence check for `reviewer-context`

## Tech Stack

Markdown only. No Python changes. No hook changes.

## Tasks

### Task 1 — Create `skills/reviewer-context/SKILL.md`

Create the new shared skill with:
- Frontmatter: `name: reviewer-context`, `user-invocable: false`, `context: fork`,
  `agent: Explore`, `allowed-tools: Read, Grep, Glob`, `model: haiku`, `effort: low`
- Full Phase 1 logic: `context_bundle` conditional fast path, ADR cache load
  (`get_cached_adrs`, `ADR-000-summary.md`, `write_adr_cache`), `project/context.md` read,
  `ROADMAP.md` read (Now + Ready + Next lanes)
- Returns: `adrs_content` and `context_content` for the calling reviewer to use

AC: File exists. Contains `context_bundle`, `get_cached_adrs`, `project/context.md`,
`ROADMAP`, `adrs_content`, `context_content`. `user-invocable: false`.

### Task 2 — Replace Phase 1 in `skills/spec-reviewer/SKILL.md`

Replace the 30-line Phase 1 block with a stub (6-8 lines):

```
## Phase 1 — Load Context Bundle

Invoke the `reviewer-context` skill to load shared context. It handles:
- **if context_bundle provided by caller** — uses `context_bundle.adrs` and
  `context_bundle.context` directly (fast path, skips disk reads)
- **If `context_bundle` absent** — reads from disk: `decisions/*.md` (via
  `get_cached_adrs` cache), `project/context.md`, `ROADMAP` lanes

Returns: `adrs_content`, `context_content`.
```

AC: All test-required strings present: `if context_bundle provided`, `context_bundle.adrs`,
`context_bundle.context`, `decisions/*.md`, `project/context.md`, `ROADMAP`.
File is at least 20 lines shorter than before.

### Task 3 — Replace Phase 1 in `skills/plan-reviewer/SKILL.md`

Same stub as Task 2 (plan-reviewer Phase 1 is identical to spec-reviewer's).

AC: Same strings as Task 2 retained. File at least 20 lines shorter.

### Task 4 — Replace Phase 1 in `skills/impl-reviewer/SKILL.md`

Replace Phase 1 with a stub that also retains `adr_cache_path` (impl-specific variant):

```
## Phase 1 — Load Context Bundle

Invoke the `reviewer-context` skill to load shared context. It handles:
- **if context_bundle provided by caller** — uses `context_bundle.context` directly;
  for ADRs checks `context_bundle.adr_cache_path` first (read JSON `content` field),
  then falls back to `context_bundle.adrs` (legacy), then disk fallback
- **If `context_bundle` absent** — reads from disk: `decisions/*.md` (via
  `get_cached_adrs` cache), `project/context.md`

Returns: `adrs_content`, `context_content`.
```

AC: Strings retained: `if context_bundle provided`, `context_bundle.adrs`,
`adr_cache_path`, `decisions/*.md`, `project/context.md`.
File at least 20 lines shorter.

### Task 5 — Add existence test for `reviewer-context`

In `tests/unit/test_sdlc_pipeline.py`, add:

```python
def test_reviewer_context_exists(self):
    assert os.path.exists(skill("reviewer-context")), \
        "skills/reviewer-context/SKILL.md must exist"
```

AC: Test added. `make test-fast` passes.

### Task 6 — Verify

Run `make test-fast` and `make lint`. Confirm zero failures and no lint errors.

AC: All green.

## Files to Change

| File | Action |
| --- | --- |
| `skills/reviewer-context/SKILL.md` | Create |
| `skills/spec-reviewer/SKILL.md` | Modify — replace Phase 1 block with stub |
| `skills/plan-reviewer/SKILL.md` | Modify — replace Phase 1 block with stub |
| `skills/impl-reviewer/SKILL.md` | Modify — replace Phase 1 block with stub |
| `tests/unit/test_sdlc_pipeline.py` | Modify — add reviewer-context existence test |
