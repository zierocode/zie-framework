---
approved: true
backlog: backlog/auto-inject.md
---

# Auto-Inject — Context พร้อมเมื่อ Session เริ่ม

## Summary

Auto-load context at Claude Code session start. Retrieve previous session memory, perform keyword-based context retrieval, and present a summary with optional "Continue?" prompt. Eliminates need for manual `/load-context` or `/status` commands.

## Motivation

Currently, every new session starts fresh. Users must manually run `/load-context` or `/status` to load project context and previous session state. This creates friction and cognitive load—users must remember to load context and know what was happening last time.

Auto-inject makes context available immediately when a session starts, allowing users to "just continue" without manual setup.

## Scope

### In Scope

1. **Hook: `hooks/session-start.py`** (new)
   - Triggered on session initialization (via pre-prompt hook)
   - Loads previous session memory from `.zie/memory/`
   - Performs keyword-based context retrieval from project knowledge
   - Outputs context summary at session start

2. **Session Memory Loading**
   - Read most recent `.zie/memory/session-*.json` file
   - Parse session summary, patterns, active tasks
   - Inject into initial system prompt context

3. **Keyword-Based Context Retrieval**
   - Extract keywords from recent conversation (if any) or use project defaults
   - Search `.zie/project/` knowledge docs for relevant context
   - Rank by relevance, inject top-N results

4. **Context Summary Presentation**
   - Display: previous session state, active tasks, relevant context
   - Optional prompt: "Continue from last session?" (non-blocking)

5. **Configuration** (in `zie-framework/project/config-reference.md`)
   - `auto-inject.enabled` (default: true)
   - `auto-inject.max-context-docs` (default: 5)
   - `auto-inject.prompt-continue` (default: false — non-blocking)

### Out of Scope

- Manual `/load-context` command removal (remains available)
- Cross-project context injection
- Real-time context updates during session

## Technical Design

### Hook Integration

```
session-start.py (pre-prompt hook)
├── Load previous session memory
│   └── .zie/memory/session-YYYYMMDD-HHMMSS.json
├── Keyword extraction
│   └── From: last N messages OR project defaults
├── Context retrieval
│   └── Search: .zie/project/*.md
└── Inject into prompt
    └── Format: markdown summary block
```

### Session Memory Schema

```json
{
  "session_id": "20260414-093000",
  "timestamp": "2026-04-14T09:30:00Z",
  "summary": "Brief session summary",
  "active_tasks": ["task-1", "task-2"],
  "patterns": [...],
  "context_keywords": ["keyword1", "keyword2"]
}
```

### Context Retrieval Algorithm

1. Tokenize keywords from last session summary
2. TF-IDF score against `.zie/project/*.md` documents
3. Return top-N documents (configurable, default 5)
4. Inject as markdown block with links to full docs

### Output Format

```markdown
## Previous Session (2026-04-14 09:30)

**Summary:** Implementing auto-inject context feature

**Active Tasks:**
- [IN_PROGRESS] hooks/session-start.py — context loading
- [PENDING] Context retrieval algorithm

**Relevant Context:**
- session-memory-format.md — memory JSON schema
- hook-conventions.md — hook output conventions

> Continue from last session? (type "yes" to load full state)
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `hooks/session-start.py` | Create | Pre-prompt context injection hook |
| `zie-framework/project/session-memory-format.md` | Create | Session memory JSON schema docs |
| `zie-framework/project/context-retrieval.md` | Create | Keyword-based retrieval algorithm |
| `zie-framework/project/config-reference.md` | Modify | Add auto-inject config keys |
| `hooks/hooks.json` | Modify | Register session-start pre-prompt hook |

## Testing

### Unit Tests (`make test-unit`)

- `test_session_start_loads_memory()` — verify memory file loading
- `test_session_start_no_memory()` — graceful handling when no prior session
- `test_keyword_extraction()` — keyword tokenization from text
- `test_context_retrieval_ranking()` — TF-IDF scoring correctness
- `test_context_summary_format()` — output format validation

### Integration Tests

- Fresh session start → context injected automatically
- No prior session → no errors, clean start
- Multiple sessions → correct (most recent) memory loaded

## Dependencies

- `unified-context-cache` (ADR-XXX) — context caching layer
- Session memory format (to be defined in `auto-learn` spec)

## Rollout Plan

1. **Phase 1:** Basic memory loading (no context retrieval)
2. **Phase 2:** Keyword-based context retrieval
3. **Phase 3:** Configurable options + continue prompt
4. **Phase 4:** Documentation + user guide update

## Success Criteria

- [ ] Context auto-injected within 2s of session start
- [ ] Previous session state visible immediately
- [ ] Relevant context docs surfaced (user-validated)
- [ ] Zero errors when no prior session exists
- [ ] Manual `/load-context` still functional

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Slow session start | Cache context, lazy-load full docs |
| Wrong context injected | Show source links, allow dismiss |
| Memory file corruption | Graceful fallback, skip corrupted files |
| Privacy concerns | Local-only storage, no external transmission |
