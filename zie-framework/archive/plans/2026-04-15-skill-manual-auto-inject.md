---
date: 2026-04-15
status: approved
slug: skill-manual-auto-inject
---

# Skill-Manual-Auto-Inject — Implementation Plan

## Steps

1. **Add config defaults** in `utils_config.py` — `skill_auto_inject.enabled` (default: true) and `skill_auto_inject.mapping` (default: `{"spec": "spec-reviewer", "plan": "write-plan", "implement": "impl-reviewer"}`).

2. **Create `hooks/utils_skill_inject.py`** — shared module with `inject_skill_context(stage: str, cwd: Path) -> str | None`. Reads `.config` for mapping, resolves skill SKILL.md path, returns content trimmed to max 2000 chars. Returns `None` on miss/disable.

3. **Extend `intent-sdlc.py`** — after building the `parts` list, call `inject_skill_context(stage, cwd)`. If non-empty, append to context before dedup+print. Only inject when `has_sdlc_keyword` is true and stage is in mapping.

4. **Extend `session-resume.py`** — after printing the orientation block, call `inject_skill_context(stage, cwd)` using the stage derived from ROADMAP. If non-empty, append to the `additionalContext` JSON payload alongside any auto-improve lines.

5. **Add unit tests** in `tests/test_skill_inject.py` — test default mapping, custom override, disabled flag, missing SKILL.md (returns None), content truncation, and non-SDLC-project guard.

6. **Update config reference** — document `skill_auto_inject` keys in `zie-framework/project/config-reference.md`.

## Tests

- `test_default_mapping_returns_skill_content` — default stage→skill mapping resolves and reads SKILL.md
- `test_disabled_returns_none` — `enabled: false` skips injection
- `test_custom_mapping_overrides_default` — user mapping takes precedence
- `test_missing_skill_returns_none` — nonexistent SKILL.md path → graceful None
- `test_content_truncated_at_2000` — long SKILL.md content is trimmed
- `test_non_sdlc_project_skips` — no `zie-framework/` dir → no injection

## Acceptance Criteria

- [ ] When stage=`implement`, `impl-reviewer/SKILL.md` content appears in `additionalContext`
- [ ] When stage=`spec`, `spec-reviewer/SKILL.md` content appears in `additionalContext`
- [ ] When stage=`plan`, `write-plan/SKILL.md` content appears in `additionalContext`
- [ ] `skill_auto_inject.enabled: false` suppresses all injection
- [ ] Custom mapping in `.config` overrides default
- [ ] Missing SKILL.md causes no error (graceful skip)
- [ ] Injection works in both `intent-sdlc.py` and `session-resume.py`
- [ ] All unit tests pass with `make test-unit`