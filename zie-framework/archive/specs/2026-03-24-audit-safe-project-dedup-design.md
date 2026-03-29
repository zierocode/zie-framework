---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-safe-project-dedup.md
---

# Safe Project Sanitization Deduplication — Design Spec

**Problem:** `session-cleanup.py` inlines its own copy of the `re.sub(r'[^a-zA-Z0-9]', '-', project)` sanitization logic instead of calling `utils.project_tmp_path()`, creating a silent divergence risk if the canonical rule ever changes.

**Approach:** Replace the inline `safe_project` derivation in `session-cleanup.py` with a call to a new thin helper `safe_project_name(project: str) -> str` extracted from `utils.project_tmp_path()`. `session-cleanup.py` then calls `safe_project_name(cwd.name)` to build its glob pattern. `project_tmp_path()` is refactored to call the same helper internally, keeping both paths in sync.

**Components:**
- `hooks/utils.py` — extract `safe_project_name()` as a public helper; refactor `project_tmp_path()` to use it
- `hooks/session-cleanup.py` — replace inline `re.sub` + `safe_project` with `safe_project_name(cwd.name)`

**Data Flow:**
1. `session-cleanup.py` imports `safe_project_name` from `utils`
2. Calls `safe_project_name(cwd.name)` to get the sanitized string
3. Uses result to build the glob pattern `f"zie-{safe_project}-*"`
4. All other hooks that call `project_tmp_path()` inherit the same rule automatically

**Edge Cases:**
- Project name is empty string — `safe_project_name("")` returns `""`, glob becomes `"zie--*"`; behavior unchanged from current code
- Project name already alphanumeric — no change in output
- Future rule change (e.g., lowercase normalization) — one edit to `safe_project_name()` propagates everywhere

**Out of Scope:**
- Changing the sanitization rule itself
- Handling symlinked or aliased project paths
- Adding tests beyond the existing `test_utils.py` coverage
