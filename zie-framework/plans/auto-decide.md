---
approved: true
spec: specs/2026-04-14-auto-decide-design.md
---

# Auto-Decide — Implementation Plan

## Overview

Proactively suggest next actions during session. Detect patterns, recommend fixes, propose next steps. Always non-blocking.

## Tasks

### Phase 1: Suggestion Triggers

1. **Define suggestion triggers**
   - File: `zie-framework/project/suggestion-triggers.md`
   - Triggers: test failure, spec complete, plan complete, multiple errors, session idle
   - Mapping: trigger → suggestion

### Phase 2: Suggestion Format

2. **Define suggestion output format**
   - File: `zie-framework/project/suggestion-format.md`
   - Markdown template with: detected condition, recommended action, skip option

### Phase 3: Post-Tool Hook

3. **Create `hooks/post-tool-use.py`**
   - Trigger: after specific tool uses
   - Functions:
     - `analyze_tool_output(tool_result)` — classify: success/failure/warning
     - `match_suggestion_trigger(event)` — pattern matching
     - `generate_recommendation(event, context)` — context-aware
     - `check_frequency_cap()` — max 3/session, 5min cooldown
     - `present_suggestion(suggestion)` — non-blocking output

### Phase 4: Hook Registration

4. **Update `hooks/hooks.json`**
   - Register `post-tool-use` hook

### Phase 5: Testing

5. **Unit tests**
   - `test_post_tool_use.py`:
     - `test_analyzes_output()`
     - `test_suggestion_trigger_test_failure()`
     - `test_suggestion_frequency_cap()`
     - `test_suggestion_format()`
     - `test_skip_suggestion()`

6. **Integration tests**
   - Test failure → `/fix` suggestion
   - Spec complete → plan suggestion
   - Frequency cap respected
   - User can skip

## Acceptance Criteria

- [ ] Suggestions at key moments (user-validated)
- [ ] Test failures detected ≥90% accuracy
- [ ] Suggestions actionable and relevant
- [ ] Skip mechanism works
- [ ] No spam (≤3/session)

## Dependencies

- `auto-learn` (pattern detection)
- Session memory format

## Rollout

1. Define triggers + format
2. Create post-tool-use hook (basic detection)
3. Add test failure detection
4. Add spec/plan complete suggestions
5. Add frequency capping
6. Test all triggers
