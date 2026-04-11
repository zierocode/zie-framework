---
slug: lean-load-context-triple-invoke
date: 2026-04-04
approved: true
approved_at: 2026-04-04
model: sonnet
effort: low
---

# Plan: lean-load-context-triple-invoke

## Goal

Eliminate redundant `load-context` calls in the sprint→implement chain by enforcing the existing fast-path contracts in prose. No new mechanisms — prose-only fix in 4 markdown files + structural tests.

## Tasks

### Task 1 — Update `skills/load-context/SKILL.md`

**File:** `skills/load-context/SKILL.md`

Add fast-path guard at the top of Steps section (before Step 0):

```
**Fast-path:** If `context_bundle` is provided as an argument to this skill
invocation → return `context_bundle` immediately. Skip all steps below.
```

### Task 2 — Update `skills/reviewer-context/SKILL.md`

**File:** `skills/reviewer-context/SKILL.md`

Strengthen the fast-path guard in Phase 1 to be unconditional:

```
**Fast-path (unconditional):** If `context_bundle` is provided → extract
`adrs_content = context_bundle.adrs` and `context_content = context_bundle.context`.
Return immediately. Skip all disk reads below.
```

### Task 3 — Update `commands/sprint.md` Phase 3

**File:** `commands/sprint.md`

In Phase 3 implement loop, change:
```
Invoke: `Skill(zie-framework:zie-implement, <slug>)`
```
To:
```
Invoke: `Skill(zie-framework:zie-implement, <slug>, context_bundle=<context_bundle>)`
```

### Task 4 — Update `commands/implement.md`

**File:** `commands/implement.md`

Verify and make explicit that `context_bundle` is passed to `impl-reviewer`:

Find the `@agent-impl-reviewer` or `Skill(impl-reviewer)` dispatch and ensure it reads:
```
Pass `context_bundle` (from argument or from load-context result above).
```

### Task 5 — Add structural tests

**File:** `tests/unit/test_lean_load_context.py` (new)

```python
from pathlib import Path

def _read(rel):
    return Path(rel).read_text()

def test_load_context_fast_path_documented():
    text = _read("skills/load-context/SKILL.md")
    assert "context_bundle" in text and "return" in text.lower()

def test_reviewer_context_fast_path_unconditional():
    text = _read("skills/reviewer-context/SKILL.md")
    assert "context_bundle" in text and "unconditional" in text.lower()

def test_sprint_passes_context_bundle_to_implement():
    text = _read("commands/sprint.md")
    assert "context_bundle" in text

def test_implement_passes_context_bundle_to_reviewer():
    text = _read("commands/implement.md")
    assert "context_bundle" in text
```

### Task 6 — Run tests

```bash
make test-unit
```

All tests must pass.

## Acceptance Criteria

- `skills/load-context/SKILL.md` has explicit fast-path returning `context_bundle` if provided
- `skills/reviewer-context/SKILL.md` has unconditional fast-path when `context_bundle` present
- `commands/sprint.md` Phase 3 passes `context_bundle` to `zie-implement`
- `commands/implement.md` passes `context_bundle` to reviewer
- New structural tests pass
