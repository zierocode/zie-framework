---
slug: lean-reviewer-context-chain-depth
date: 2026-04-04
approved: true
approved_at: 2026-04-04
model: sonnet
effort: low
---

# Plan: lean-reviewer-context-chain-depth

## Goal

Remove the `Skill(reviewer-context)` call from all three reviewers. Replace with an inline two-branch block (fast-path when `context_bundle` provided; disk-fallback when absent). Update callers to pass `context_bundle`. Eliminate 1 skill invocation per reviewer call.

## Tasks

### Task 1 — Update `skills/spec-reviewer/SKILL.md`

**File:** `skills/spec-reviewer/SKILL.md`

Replace Phase 1 (`Skill(reviewer-context)`) with inline block:

```markdown
**Phase 1: Load context**

- If `context_bundle` provided by caller:
  - `adrs_content = context_bundle.adrs`
  - `context_content = context_bundle.context`
  - (Skip disk reads)
- Else (disk fallback):
  - Call `get_cached_adrs(session_id, "zie-framework/decisions/")` → `adrs_content`; on cache miss read all `decisions/*.md`
  - Read `zie-framework/project/context.md` → `context_content`
  - Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")` → `adr_cache_path`
```

### Task 2 — Update `skills/plan-reviewer/SKILL.md`

**File:** `skills/plan-reviewer/SKILL.md`

Apply identical Phase 1 inline block as Task 1.

### Task 3 — Update `skills/impl-reviewer/SKILL.md`

**File:** `skills/impl-reviewer/SKILL.md`

Apply identical Phase 1 inline block as Task 1.

### Task 4 — Update `skills/spec-design/SKILL.md`

**File:** `skills/spec-design/SKILL.md`

When invoking `Skill(spec-reviewer, ...)`, add `context_bundle=<context_bundle>` as argument.

### Task 5 — Update `skills/write-plan/SKILL.md`

**File:** `skills/write-plan/SKILL.md`

When invoking `Skill(plan-reviewer, ...)`, add `context_bundle=<context_bundle>` as argument.

### Task 6 — Update `skills/reviewer-context/SKILL.md`

**File:** `skills/reviewer-context/SKILL.md`

Add note at the top:

```markdown
> **Note:** This skill is for standalone direct use only. The three reviewer
> skills (spec-reviewer, plan-reviewer, impl-reviewer) inline their own
> context-load logic. Do not invoke this skill from within those reviewers.
```

### Task 7 — Add structural tests

**File:** `tests/unit/test_reviewer_context_chain.py` (new)

```python
from pathlib import Path

def test_spec_reviewer_no_skill_reviewer_context_call():
    text = Path("skills/spec-reviewer/SKILL.md").read_text()
    assert "Skill(reviewer-context)" not in text

def test_plan_reviewer_no_skill_reviewer_context_call():
    text = Path("skills/plan-reviewer/SKILL.md").read_text()
    assert "Skill(reviewer-context)" not in text

def test_impl_reviewer_no_skill_reviewer_context_call():
    text = Path("skills/impl-reviewer/SKILL.md").read_text()
    assert "Skill(reviewer-context)" not in text

def test_spec_design_passes_context_bundle_to_reviewer():
    text = Path("skills/spec-design/SKILL.md").read_text()
    assert "context_bundle" in text

def test_write_plan_passes_context_bundle_to_reviewer():
    text = Path("skills/write-plan/SKILL.md").read_text()
    assert "context_bundle" in text
```

### Task 8 — Run tests

```bash
make test-unit
```

## Acceptance Criteria

- None of the three reviewer SKILL.md files contain `Skill(reviewer-context)`
- All three have inline two-branch Phase 1 block with fast-path + disk-fallback
- `spec-design` and `write-plan` pass `context_bundle` to their respective reviewers
- `reviewer-context/SKILL.md` documented as standalone-only
- Structural tests pass
