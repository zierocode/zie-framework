---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-intent-detect-regex-recompile.md
spec: specs/2026-03-24-audit-intent-detect-regex-recompile-design.md
---

# Intent-Detect Module-Level Regex Compilation — Implementation Plan

**Goal:** Move `PATTERNS` and `COMPILED_PATTERNS` from inside the script body to module-level constants so Python's `.pyc` bytecode cache can avoid re-parsing pattern strings on subsequent invocations.
**Architecture:** Both dicts are hoisted above all conditional logic (after imports, before any `if` statement). The scoring loop that iterates over `COMPILED_PATTERNS` is unchanged. No logic changes; only placement changes. The existing `TestIntentDetectCompiledPatterns` test already asserts `hasattr(mod, "COMPILED_PATTERNS")` and will serve as the GREEN signal.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/intent-detect.py` | Move `PATTERNS` and `COMPILED_PATTERNS` to module top-level (after imports) |
| Modify | `tests/unit/test_hooks_intent_detect.py` | Add test confirming `PATTERNS` is also at module level and has expected category count |

## Task 1: Hoist `PATTERNS` and `COMPILED_PATTERNS` to module level

<!-- depends_on: none -->

**Acceptance Criteria:**
- `PATTERNS` is defined before any `if` or `try` statement in the module (after imports)
- `COMPILED_PATTERNS` is defined immediately after `PATTERNS` at module level
- The number of categories in `PATTERNS` remains 9 (`init`, `backlog`, `spec`, `plan`, `implement`, `fix`, `release`, `retro`, `status`)
- All `TestIntentDetect*` tests pass unchanged
- `TestIntentDetectCompiledPatterns.test_compiled_patterns_exist_at_module_level` continues to pass

**Files:**
- Modify: `hooks/intent-detect.py`
- Modify: `tests/unit/test_hooks_intent_detect.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hooks_intent_detect.py — add inside TestIntentDetectCompiledPatterns class

      def test_patterns_dict_at_module_level_with_correct_categories(self, tmp_path):
          """PATTERNS must be a module-level dict with all 9 expected categories."""
          import importlib.util, io, os, sys
          (tmp_path / "zie-framework").mkdir()
          hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
          spec = importlib.util.spec_from_file_location("intent_detect_recompile", hook)
          mod = importlib.util.module_from_spec(spec)
          original_stdin = sys.stdin
          original_env = os.environ.copy()
          try:
              sys.stdin = io.StringIO('{"prompt": "hello world neutral text here"}')
              os.environ["CLAUDE_CWD"] = str(tmp_path)
              try:
                  spec.loader.exec_module(mod)
              except SystemExit:
                  pass
          finally:
              sys.stdin = original_stdin
              os.environ.clear()
              os.environ.update(original_env)

          assert hasattr(mod, "PATTERNS"), "PATTERNS not found at module level"
          expected_categories = {
              "init", "backlog", "spec", "plan",
              "implement", "fix", "release", "retro", "status",
          }
          assert set(mod.PATTERNS.keys()) == expected_categories, (
              f"PATTERNS categories mismatch: {set(mod.PATTERNS.keys())}"
          )

      def test_compiled_patterns_count_matches_patterns(self, tmp_path):
          """COMPILED_PATTERNS must have same keys as PATTERNS."""
          import importlib.util, io, os, sys
          (tmp_path / "zie-framework").mkdir()
          hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
          spec = importlib.util.spec_from_file_location("intent_detect_recompile2", hook)
          mod = importlib.util.module_from_spec(spec)
          original_stdin = sys.stdin
          original_env = os.environ.copy()
          try:
              sys.stdin = io.StringIO('{"prompt": "neutral message for testing purposes"}')
              os.environ["CLAUDE_CWD"] = str(tmp_path)
              try:
                  spec.loader.exec_module(mod)
              except SystemExit:
                  pass
          finally:
              sys.stdin = original_stdin
              os.environ.clear()
              os.environ.update(original_env)

          assert hasattr(mod, "COMPILED_PATTERNS"), "COMPILED_PATTERNS not at module level"
          assert set(mod.COMPILED_PATTERNS.keys()) == set(mod.PATTERNS.keys()), (
              "COMPILED_PATTERNS keys must match PATTERNS keys"
          )
  ```
  Run: `make test-unit` — The `test_patterns_dict_at_module_level_with_correct_categories` test passes vacuously if `PATTERNS` is already accessible (it is — module-level code runs during `exec_module`). The real RED signal is verified by checking the *position* of `PATTERNS` in the source file. Use a source-inspection test:

  ```python
      def test_patterns_defined_before_any_conditional(self):
          """PATTERNS must appear before any if/try block in the source file."""
          import os, ast
          hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
          src = open(hook).read()
          tree = ast.parse(src)

          patterns_line = None
          first_conditional_line = None

          for node in ast.walk(tree):
              if isinstance(node, ast.Assign):
                  for target in node.targets:
                      if isinstance(target, ast.Name) and target.id == "PATTERNS":
                          patterns_line = node.lineno
              if isinstance(node, (ast.If, ast.Try)) and first_conditional_line is None:
                  first_conditional_line = node.lineno

          assert patterns_line is not None, "PATTERNS assignment not found"
          assert first_conditional_line is not None, "No conditional found (unexpected)"
          assert patterns_line < first_conditional_line, (
              f"PATTERNS (line {patterns_line}) must be defined before first "
              f"conditional (line {first_conditional_line})"
          )
  ```
  Run: `make test-unit` — must FAIL (`PATTERNS` is currently at line 33 which is *after* the `try` block at line 9)

- [ ] **Step 2: Implement (GREEN)**
  Restructure `hooks/intent-detect.py` so that `PATTERNS`, `COMPILED_PATTERNS`, and `SUGGESTIONS` are declared immediately after the `import` statements and before the `try: event = json.loads(...)` outer guard. The final file structure is:

  ```python
  #!/usr/bin/env python3
  """UserPromptSubmit hook — detect SDLC intent and suggest the right /zie-* command."""
  import sys
  import json
  import os
  import re
  from pathlib import Path

  # ── Module-level constants (compiled once, cached in .pyc) ──────────────────

  PATTERNS = {
      "init": [
          r"\binit\b", r"เริ่มต้น.*project", r"ตั้งค่า.*project",
          r"setup.*project", r"bootstrap",
      ],
      "backlog": [
          r"อยากทำ", r"อยากได้", r"อยากเพิ่ม", r"อยากสร้าง",
          r"\bidea\b", r"\bfeature\b", r"new feature", r"เพิ่ม.*feature",
          r"สร้าง.*ใหม่", r"want to (build|add|create|make)",
          r"ต้องการ", r"would like to", r"\bbacklog\b", r"capture.*idea",
      ],
      "spec": [
          r"\bspec\b", r"design.*doc", r"write.*spec", r"spec.*feature",
          r"เขียน.*spec", r"ออกแบบ", r"design.*feature",
      ],
      "plan": [
          r"\bplan\b", r"วางแผน", r"อยากวางแผน", r"เลือก.*backlog",
          r"หยิบ.*backlog", r"plan.*feature", r"ready.*to.*plan",
          r"zie.?plan",
      ],
      "implement": [
          r"implement", r"ทำ.*ต่อ", r"continue", r"resume",
          r"สร้าง.*feature", r"next task", r"task.*ต่อ",
          r"code.*this", r"let.*s.*build", r"start.*coding",
      ],
      "fix": [
          r"\bbug\b", r"พัง", r"\berror\b", r"\bfix\b",
          r"ไม่ทำงาน", r"\bcrash\b", r"exception", r"traceback",
          r"ล้มเหลว", r"broken", r"doesn.*t work", r"not working",
          r"failed", r"failure",
      ],
      "release": [
          r"\brelease\b", r"\bdeploy\b", r"\bpublish\b",
          r"merge.*main", r"go.*live", r"launch", r"ready.*to.*release",
          r"ปล่อย", r"deploy.*now",
      ],
      "retro": [
          r"\bretro\b", r"retrospective", r"สรุป.*session", r"ทบทวน",
          r"review.*session", r"what.*did.*we", r"what.*we.*learned",
          r"what.*worked",
      ],
      "status": [
          r"\bstatus\b", r"ทำอะไรอยู่", r"where.*am.*i", r"progress",
          r"what.*next", r"ต่อไปทำ", r"ถัดไป", r"สถานะ",
      ],
  }

  COMPILED_PATTERNS = {
      cat: [re.compile(p) for p in pats]
      for cat, pats in PATTERNS.items()
  }

  SUGGESTIONS = {
      "init":      "/zie-init",
      "backlog":   "/zie-backlog",
      "spec":      "/zie-spec",
      "plan":      "/zie-plan",
      "implement": "/zie-implement",
      "fix":       "/zie-fix",
      "release":   "/zie-release",
      "retro":     "/zie-retro",
      "status":    "/zie-status",
  }

  MAX_MESSAGE_LEN = 1000

  # ── Hook execution ───────────────────────────────────────────────────────────

  try:
      event = json.loads(sys.stdin.read())
  except Exception:
      sys.exit(0)

  message = (event.get("prompt") or "").lower().strip()

  if not message or len(message) < 3:
      sys.exit(0)

  if len(message) > MAX_MESSAGE_LEN:
      sys.exit(0)

  if message.startswith("---") or len(message) > 500:
      sys.exit(0)

  cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
  if not (cwd / "zie-framework").exists():
      sys.exit(0)

  if message.startswith("/zie-"):
      sys.exit(0)

  scores = {}
  for category, compiled_pats in COMPILED_PATTERNS.items():
      score = 0
      for compiled_pat in compiled_pats:
          if compiled_pat.search(message):
              score += 1
      if score > 0:
          scores[category] = score

  if not scores:
      sys.exit(0)

  best = max(scores, key=scores.get)
  best_score = scores[best]

  if best_score >= 1:
      cmd = SUGGESTIONS[best]
      if best == "init" and (cwd / "zie-framework" / ".config").exists():
          sys.exit(0)
      print(json.dumps({"additionalContext": f"[zie-framework] Detected: {best} intent → {cmd}"}))
  ```

  Note: `MAX_MESSAGE_LEN` is placed with the other module-level constants. If `audit-intent-detect-redos` has already been applied, the constant and guard are already present — this plan only moves `PATTERNS`/`COMPILED_PATTERNS` above the `try` block.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify `PATTERNS` line number is < first `try:` line number using the AST test.
  Confirm all `TestIntentDetectHappyPath`, `TestIntentDetectGuardrails`, `TestIntentDetectSkipGuards` tests still pass.
  Run: `make test-unit` — still PASS

---
*Commit: `git add hooks/intent-detect.py tests/unit/test_hooks_intent_detect.py && git commit -m "fix: hoist PATTERNS and COMPILED_PATTERNS to module level in intent-detect"`*
