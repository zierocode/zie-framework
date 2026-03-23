---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-intent-detect-redos.md
---

# Intent-Detect ReDoS Input Guard — Design Spec

**Problem:** `intent-detect.py` has no maximum-length guard on the incoming `message` before running 96 compiled regex patterns against it, creating a ReDoS exposure for adversarially crafted or pathologically long prompts.

**Approach:** Add a hard character-length cap (e.g., 1000 chars) applied to `message` immediately after the existing `len(message) < 3` check and before pattern matching. The existing `len(message) > 500` early-exit already catches command content; the new guard is a safety ceiling that short-circuits before any regex runs. The cap is defined as a named constant `MAX_MESSAGE_LEN` at the top of the file for easy tuning.

**Components:**
- `hooks/intent-detect.py` — add `MAX_MESSAGE_LEN = 1000` constant and early-exit guard after line 16

**Data Flow:**
1. Event parsed; `message` extracted and lowercased (existing)
2. `len(message) < 3` check (existing)
3. **NEW:** `len(message) > MAX_MESSAGE_LEN` → `sys.exit(0)`
4. `message.startswith("---") or len(message) > 500` check (existing, kept as-is)
5. Pattern matching proceeds on bounded input

**Edge Cases:**
- Legitimate long prompts (e.g., pasted code) — already handled by the existing `> 500` exit; new guard adds a redundant backstop only
- Thai multibyte characters — `len()` counts code points in Python 3, not bytes; cap is intentionally generous at 1000
- Empty or whitespace-only message — caught by existing `< 3` check before reaching new guard

**Out of Scope:**
- Auditing or replacing individual regex patterns for catastrophic backtracking
- Changing the suggestion threshold or scoring logic
- Per-pattern timeout/deadline enforcement
