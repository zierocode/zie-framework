---
approved: true
approved_at: 2026-04-13
backlog: backlog/intent-sdlc-context-dedup.md
---

# intent-sdlc: Deduplicate Same-Context Injection Per Session — Design Spec

**Problem:** `hooks/intent-sdlc.py` fires on every `UserPromptSubmit` event. When the same SDLC intent + stage is active across multiple consecutive turns (e.g., repeated questions during an implement session), the hook emits identical `additionalContext` JSON on every turn — wasting ~150-200 tokens per message with no new information.

**Approach:** Add a module-level in-process cache (`dict[str, str]`) keyed on `session_id`. Before emitting `additionalContext`, compute a short dedup key from the tuple `(intent_cmd, stage, active_task[:40])`. If the same key was emitted in this session → exit 0 silently (no re-injection). After emitting → store the key. This is in-process only (no disk), resets per session restart, and adds zero disk I/O.

**Non-goals:** We are NOT caching the ROADMAP read (already handled by `read_roadmap_cached` with 30s TTL). We are NOT preventing injection on first occurrence, or when context changes.

**Components:**
- Modify: `hooks/intent-sdlc.py` — add `_last_context_key: dict[str, str]` cache; insert dedup check before `print(json.dumps(...))` call
- Modify: `tests/unit/test_intent_sdlc.py` — add test: same context → second call exits 0 with no output; different context → re-emits

**Data Flow:**
1. Hook fires, detects SDLC intent → computes dedup_key from `(intent_cmd, stage, active_task[:40])`
2. If `_last_context_key.get(session_id) == dedup_key` → `sys.exit(0)`
3. If different → emit context, update `_last_context_key[session_id] = dedup_key`

**Acceptance Criteria:**
- AC1: When hook fires twice in same session with same intent+stage+active_task → second call emits no output
- AC2: When stage or active_task changes → hook re-emits normally
- AC3: Cache is module-level (in-process only); no disk writes
- AC4: All existing intent-sdlc tests continue to pass
- AC5: Test added for dedup behavior (same context → no second emission)
