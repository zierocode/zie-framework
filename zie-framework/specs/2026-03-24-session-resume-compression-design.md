---
approved: true
approved_at: 2026-03-24
backlog: backlog/session-resume-compression.md
---

# Session-Resume Hook Output Compression — Design Spec

**Problem:** `session_resume.py` fires on every SessionStart and prints 20+ lines of project state into the context window before any user prompt is processed — consuming tokens every session regardless of what the user intends to do.

**Approach:** Compress hook output to exactly 4 lines covering the essential session-start facts. Everything else is available on demand via `/zie-status`. The 4-line format is specified in the backlog:
```
[zie-framework] <project> (<type>) v<version>
  Active: <feature name or "No active feature — run /zie-backlog to start one">
  Brain: <enabled|disabled>
  → Run /zie-status for full state
```

**Components:**
- Modify: `hooks/session_resume.py` — replace current multi-section output with 4-line format; keep all existing data-gathering logic (it feeds `/zie-status`); only the print statements change

**Acceptance Criteria:**
- [ ] Hook output is ≤4 lines on every SessionStart
- [ ] Output includes: project name + type + version, active feature (or "No active feature"), brain status, /zie-status hint
- [ ] `/zie-status` output is unchanged (still shows full detail)
- [ ] Hook still exits 0 and never blocks Claude
- [ ] Output format matches the 4-line spec exactly

**Out of Scope:**
- Changing what `/zie-status` shows
- Changing any other hooks
