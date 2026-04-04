---
slug: lean-dual-audit-pipeline
date: 2026-04-04
approved: true
approved_at: 2026-04-04
model: sonnet
effort: low
---

# Plan: lean-dual-audit-pipeline

## Goal

Make `skills/zie-audit/SKILL.md` the single canonical audit implementation. Reduce `commands/audit.md` to a thin dispatcher (≤20 lines). Absorb unique command-level agent checks into the skill.

## Tasks

### Task 1 — Update `skills/zie-audit/SKILL.md`

**File:** `skills/zie-audit/SKILL.md`

Absorb the following checks from `commands/audit.md` into existing agents:

- **MCP server usage check** (`grep commands/*.md + skills/*/SKILL.md for mcp__<name>__`) → add to Agent E (Architecture)
- **Dead code/duplication checks** from command's Agent 2 → merge into Agent B (Lean/Efficiency)
- **Async/hot-path perf checks** from command's Agent 2 → merge into Agent E (Architecture)
- **Observability checks** (health checks, log levels, graceful shutdown) from command's Agent 3 → merge into Agent E
- **Dep health checks** (overly-loose pins, license risks, actively-maintained alternatives) from command's Agent 1 → merge into Agent A (Security)

### Task 2 — Rewrite `commands/audit.md` as thin dispatcher

**File:** `commands/audit.md`

Preserve frontmatter. Replace body with:

```markdown
<!-- model: haiku effort: low -->

Parse `--focus <dim>` from `$ARGUMENTS` if present.

Invoke: `Skill(zie-framework:zie-audit)` passing `--focus <dim>` or no args.

The skill handles all audit phases, agent dispatch, synthesis, and backlog selection.
```

Target: ≤20 lines total (frontmatter + body).

### Task 3 — Add structural test

**File:** `tests/unit/test_structural.py`

Add assertion:

```python
def test_audit_command_is_thin_dispatcher():
    lines = Path("commands/audit.md").read_text().splitlines()
    assert len(lines) <= 20, f"commands/audit.md has {len(lines)} lines (limit: 20)"
```

### Task 4 — Run tests

```bash
make test-unit
```

Existing structural tests must pass. New assertion passes.

## Acceptance Criteria

- `commands/audit.md` ≤20 lines; body is a thin dispatcher invoking the skill
- `skills/zie-audit/SKILL.md` absorbs the 4 unique check categories from the command
- `--focus` pass-through works (dispatcher passes raw value to skill)
- Structural test assertion passes
- No duplicate context-bundle setup; skill Phase 1 is the single setup point
