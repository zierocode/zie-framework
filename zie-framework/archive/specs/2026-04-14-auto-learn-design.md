---
approved: true
backlog: backlog/auto-learn.md
---

# Auto-Learn — Patterns ถูก Extract เมื่อ Session จบ

## Summary

Automatically extract and save patterns at session end. Capture session activity, detect high-confidence patterns, and persist to `.zie/memory/session-*.json`. Eliminates need for manual `/retro` for routine pattern capture.

## Motivation

Currently, session knowledge is lost when the session ends. Users must manually run `/retro` to extract patterns and learnings. This creates friction and results in lost knowledge—patterns that could improve future sessions are never captured.

Auto-learn captures patterns automatically at session end, building a growing knowledge base that improves over time.

## Scope

### In Scope

1. **Hook: `hooks/session-stop.py`** (new)
   - Triggered on session termination (via post-exit hook)
   - Captures full session transcript and tool usage
   - Extracts patterns using heuristic + LLM-based analysis
   - Writes session memory JSON file

2. **Session Memory Format**
   - JSON schema for session data
   - Stored in `.zie/memory/session-YYYYMMDD-HHMMSS.json`
   - Includes: summary, patterns, tool stats, decisions

3. **Pattern Detection**
   - High-confidence threshold (≥0.95) for auto-apply candidates
   - Pattern categories: workflow, code, decision, communication
   - Confidence scoring based on frequency + consistency

4. **Session Memory Storage**
   - Append-only session memory files
   - Aggregated into `.zie/memory/latest.json` symlink
   - Indexed by timestamp for retrieval

### Out of Scope

- Manual `/retro` command removal (remains for deep review)
- Cross-session pattern aggregation (handled by `auto-improve`)
- Real-time pattern detection during session

## Technical Design

### Hook Integration

```
session-stop.py (post-exit hook)
├── Capture session transcript
├── Analyze tool usage patterns
├── Extract patterns (heuristic + LLM)
├── Score pattern confidence
└── Write session memory JSON
```

### Session Memory Schema

```json
{
  "session_id": "20260414-093000",
  "timestamp": {
    "start": "2026-04-14T09:30:00Z",
    "end": "2026-04-14T10:45:00Z"
  },
  "summary": "Auto-generated session summary",
  "statistics": {
    "tool_calls": 42,
    "files_modified": 5,
    "tests_run": 12,
    "commits": 2
  },
  "patterns": [
    {
      "id": "pattern-001",
      "category": "workflow",
      "description": "TDD loop: test → implement → refactor",
      "confidence": 0.97,
      "evidence": ["test-unit run before implement", "refactor after green"],
      "auto_apply": true
    }
  ],
  "decisions": [
    {
      "id": "decision-001",
      "description": "Chose pytest over unittest",
      "rationale": "Better fixture support",
      "adr_suggested": false
    }
  ],
  "context_keywords": ["tdd", "pytest", "hooks"]
}
```

### Pattern Extraction Algorithm

1. **Heuristic Analysis**
   - Count tool call sequences (e.g., test → implement → refactor)
   - Detect repeated workflows (≥3 occurrences = high confidence)
   - Identify code patterns (naming, structure, style)

2. **LLM-Based Analysis** (optional, gated)
   - Send session transcript to LLM for pattern extraction
   - Extract: decisions, learnings, anti-patterns
   - Merge with heuristic results

3. **Confidence Scoring**
   - Frequency weight: 0.4 × (occurrences / max_occurrences)
   - Consistency weight: 0.3 × (1 - variance / mean)
   - Recency weight: 0.3 × exp(-days_since / 30)
   - Final score: sum of weights (0.0 - 1.0)

4. **Auto-Apply Threshold**
   - `auto_apply: true` when confidence ≥ 0.95
   - These patterns are candidates for `auto-improve`

### Pattern Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `workflow` | Repeated action sequences | TDD loop, spec→plan→implement |
| `code` | Code style/structure patterns | Naming conventions, file organization |
| `decision` | Recurring decision patterns | Tool choices, architecture decisions |
| `communication` | Interaction patterns | Question types, clarification needs |

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `hooks/session-stop.py` | Create | Post-exit pattern extraction hook |
| `zie-framework/project/session-memory-format.md` | Create | Session memory JSON schema (shared with auto-inject) |
| `zie-framework/project/pattern-extraction.md` | Create | Pattern detection algorithm docs |
| `zie-framework/project/pattern-categories.md` | Create | Pattern category definitions |
| `hooks/hooks.json` | Modify | Register session-stop post-exit hook |

## Testing

### Unit Tests (`make test-unit`)

- `test_session_stop_captures_transcript()` — transcript capture correctness
- `test_pattern_extraction_heuristic()` — frequency-based pattern detection
- `test_pattern_confidence_scoring()` — confidence calculation accuracy
- `test_session_memory_schema()` — JSON schema validation
- `test_auto_apply_threshold()` — 0.95 threshold boundary cases

### Integration Tests

- Session end → memory file created
- Multiple patterns extracted and scored
- High-confidence patterns marked for auto-apply
- Session memory retrievable by `auto-inject`

## Dependencies

- None (foundational feature)
- Enables: `auto-decide`, `auto-improve`

## Rollout Plan

1. **Phase 1:** Basic session capture (transcript + stats)
2. **Phase 2:** Heuristic pattern extraction
3. **Phase 3:** LLM-based extraction (optional)
4. **Phase 4:** Confidence scoring + auto-apply marking

## Success Criteria

- [ ] Session memory file created on every session end
- [ ] Patterns extracted with ≥80% precision (user-validated)
- [ ] High-confidence patterns correctly identified (≥0.95)
- [ ] Session memory retrievable by `auto-inject`
- [ ] Zero impact on session performance (<1s overhead)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Pattern extraction slow | Run async, don't block session end |
| Wrong patterns extracted | Low threshold, require high confidence for auto-apply |
| Memory file bloat | Rotate old sessions (>90 days) |
| Privacy concerns | Local-only storage, transcript optional |
