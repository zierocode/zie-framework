---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-exception-handling-inconsistency.md
spec: specs/2026-03-24-audit-exception-handling-inconsistency-design.md
---

# Standardize Hook Exception Handling Convention — Implementation Plan

**Goal:** Document the two-tier exception handling convention in `CLAUDE.md` and confirm all hooks comply, making one targeted fix to `session-resume.py`'s config-load bare `pass` (which is also covered by `audit-silent-config-parse-failures`, but the convention doc is owned here).
**Architecture:** The convention is: (1) outer guard catches silently and calls `sys.exit(0)` — never blocks Claude; (2) inner operations catch with `except Exception as e` and print `[zie-framework] <hook>: <e>` to stderr. A new "Hook Error Handling Convention" section is added to `CLAUDE.md`. The only code change is the `session-resume.py` config-load except (if not already fixed by the silent-config-parse-failures plan). All other hooks already comply per the spec audit.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `CLAUDE.md` | Add "Hook Error Handling Convention" section under Key Rules |
| Modify | `hooks/session-resume.py` | Fix bare `pass` in config-load except (if not already done) |
| Modify | `tests/unit/test_hooks_session_resume.py` | Add convention-compliance test |

## Task 1: Document the convention in `CLAUDE.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `CLAUDE.md` contains a "Hook Error Handling Convention" section under "Key Rules"
- The section describes the two-tier pattern: outer guard = silent exit; inner operations = stderr log
- The `[zie-framework] <hook-name>: <e>` format is documented

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # No automated test for CLAUDE.md content — this task is documentation only.
  # The RED signal is a manual check: grep for "Hook Error Handling" in CLAUDE.md
  # and confirm it is absent before the change.
  #
  # Automated proxy test: verify the section heading exists after the change.

  # tests/unit/test_hooks_session_resume.py — add at end of file
  # (This test covers the convention rule, not just session-resume specifically)

  class TestHookExceptionConvention:
      def test_claude_md_documents_hook_error_convention(self):
          """CLAUDE.md must contain the Hook Error Handling Convention section."""
          import os
          repo_root = os.path.abspath(
              os.path.join(os.path.dirname(__file__), "..", "..")
          )
          claude_md = os.path.join(repo_root, "CLAUDE.md")
          content = open(claude_md).read()
          assert "Hook Error Handling" in content, (
              "CLAUDE.md missing 'Hook Error Handling' section — convention not documented"
          )
  ```
  Run: `make test-unit` — must FAIL (section absent from `CLAUDE.md`)

- [ ] **Step 2: Implement (GREEN)**
  Add the following section to `CLAUDE.md` under `## Key Rules`, after the existing bullet list:

  ```markdown
  ## Hook Error Handling Convention

  All hooks follow a two-tier pattern:

  1. **Outer guard** — event parse + early-exit checks. Use bare `except Exception` →
     `sys.exit(0)`. This tier must _never_ block Claude regardless of input.
  2. **Inner operations** — file I/O, API calls, subprocess. Use
     `except Exception as e: print(f"[zie-framework] <hook-name>: {e}", file=sys.stderr)`.
     Hook still exits 0 after logging; Claude is never blocked.

  Never raise an unhandled exception from a hook. Never use a non-zero exit code.
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No code refactor needed. Confirm the heading text exactly matches `"Hook Error Handling"`.
  Run: `make test-unit` — still PASS

## Task 2: Verify all hooks comply — fix any remaining bare `pass`

<!-- depends_on: none -->

**Acceptance Criteria:**
- No hook file contains a bare `except Exception: pass` in an inner operation block
- `session-resume.py` config-load uses the logging pattern (may already be done by `audit-silent-config-parse-failures` plan)
- All existing hook tests pass

**Files:**
- Modify: `hooks/session-resume.py` (if not already updated)

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hooks_session_resume.py — add inside TestHookExceptionConvention class

      def test_no_bare_pass_in_session_resume_inner_ops(self):
          """session-resume.py must not contain bare 'except Exception: pass' blocks."""
          import os, ast
          repo_root = os.path.abspath(
              os.path.join(os.path.dirname(__file__), "..", "..")
          )
          src = open(os.path.join(repo_root, "hooks", "session-resume.py")).read()
          tree = ast.parse(src)
          for node in ast.walk(tree):
              if isinstance(node, ast.ExceptHandler):
                  # A bare pass: handler body is exactly one Pass node, no 'as' binding
                  if (
                      node.name is None
                      and len(node.body) == 1
                      and isinstance(node.body[0], ast.Pass)
                  ):
                      # Only flag if NOT at the top-level outer guard
                      # (outer guard is the very first try block — line ~12)
                      # We check line number: outer guard is before line 20
                      if node.lineno > 20:
                          raise AssertionError(
                              f"Bare 'except: pass' found at line {node.lineno} "
                              "in session-resume.py — inner ops must log to stderr"
                          )
  ```
  Run: `make test-unit` — must FAIL (bare `pass` at config-load line 28 is > line 20)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/session-resume.py — replace config-load except clause (lines 25-29)
  # (Same change as audit-silent-config-parse-failures Task 2 — idempotent if already applied)

  # OLD:
  #     except Exception:
  #         pass

  # NEW:
      except Exception as e:
          print(f"[zie] warning: .config unreadable ({e}), using defaults", file=sys.stderr)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Run the AST check mentally against `auto-test.py` (line 73 outer guard is inside `if __name__ == "__main__"`, which is fine), `session-learn.py`, `wip-checkpoint.py`, `session-cleanup.py`, and `intent-detect.py` — all already comply per spec audit.
  Run: `make test-unit` — still PASS

---
*Commit: `git add CLAUDE.md hooks/session-resume.py tests/unit/test_hooks_session_resume.py && git commit -m "fix: document hook error handling convention, fix session-resume bare pass"`*
