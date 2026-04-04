---
slug: model-release-effort-medium-to-low
date: 2026-04-04
approved: true
approved_at: 2026-04-04
model: sonnet
effort: low
---

# Plan: model-release-effort-medium-to-low

## Goal

Change `commands/release.md` frontmatter `effort: medium` → `effort: low`. Update test assertions to match.

## Tasks

### Task 1 — Update `commands/release.md`

**File:** `commands/release.md`

In frontmatter, change:
```yaml
effort: medium
```
To:
```yaml
effort: low
```

### Task 2 — Update test assertions

**File:** `tests/unit/test_model_effort_frontmatter.py`

Find `commands/release.md` entry in `EXPECTED` map:
- Change `("haiku", "medium")` → `("haiku", "low")`

Find `TestHaikuFiles.EXPECTED_HAIKU` list:
- Verify `commands/release.md` is included; update expected effort tuple if needed

### Task 3 — Run tests

```bash
make test-unit
```

All tests must pass.

## Acceptance Criteria

- `commands/release.md` frontmatter: `effort: low`
- `test_model_effort_frontmatter.py` asserts `("haiku", "low")` for `commands/release.md`
- `make test-unit` passes
