---
slug: lean-subagent-stop-no-matcher
date: 2026-04-04
approved: true
approved_at: 2026-04-04
model: sonnet
effort: low
---

# Plan: lean-subagent-stop-no-matcher

## Goal

Investigate whether `SubagentStop` supports a `matcher` field in the Claude Code plugin spec. Document the finding in `hooks.json` and write an ADR. No changes to `subagent-stop.py` logic.

## Tasks

### Task 1 — Investigate matcher support

Read `hooks/hooks.json` to see how `Stop` and `SubagentStart` matchers are defined. Check Claude Code plugin documentation (available in CLAUDE.md or `zie-framework/decisions/`) for any reference to SubagentStop matcher support. Check if the existing `_stop_matcher_note` comment addresses SubagentStop.

Expected outcome: SubagentStop does **not** support matchers (Claude Code docs indicate matcher support is limited for async/stop-class hooks).

### Task 2 — Update `hooks/hooks.json`

**File:** `hooks/hooks.json`

If matcher is **not** supported (expected case):

Add/update comment in the `SubagentStop` block:

```json
// SubagentStop does not support matcher field (investigated 2026-04-04).
// Filtering is handled by the in-hook cwd guard (Tier 1) in subagent-stop.py.
// See ADR-054.
```

If matcher **is** supported (unlikely):

Add:
```json
"matcher": "Explore|Plan|spec-reviewer|plan-reviewer|impl-reviewer"
```

### Task 3 — Write ADR

**File:** `zie-framework/decisions/ADR-054-subagent-stop-matcher-investigation.md`

```markdown
# ADR-054: SubagentStop Matcher Support Investigation

**Date:** 2026-04-04
**Status:** Accepted

## Context

SubagentStop fires on every subagent completion across all projects. Without a
matcher filter, Python startup overhead occurs even in non-zie-framework projects.
We investigated whether SubagentStop supports a `matcher` field like `SubagentStart`.

## Decision

SubagentStop does not support matcher field in the Claude Code plugin spec.
The in-hook cwd guard (Tier 1 in `subagent-stop.py`) is the sole filter:
exits 0 immediately if `zie-framework/` dir is absent from cwd.

## Consequences

- `hooks.json` is documented to explain why no matcher is present
- `subagent-stop.py` cwd guard remains the authoritative filter
- No code changes required
```

### Task 4 — Add test

**File:** `tests/unit/test_hooks_json.py`

Add assertion:

```python
def test_subagent_stop_matcher_absence_documented():
    """SubagentStop has no matcher; comment must document why."""
    hooks_text = Path("hooks/hooks.json").read_text()
    assert "SubagentStop" in hooks_text
    # Either matcher absent (expected) or matcher present (if supported)
    # The key assertion: the investigation note/comment is present
    assert "ADR-054" in hooks_text or "not support" in hooks_text.lower()
```

### Task 5 — Run tests

```bash
make test-unit
```

## Acceptance Criteria

- Investigation completed; finding documented in `hooks.json` comment
- ADR-054 written explaining the investigation result
- If not supported: comment explains why matcher is absent; cwd guard documented as sole filter
- If supported: matcher added with appropriate agent-type filter string
- New test assertion passes
