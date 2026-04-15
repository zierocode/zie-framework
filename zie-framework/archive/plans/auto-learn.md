---
approved: true
spec: specs/2026-04-14-auto-learn-design.md
---

# Auto-Learn — Implementation Plan

## Overview

Automatically extract and save patterns at session end. Capture session activity, detect high-confidence patterns, persist to `.zie/memory/session-*.json`.

## Tasks

### Phase 1: Session Memory Schema

1. **Define session memory schema** (shared with auto-inject)
   - File: `zie-framework/project/session-memory-format.md`
   - Fields: `session_id`, `timestamp`, `summary`, `statistics`, `patterns`, `decisions`, `context_keywords`
   - Pattern schema: `id`, `category`, `description`, `confidence`, `evidence`, `auto_apply`

### Phase 2: Pattern Categories

2. **Define pattern categories**
   - File: `zie-framework/project/pattern-categories.md`
   - Categories: `workflow`, `code`, `decision`, `communication`
   - Examples per category

### Phase 3: Session Stop Hook

3. **Create `hooks/session-stop.py`**
   - Trigger: post-exit hook
   - Functions:
     - `capture_transcript()` — session conversation
     - `analyze_tool_usage()` — tool call statistics
     - `extract_patterns_heuristic(transcript, tool_stats)` — frequency-based
     - `extract_patterns_llm(transcript)` — optional, gated
     - `score_pattern_confidence(pattern)` — frequency + consistency + recency
     - `write_session_memory(session_data)` — JSON output

### Phase 4: Hook Registration

4. **Update `hooks/hooks.json`**
   - Register `session-stop` as post-exit hook

### Phase 5: Pattern Extraction Algorithm

5. **Document algorithm**
   - File: `zie-framework/project/pattern-extraction.md`
   - Heuristic: count tool sequences, detect repeated workflows
   - LLM-based: extract decisions, learnings, anti-patterns
   - Scoring: 0.4×frequency + 0.3×consistency + 0.3×recency
   - Auto-apply threshold: ≥0.95

### Phase 6: Testing

6. **Unit tests**
   - `test_session_stop.py`:
     - `test_captures_transcript()`
     - `test_pattern_extraction_heuristic()`
     - `test_pattern_confidence_scoring()`
     - `test_session_memory_schema()`
     - `test_auto_apply_threshold()`

7. **Integration tests**
   - Session end → memory file created
   - Patterns extracted and scored
   - High-confidence marked for auto-apply

## Acceptance Criteria

- [ ] Session memory file created on every session end
- [ ] Patterns extracted with ≥80% precision
- [ ] High-confidence patterns correctly identified (≥0.95)
- [ ] Session memory retrievable by auto-inject
- [ ] Zero impact on session performance (<1s overhead)

## Dependencies

- None (foundational)

## Rollout

1. Define session memory schema + categories
2. Create session-stop hook (basic capture)
3. Add heuristic pattern extraction
4. Add LLM extraction (optional)
5. Add confidence scoring + auto-apply
6. Test end-to-end
