---
approved: true
approved_at: 2026-04-14
backlog: backlog/context-loader-sprint.md
---

# Context Loader Sprint — Auto-load zie-framework context at session start

**Problem:** Claude Code ต้องลองผิดลองถูกกับ commands/skills ของ zie-framework เพราะไม่มี context กลางที่โหลดอัตโนมัติ ทำให้เสียเวลาและ tokens ในการ discover

**Approach:** SessionStart hook โหลด context bundle ครั้งเดียวแล้ว cache ทั้ง session, inject เป็น additionalContext ให้ Claude รู้ command/skill structure ตั้งแต่เริ่ม

**Components:**
- Create: `hooks/zie-context-loader.py` — standalone module; exports `build_context_map(cwd: Path) -> dict` with keys: `commands: [{name, file, path}]`, `skills: [{name, path}]`; scans commands/*.md, skills/*/SKILL.md; wrapped in `try/except` with `sys.exit(0)` on failure (hook safety pattern per ADR-009)
- Modify: `hooks/session-resume.py` — extract existing inline command map logic (lines 201-245) to `zie-context-loader.py`, then import and call it
- Reuse: `.zie/cache/session-cache.json` — existing unified cache location (via utils_cache.py)
- Reuse: `hooks/utils_cache.py` — `get_cache_manager(cwd).get_or_compute(key, session_id, fn, ttl)` with cache key format `session:{session_id}:command_map:{skill_mtime}` for mtime-gate (ADR-045)
- Reuse: `hooks/intent-sdlc.py` — reads command map from session cache (no modification needed)

**Acceptance Criteria:**
- Context loads in <2s at session start (measured by hook timing log)
- Command map loads in <2s on cold start, <100ms on cache hit (measured by hook timing log)
- Downstream hooks (intent-sdlc.py) call cache.get_or_compute() not direct file reads (verified by code audit after implementation)
- Context injected in session-resume output for all sessions (verified by stdout check)

**Data Flow:**
1. SessionStart → hooks/session-resume.py calls build_context_map() from zie-context-loader.py
2. zie-context-loader.py scans commands/*.md, skills/*/SKILL.md
3. Extract from each file: name (from filename/slug), type (command/skill), path; for skills at `skills/<skill-name>/SKILL.md`, extract `<skill-name>` from parent directory name
4. Build context.md with command map table + skill list
5. Compute cache key: `session:{session_id}:command_map:{skill_mtime}` (includes session_id + SKILL.md mtime for automatic invalidation per ADR-045)
6. Write to `.zie/cache/session-cache.json` via utils_cache.get_or_compute(key, session_id, fn, ttl=1800)
7. Inject as additionalContext ใน session-resume → Claude รู้ framework structure ตั้งแต่เริ่ม
8. Subsequent hooks (intent-sdlc.py) use cache.get_or_compute() → zero full file content reads

**Edge Cases:**
- zie-framework folder missing → skip silently, print advisory
- Cache write failed → log warning, build context in-memory for this session only (no persistence), retry cache write on next session
- SKILL.md mtime changed → cache invalidates automatically (utils_cache.py checks mtime before returning cached value)

**Out of Scope:**
- MCP server config (ใช้ hook แทน)
- แก้ command/skill ทุกตัว (context โหลดอัตโนมัติที่ session start)
