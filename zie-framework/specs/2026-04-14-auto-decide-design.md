---
approved: true
backlog: backlog/auto-decide.md
---

# Auto-Decide — เสนอ Action ที่เหมาะสมระหว่างทาง

## Summary

Proactively suggest next actions during a session. Detect patterns, recommend fixes, and propose next steps based on context. Always non-blocking—users can skip suggestions.

## Motivation

Currently, Claude waits for explicit user instructions at every step. There's no proactive suggestion of next actions—users must decide and direct every move. This creates cognitive load and slows progress.

Auto-decide provides intelligent suggestions at key moments: after test failures, at decision points, when patterns are detected. Users remain in control but get helpful nudges.

## Scope

### In Scope

1. **Hook: `hooks/post-tool-use.py`** (new)
   - Triggered after specific tool uses
   - Analyzes tool output for suggestion opportunities
   - Presents non-blocking suggestions

2. **Pattern-Based Recommendations**
   - Test failure → suggest `/fix` or debug steps
   - Multiple similar errors → suggest pattern fix
   - Completed task → suggest next backlog item

3. **"Continue?" Prompts**
   - After key events (test pass, spec complete, etc.)
   - Optional: "Continue to next step?" with skip option
   - Configurable prompt frequency

4. **Test Failure Detection**
   - Parse test output for failure patterns
   - Suggest: `/fix`, specific debug commands, relevant docs
   - Link to related context docs

### Out of Scope

- User control removal (always can skip)
- Auto-execution of suggestions (requires explicit approval)
- Cross-session decision tracking (handled by session memory)

## Technical Design

### Hook Integration

```
post-tool-use.py (post-tool hook)
├── Analyze tool output
├── Match against suggestion triggers
├── Generate context-aware recommendation
└── Present suggestion (non-blocking)
```

### Suggestion Triggers

| Trigger | Condition | Suggestion |
|---------|-----------|------------|
| Test failure | pytest exit code ≠ 0 | `/fix` + failure analysis |
| Spec complete | Spec file written | "Write plan? (`/plan`)" |
| Plan complete | Plan file written | "Implement? (`/implement`)" |
| Multiple errors | ≥3 similar errors | Pattern fix suggestion |
| Session idle | No activity >5min | "Continue working?" |

### Suggestion Format

```markdown
## Suggestion

**Detected:** 3 tests failing (AssertionError in test_auto_inject)

**Recommended action:** Run `/fix` to debug and fix failing tests

> Skip this suggestion: type "skip" or continue with another command
```

### Decision Detection Algorithm

1. **Event Classification**
   - Categorize tool output: success, failure, warning, info
   - Extract entities: files, tests, errors, decisions

2. **Pattern Matching**
   - Match against known suggestion patterns
   - Score relevance based on context

3. **Suggestion Generation**
   - Select highest-relevance suggestion
   - Format with context (file names, error snippets)

4. **Frequency Capping**
   - Max 3 suggestions per session
   - Cooldown: 5 minutes between suggestions
   - User-initiated actions reset cooldown

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `hooks/post-tool-use.py` | Create | Post-tool suggestion hook |
| `zie-framework/project/suggestion-triggers.md` | Create | Trigger → suggestion mapping |
| `zie-framework/project/suggestion-format.md` | Create | Suggestion output format spec |
| `hooks/hooks.json` | Modify | Register post-tool-use hook |

## Testing

### Unit Tests (`make test-unit`)

- `test_post_tool_analyzes_output()` — tool output parsing
- `test_suggestion_trigger_test_failure()` — test failure detection
- `test_suggestion_frequency_cap()` — max suggestions enforced
- `test_suggestion_format()` — output format validation
- `test_skip_suggestion()` — skip mechanism

### Integration Tests

- Test failure → `/fix` suggestion presented
- Spec complete → plan suggestion presented
- Multiple suggestions → frequency cap respected
- User can skip and continue without suggestion

## Dependencies

- `auto-learn` — pattern detection for suggestion triggers
- Session memory format — context for suggestions

## Rollout Plan

1. **Phase 1:** Basic test failure detection
2. **Phase 2:** Spec/plan complete suggestions
3. **Phase 3:** Pattern-based recommendations
4. **Phase 4:** Frequency capping + user preferences

## Success Criteria

- [ ] Suggestions presented at key moments (user-validated)
- [ ] Test failures detected with ≥90% accuracy
- [ ] Suggestions are actionable and relevant
- [ ] Users can skip suggestions easily
- [ ] No suggestion spam (≤3 per session)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Suggestion spam | Frequency cap, user-configurable limits |
| Wrong suggestions | Low-confidence suggestions suppressed |
| Interrupts flow | Non-blocking, skip option always available |
| Annoying prompts | Configurable, default to key events only |
