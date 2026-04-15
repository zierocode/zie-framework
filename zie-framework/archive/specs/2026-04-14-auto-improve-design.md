---
approved: true
backlog: backlog/auto-improve.md
---

# Auto-Improve — High-Confidence Patterns Applied อัตโนมัติ

## Summary

Automatically apply high-confidence patterns (≥0.95) extracted from sessions. Update `.claude/CLAUDE.md` or `MEMORY.md`, propose ADRs for significant patterns, and suggest config changes. Low-confidence patterns require manual review.

## Motivation

Currently, patterns extracted from retrospectives must be applied manually. This creates friction—users know what improvements to make but must remember to apply them. High-confidence patterns that would improve workflow are never actioned.

Auto-improve closes the loop: detected patterns are automatically applied, building a self-improving system that gets better over time.

## Scope

### In Scope

1. **Command: `commands/retro.md` — Auto-Mode**
   - New `--auto` flag for automatic pattern application
   - Aggregates patterns from session memory
   - Applies high-confidence patterns (≥0.95) automatically

2. **Pattern Aggregation + Ranking**
   - Collect patterns from all session memories
   - Deduplicate similar patterns
   - Rank by confidence, frequency, recency

3. **Auto-Apply Mechanisms**
   - **CLAUDE.md updates:** Append workflow patterns
   - **MEMORY.md updates:** Add learned patterns
   - **Config changes:** Suggest settings.json modifications
   - **ADR generation:** For significant architectural patterns

4. **Low-Confidence Review**
   - Patterns <0.95 presented for manual review
   - User approves/rejects each pattern
   - Rejected patterns deprioritized

### Out of Scope

- Low-confidence pattern auto-application (requires review)
- Destructive changes (always requires approval)
- Cross-project pattern application

## Technical Design

### Pattern Aggregation Pipeline

```
Session Memories (.zie/memory/*.json)
├── Extract all patterns
├── Deduplicate (semantic similarity)
├── Aggregate scores (weighted average)
└── Rank by: confidence (0.5), frequency (0.3), recency (0.2)
```

### Auto-Apply Threshold

| Confidence | Action |
|------------|--------|
| ≥0.95 | Auto-apply, notify user |
| 0.80-0.94 | Present for review |
| <0.80 | Archive, no action |

### Pattern Application Types

| Pattern Type | Application Method |
|--------------|-------------------|
| Workflow | Append to CLAUDE.md "From Now On" section |
| Code Style | Update CLAUDE.md code review checklist |
| Decision | Generate ADR draft |
| Config | Suggest settings.json change |

### ADR Generation

For significant patterns (architectural decisions):

1. Detect pattern category: `architecture`, `workflow`, `tooling`
2. Generate ADR draft in `zie-framework/decisions/`
3. Present for review: "Generate ADR for this pattern?"
4. On approval: Write ADR, link from ROADMAP.md

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `commands/retro.md` | Modify | Add `--auto` flag for auto-apply mode |
| `zie-framework/project/pattern-aggregation.md` | Create | Pattern aggregation algorithm |
| `zie-framework/project/auto-apply-thresholds.md` | Create | Threshold definitions |
| `hooks/apply-patterns.py` | Create | Pattern application logic |
| `zie-framework/decisions/adr-template.md` | Modify | ADR template for pattern-based ADRs |

## Testing

### Unit Tests (`make test-unit`)

- `test_pattern_aggregation_dedup()` — semantic deduplication
- `test_pattern_ranking()` — score calculation correctness
- `test_auto_apply_threshold()` — 0.95 boundary cases
- `test_claude_md_update()` — CLAUDE.md append logic
- `test_adr_generation()` — ADR draft generation

### Integration Tests

- High-confidence patterns auto-applied
- CLAUDE.md updated correctly
- ADR generated for significant patterns
- Low-confidence patterns presented for review
- Rejected patterns deprioritized

## Dependencies

- `auto-learn` — pattern extraction from sessions
- Session memory format — pattern storage

## Rollout Plan

1. **Phase 1:** Pattern aggregation from session memories
2. **Phase 2:** CLAUDE.md auto-update for workflow patterns
3. **Phase 3:** ADR generation for significant patterns
4. **Phase 4:** Config change suggestions

## Success Criteria

- [ ] High-confidence patterns auto-applied correctly
- [ ] CLAUDE.md updated without user intervention
- [ ] ADRs generated for significant patterns
- [ ] Low-confidence patterns require review
- [ ] No destructive changes without approval

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Wrong patterns applied | High threshold (0.95), rollback mechanism |
| CLAUDE.md bloat | Periodic review, pattern expiration |
| Unwanted config changes | Always present for review first |
| ADR spam | Only significant patterns, user confirmation |
