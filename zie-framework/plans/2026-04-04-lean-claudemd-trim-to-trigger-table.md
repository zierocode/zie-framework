---
slug: lean-claudemd-trim-to-trigger-table
date: 2026-04-04
approved: true
approved_at: 2026-04-04
model: sonnet
effort: low
---

# Plan: lean-claudemd-trim-to-trigger-table

## Goal

Cut `CLAUDE.md` from ~160 lines to ≤80 lines by moving hook-authoring reference sections to spoke docs in `zie-framework/project/`. Add a Makefile line-count lint rule to enforce the limit.

## Tasks

### Task 1 — Create `zie-framework/project/hook-conventions.md`

**File:** `zie-framework/project/hook-conventions.md` (new)

Move verbatim from `CLAUDE.md`:
- "Hook Output Convention" section
- "Hook Error Handling Convention" section
- "Hook Context Hints" section

### Task 2 — Create `zie-framework/project/config-reference.md`

**File:** `zie-framework/project/config-reference.md` (new)

Move verbatim from `CLAUDE.md`:
- "Hook Configuration" section (the config key table)

### Task 3 — Update `CLAUDE.md`

**File:** `CLAUDE.md`

Replace the four moved sections with a 4-row trigger table:

```markdown
## Reference Docs

| Topic | File |
| --- | --- |
| Hook Output Convention | `zie-framework/project/hook-conventions.md` |
| Hook Error Handling Convention | `zie-framework/project/hook-conventions.md` |
| Hook Context Hints | `zie-framework/project/hook-conventions.md` |
| Hook Configuration Keys | `zie-framework/project/config-reference.md` |
```

Target: ≤80 lines after change.

### Task 4 — Update `templates/CLAUDE.md`

**File:** `templates/CLAUDE.md`

Apply the same trigger table replacement so new `/init` projects get the lean version.

### Task 5 — Update `Makefile`

**File:** `Makefile`

Add `check-claudemd-lines` target:
```makefile
check-claudemd-lines:
	@python3 -c "import sys; lines = open('CLAUDE.md').readlines(); n = len(lines); sys.exit(1) if n > 80 else print(f'CLAUDE.md: {n} lines (OK)')"
```

Wire into `lint`: add `check-claudemd-lines` as dependency of the `lint` target.

### Task 6 — Add test

**File:** `tests/unit/test_claudemd_line_count.py` (new)

```python
def test_claudemd_line_count():
    path = Path("CLAUDE.md")
    lines = path.read_text().splitlines()
    assert len(lines) <= 80, f"CLAUDE.md has {len(lines)} lines (limit: 80)"
```

### Task 7 — Run tests

```bash
make test-unit
```

All existing tests must pass. New test passes.

## Acceptance Criteria

- `CLAUDE.md` ≤80 lines
- `zie-framework/project/hook-conventions.md` exists with moved content (verbatim)
- `zie-framework/project/config-reference.md` exists with moved content (verbatim)
- `templates/CLAUDE.md` has trigger table (not the verbose sections)
- `make lint` includes `check-claudemd-lines` and passes
- New test asserts ≤80 lines and passes
