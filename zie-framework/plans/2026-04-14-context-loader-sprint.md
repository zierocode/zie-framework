---
approved: true
approved_at: 2026-04-14
backlog: backlog/context-loader-sprint.md
---

# Context Loader Sprint — Implementation Plan

**Goal:** สร้าง context loader ที่ scan commands/skills และ cache ผลลัพธ์ทั้ง session เพื่อลด disk reads

**Architecture:** แยก command map logic จาก session-resume.py ไปเป็น zie-context-loader.py standalone module; ใช้ utils_cache.py session cache พร้อม mtime-gate invalidation

**Tech Stack:** Python 3.x, hooks/utils_cache.py (session cache), hooks/session-resume.py (SessionStart hook)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/zie_context_loader.py` | Scan commands/, skills/, build command map, write to session cache (file already exists) |
| Modify | `hooks/session-resume.py` | Import และเรียก use zie_context_loader แทน inline logic (already done) |
| Modify | `tests/test_context_loader.py` | Unit tests สำหรับ zie_context_loader.py (file already exists with 9 tests) |

---

## Task 1: Modify zie_context_loader.py (already exists)

**Acceptance Criteria:**
- Module exports `build_context_map(cwd: Path) -> dict` ที่ return `{commands: [...], skills: [...]}`
- มี try/except guard พร้อม sys.exit(0) on failure (ADR-009)
- Scan commands/*.md และ skills/*/SKILL.md ได้ถูกต้อง

**Files:**
- Create: `hooks/zie_context_loader.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/test_context_loader.py
  def test_build_context_map_returns_dict():
      from hooks.zie_context_loader import build_context_map
      from pathlib import Path
      result = build_context_map(Path.cwd())
      assert isinstance(result, dict)
      assert "commands" in result
      assert "skills" in result
  ```
  Run: `make test-unit` — must FAIL (module doesn't exist yet)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/zie-context-loader.py
  #!/usr/bin/env python3
  """zie-context-loader — Scan commands/skills, build command map, cache per session."""
  import os
  import sys
  from pathlib import Path
  
  def build_context_map(cwd: Path) -> dict:
      """Scan commands/ and skills/, return {commands: [{name, file, path}], skills: [{name, path}]}."""
      commands = []
      skills = []
      
      # Scan commands/*.md
      commands_dir = cwd / "commands"
      if commands_dir.exists():
          for f in commands_dir.glob("*.md"):
              commands.append({
                  "name": f"/{f.stem}",
                  "file": f.name,
                  "path": str(f.relative_to(cwd))
              })
      
      # Scan skills/*/SKILL.md
      skills_dir = cwd / "skills"
      if skills_dir.exists():
          for skill_dir in skills_dir.iterdir():
              if skill_dir.is_dir():
                  skill_file = skill_dir / "SKILL.md"
                  if skill_file.exists():
                      skills.append({
                          "name": skill_dir.name,
                          "path": str(skill_file.relative_to(cwd))
                      })
      
      return {"commands": commands, "skills": skills}
  
  if __name__ == "__main__":
      try:
          context = build_context_map(Path.cwd())
          print(f"Commands: {len(context['commands'])}")
          print(f"Skills: {len(context['skills'])}")
          sys.exit(0)
      except Exception:
          sys.exit(0)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - เพิ่ม docstring ให้แต่ละ function
  - แยก scan_commands() และ scan_skills() เป็น helper functions
  Run: `make test-unit` — still PASS

---

## Task 2: Integrate with session cache

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Cache key format: `session:{session_id}:command_map:{skill_mtime}`
- ใช้ utils_cache.get_or_compute() พร้อม TTL 1800s
- SKILL.md mtime เปลี่ยน → cache invalidates

**Files:**
- Modify: `hooks/zie-context-loader.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/test_context_loader.py
  def test_cache_key_includes_session_id():
      import os
      os.environ["CLAUDE_SESSION_ID"] = "test-123"
      from hooks.zie_context_loader import _build_cache_key
      key = _build_cache_key(1234567890.0)  # skill_mtime
      assert "session:test-123" in key
      assert "command_map" in key
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/zie-context-loader.py (เพิ่ม)
  import time
  
  def _get_skill_mtime(cwd: Path) -> float:
      """Get SKILL.md mtime for cache invalidation."""
      skill_path = cwd / "skills" / "using-zie-framework" / "SKILL.md"
      if skill_path.exists():
          return skill_path.stat().st_mtime
      return 0.0
  
  def _build_cache_key(skill_mtime: float) -> str:
      """Build session-scoped cache key with mtime-gate."""
      session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
      return f"session:{session_id}:command_map:{skill_mtime}"
  
  def get_cached_context(cwd: Path) -> dict:
      """Get command map from session cache, or build if missing."""
      from hooks.utils_cache import get_cache_manager
      skill_mtime = _get_skill_mtime(cwd)
      cache_key = _build_cache_key(skill_mtime)
      session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
      cache = get_cache_manager(cwd)
      return cache.get_or_compute(
          cache_key, session_id, lambda: build_context_map(cwd), ttl=1800
      )
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - ย้าย import ไปไว้บนสุด
  - เพิ่ม type hints
  Run: `make test-unit` — still PASS

---

## Task 3: Update session-resume.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- session-resume.py เรียกใช้ get_cached_context() แทน inline command map logic
- Inject command map เป็น additionalContext ใน output
- บรรทัด 201-245 (inline command map) ถูกลบออก

**Files:**
- Modify: `hooks/session-resume.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/test_session_resume.py
  def test_session_resume_uses_context_loader():
      import ast
      with open("hooks/session-resume.py") as f:
          content = f.read()
      assert "from hooks.zie_context_loader import" in content or \
             "from hooks import zie_context_loader" in content
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/session-resume.py (แก้)
  from hooks.zie_context_loader import get_cached_context
  
  # แทนที่บรรทัด 201-245 ด้วย:
  try:
      context = get_cached_context(cwd)
      cmd_line = f"[zie-framework] commands — {' '.join(c['name'] for c in context['commands'])}"
      skill_line = f"[zie-framework] skills — {' '.join(s['name'] for s in context['skills'])}"
      print(cmd_line)
      print(skill_line)
  except Exception:
      print("[zie-framework] framework: commands — /backlog /spec /plan /implement ...")
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - ลบ inline command map parsing code (บรรทัด 201-245)
  - เพิ่ม error handling ให้ print fallback
  Run: `make test-unit` — still PASS

---

## Task 4: Add edge case handling

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- zie-framework folder missing → skip silently, print advisory
- Cache write failed → log warning, use in-memory fallback

**Files:**
- Modify: `hooks/zie-context-loader.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/test_context_loader.py
  def test_missing_zie_framework_returns_empty():
      from hooks.zie_context_loader import build_context_map
      from pathlib import Path
      import tempfile
      with tempfile.TemporaryDirectory() as tmp:
          result = build_context_map(Path(tmp))
          assert result == {"commands": [], "skills": []}
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/zie-context-loader.py (เพิ่ม guard)
  def get_cached_context(cwd: Path) -> dict:
      """Get command map from session cache, or build if missing."""
      try:
          from hooks.utils_cache import get_cache_manager
          skill_mtime = _get_skill_mtime(cwd)
          cache_key = _build_cache_key(skill_mtime)
          session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
          cache = get_cache_manager(cwd)
          return cache.get_or_compute(
              cache_key, session_id, lambda: build_context_map(cwd), ttl=1800
          )
      except Exception as e:
          print(f"[zie-framework] context-loader: cache failed: {e}", file=sys.stderr)
          return build_context_map(cwd)  # Fallback to direct build
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - เพิ่ม logging ให้สอดคล้องกับ ADR-038 (hook timing)
  Run: `make test-unit` — still PASS

---

## Task 5: Add tests for integration

<!-- depends_on: Task 1, Task 2, Task 4 -->

**Acceptance Criteria:**
- มี test file `tests/test_context_loader.py` พร้อม 5+ tests
- Tests cover: basic scan, cache key, missing folder, edge cases

**Files:**
- Create: `tests/test_context_loader.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/test_context_loader.py — full test file
  # 5+ tests as described in tasks 1-4
  ```
  Run: `make test-unit` — must FAIL (file doesn't exist)

- [ ] **Step 2: Implement (GREEN)**
  - Write complete test file รวมทุก tests จาก tasks ข้างต้น
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - ใช้ fixtures สำหรับ temp directories
  - เพิ่ม integration test ที่ run hook จริง
  Run: `make test-unit` — still PASS
