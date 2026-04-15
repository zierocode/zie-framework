---
approved: true
spec: specs/2026-04-14-auto-improve-design.md
---

# Auto-Improve — Implementation Plan

## Overview

Automatically apply high-confidence patterns (≥0.95) from sessions. Update CLAUDE.md/MEMORY.md, propose ADRs, suggest config changes.

## Tasks

### Phase 1: Pattern Aggregation

1. **Define pattern aggregation algorithm**
   - File: `zie-framework/project/pattern-aggregation.md`
   - Collect from all `.zie/memory/*.json`
   - Deduplicate (semantic similarity)
   - Rank: 0.5×confidence + 0.3×frequency + 0.2×recency

### Phase 2: Auto-Apply Thresholds

2. **Define thresholds**
   - File: `zie-framework/project/auto-apply-thresholds.md`
   - ≥0.95: auto-apply
   - 0.80-0.94: review
   - <0.80: archive

### Phase 3: Pattern Application Module

3. **Create `hooks/apply-patterns.py`**
   - Functions:
     - `aggregate_patterns(session_files)` — collect + dedupe
     - `rank_patterns(patterns)` — score calculation
     - `apply_to_claude_md(patterns)` — append workflow patterns
     - `apply_to_memory_md(patterns)` — add learned patterns
     - `suggest_config_changes(patterns)` — settings.json
     - `generate_adr_draft(pattern)` — for significant patterns

### Phase 4: Retro Command Update

4. **Update `commands/retro.md`**
   - Add `--auto` flag
   - Call `apply-patterns.py` with aggregated patterns
   - Present low-confidence for review

### Phase 5: ADR Template

5. **Update `zie-framework/decisions/adr-template.md`**
   - Add pattern-based ADR template section

### Phase 6: Testing

6. **Unit tests**
   - `test_apply_patterns.py`:
     - `test_pattern_aggregation_dedup()`
     - `test_pattern_ranking()`
     - `test_auto_apply_threshold()`
     - `test_claude_md_update()`
     - `test_adr_generation()`

7. **Integration tests**
   - High-confidence auto-applied
   - CLAUDE.md updated correctly
   - ADR generated for significant patterns
   - Low-confidence presented for review

## Acceptance Criteria

- [ ] High-confidence patterns auto-applied
- [ ] CLAUDE.md updated without intervention
- [ ] ADRs generated for significant patterns
- [ ] Low-confidence requires review
- [ ] No destructive changes without approval

## Dependencies

- `auto-learn` (pattern extraction)
- Session memory format

## Rollout

1. Define aggregation algorithm + thresholds
2. Create apply-patterns module
3. Update retro.md with --auto flag
4. Add CLAUDE.md auto-update
5. Add ADR generation
6. Test end-to-end
