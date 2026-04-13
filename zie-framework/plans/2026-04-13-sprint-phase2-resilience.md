---
approved: true
approved_at: 2026-04-13
backlog: backlog/sprint-phase2-resilience.md
spec: specs/2026-04-13-sprint-phase2-resilience-design.md
---

# sprint-phase2-resilience — Implementation Plan

**Goal:** Add per-item `.sprint-state` updates and per-item `/compact` to Phase 2 loop in `commands/sprint.md`.

**Tech Stack:** Markdown edit to `commands/sprint.md` only. No Python changes.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `commands/sprint.md` | Update Phase 2 loop + resume logic |
| Create | `tests/unit/test_sprint_command.py` | Structural tests for new Phase 2 behavior |

---

## Task 1 — RED: Write failing tests

Create `tests/unit/test_sprint_command.py`:

```python
from pathlib import Path
REPO_ROOT = Path(__file__).parents[2]
SPRINT_MD = REPO_ROOT / "commands" / "sprint.md"

def test_phase2_updates_state_per_item():
    text = SPRINT_MD.read_text()
    assert "remaining_items" in text
    # State update must appear inside the per-item loop, before "After all impl"
    loop_section = text[text.index("For each item"):text.index("After all impl complete")]
    assert "remaining_items" in loop_section

def test_phase2_resume_skips_completed():
    text = SPRINT_MD.read_text()
    assert "skipping completed" in text or "skip" in text.lower() and "remaining_items" in text

def test_phase2_compact_between_items():
    text = SPRINT_MD.read_text()
    loop_section = text[text.index("For each item"):text.index("After all impl complete")]
    assert "compact" in loop_section.lower()
    assert "context cleared" in loop_section
```

Run `make test-fast` → confirm 3 tests FAIL.

---

## Task 2 — GREEN: Edit sprint.md Phase 2

### Change A — Per-item state update

In the "For each item" loop, after step 3 (impl success line), add:

```markdown
   After success: rewrite `.sprint-state`:
   `{"phase": 2, "items": <all_slugs>, "completed_phases": [1], "remaining_items": <remaining_items minus this slug>, "started_at": <iso_ts>}`
```

### Change B — Per-item compact (between items, not after last)

After the state update step above (inside the loop, before moving to next item), add:

```markdown
   If this is not the last item: run `/compact` → print `[compact] context cleared after <slug>`
```

### Change C — Resume logic update

In pre-flight step 7 (Sprint resume check), extend the `yes` path:
```markdown
   - `yes` → skip audit, jump to the phase stored in state, use remaining_items
     - If phase=2: print `[resume] Phase 2 — skipping completed: <items not in remaining_items> | resuming from: <first remaining>`
```

**Acceptance Criteria:**
- [ ] State update inside loop (before "After all impl complete")
- [ ] `/compact` + "context cleared" inside loop
- [ ] Resume logic mentions remaining_items skip behavior
- [ ] All 3 RED tests now PASS

---

## Task 3 — Verify full suite

Run `make test-unit` → full suite passes.

**Acceptance Criteria:**
- [ ] 3 tests from Task 1 GREEN
- [ ] No regressions in existing sprint/implement/release tests

---

## Estimated Risk: LOW
- Pure markdown edit, no Python changes
- Additive only — doesn't remove existing behavior
- Structural tests verify presence, not runtime behavior
