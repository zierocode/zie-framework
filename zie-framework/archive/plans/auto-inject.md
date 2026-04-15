---
approved: true
spec: specs/2026-04-14-auto-inject-design.md
---

# Auto-Inject — Implementation Plan

## Overview

Auto-load context at Claude Code session start. Retrieve previous session memory, perform keyword-based context retrieval, present summary.

## Tasks

### Phase 1: Session Memory Format

1. **Define session memory schema**
   - File: `zie-framework/project/session-memory-format.md`
   - JSON schema: `session_id`, `summary`, `active_tasks`, `patterns`, `context_keywords`
   - Location: `.zie/memory/session-YYYYMMDD-HHMMSS.json`

### Phase 2: Context Retrieval Algorithm

2. **Create context retrieval module**
   - File: `zie-framework/project/context-retrieval.md`
   - Algorithm: TF-IDF scoring against `.zie/project/*.md`
   - Return top-N docs (configurable, default 5)

### Phase 3: Session Start Hook

3. **Create `hooks/session-start.py`**
   - Trigger: pre-prompt hook
   - Functions:
     - `load_previous_session()` — find most recent memory file
     - `extract_keywords(text)` — tokenize session summary
     - `retrieve_context(keywords, max_docs=5)` — TF-IDF search
     - `format_summary(session, context_docs)` — markdown output
   - Output: context summary block injected at session start

### Phase 4: Hook Registration

4. **Update `hooks/hooks.json`**
   - Register `session-start` as pre-prompt hook

### Phase 5: Configuration

5. **Update `zie-framework/project/config-reference.md`**
   - Add config keys:
     - `auto-inject.enabled` (default: true)
     - `auto-inject.max-context-docs` (default: 5)
     - `auto-inject.prompt-continue` (default: false)

### Phase 6: Testing

6. **Unit tests**
   - `test_session_start.py`:
     - `test_loads_memory()`
     - `test_no_memory_graceful()`
     - `test_keyword_extraction()`
     - `test_context_retrieval_ranking()`
     - `test_context_summary_format()`

7. **Integration tests**
   - Fresh session start → context injected
   - No prior session → no errors
   - Multiple sessions → correct memory loaded

## Acceptance Criteria

- [ ] Context auto-injected within 2s of session start
- [ ] Previous session state visible immediately
- [ ] Relevant context docs surfaced
- [ ] Zero errors when no prior session
- [ ] Manual `/load-context` still functional

## Dependencies

- `unified-context-cache` (ADR-XXX)

## Rollout

1. Define session memory schema
2. Create context retrieval algorithm
3. Build session-start hook
4. Register hook + add config
5. Test with fresh + existing sessions
