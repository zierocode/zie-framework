---
approved: true
approved_at: 2026-03-29
spec: specs/2026-03-29-user-onboarding-sdlc-design.md
backlog: backlog/user-onboarding-sdlc.md
---

# User Onboarding + Knowledge Drift Detection — Implementation Plan

**Goal:** Add a 3-line SDLC pipeline summary to `/zie-init` Step 13 output and drift detection to `session-resume.py` via a new `--check` mode in `knowledge-hash.py`.
**Architecture:** Two minimally invasive additions to existing hooks/commands. `knowledge-hash.py` gains a `--check` flag that compares the stored hash in `.config` to the current computed hash and exits non-zero (signalled via stdout message) only when drift is detected. `session-resume.py` calls the script as a subprocess guarded by a try/except that can never block Claude. `zie-init.md` gets a fixed 3-line block appended after the Step 13 summary.
**Tech Stack:** Python 3.x, argparse, hashlib, subprocess, pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/knowledge-hash.py` | Add `--check` mode: compare stored vs computed hash, print drift warning if mismatch |
| Modify | `hooks/session-resume.py` | After active-feature print, call `knowledge-hash.py --check` in a guarded subprocess |
| Modify | `commands/zie-init.md` | Append pipeline summary block after Step 13 summary output |
| Create | `tests/unit/test_knowledge_hash_check.py` | Unit tests for `--check` mode of `knowledge-hash.py` |
| Modify | `tests/unit/test_hooks_session_resume.py` | Add tests: drift warning printed, silent on match, exit 0 on crash |
| Create | `tests/unit/test_commands_zie_init.py` | Verify pipeline summary string present in Step 13 output spec |

---

## Task 1: Add `--check` mode to `knowledge-hash.py`

**Acceptance Criteria:**
- `python3 hooks/knowledge-hash.py --check` prints `[zie-framework] Knowledge drift detected since last session — run /zie-resync to update project context` to stdout when stored hash differs from computed hash
- `--check` exits silently (no output, exit 0) when hashes match
- `--check` exits silently when `knowledge_hash` in `.config` is empty string or key is absent
- `--check` exits silently when `zie-framework/.config` does not exist
- `--check` and `--now` (default) are mutually exclusive paths; default (no flag) still prints computed hash

**Files:**
- Modify: `hooks/knowledge-hash.py`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_knowledge_hash_check.py`:

  ```python
  """Tests for knowledge-hash.py --check mode."""
  import json
  import os
  import subprocess
  import sys
  from pathlib import Path

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  SCRIPT = os.path.join(REPO_ROOT, "hooks", "knowledge-hash.py")


  def run_check(root_dir):
      return subprocess.run(
          [sys.executable, SCRIPT, "--check", "--root", str(root_dir)],
          capture_output=True, text=True,
      )


  def write_config(root_dir, knowledge_hash=""):
      zf = Path(root_dir) / "zie-framework"
      zf.mkdir(parents=True, exist_ok=True)
      (zf / ".config").write_text(json.dumps({"knowledge_hash": knowledge_hash}))


  class TestCheckModeHashMismatch:
      def test_prints_drift_warning_on_mismatch(self, tmp_path):
          """Stored hash differs from computed → drift warning printed."""
          write_config(tmp_path, knowledge_hash="deadbeef0000")
          r = run_check(tmp_path)
          assert r.returncode == 0
          assert "[zie-framework] Knowledge drift detected" in r.stdout
          assert "/zie-resync" in r.stdout

      def test_drift_message_exact_text(self, tmp_path):
          write_config(tmp_path, knowledge_hash="aaaaaaaaaaaa")
          r = run_check(tmp_path)
          assert (
              "[zie-framework] Knowledge drift detected since last session"
              " — run /zie-resync to update project context"
          ) in r.stdout


  class TestCheckModeSilentCases:
      def test_silent_when_hashes_match(self, tmp_path):
          """When stored hash equals computed hash → no output."""
          # Compute current hash first
          compute = subprocess.run(
              [sys.executable, SCRIPT, "--root", str(tmp_path)],
              capture_output=True, text=True,
          )
          current_hash = compute.stdout.strip()
          write_config(tmp_path, knowledge_hash=current_hash)
          r = run_check(tmp_path)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_silent_when_stored_hash_empty(self, tmp_path):
          """Empty knowledge_hash → skip check silently."""
          write_config(tmp_path, knowledge_hash="")
          r = run_check(tmp_path)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_silent_when_key_absent(self, tmp_path):
          """Missing knowledge_hash key → skip check silently."""
          zf = tmp_path / "zie-framework"
          zf.mkdir(parents=True)
          (zf / ".config").write_text(json.dumps({"project_type": "python-api"}))
          r = run_check(tmp_path)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_silent_when_config_missing(self, tmp_path):
          """No .config file → skip check silently."""
          # No zie-framework dir at all
          r = run_check(tmp_path)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_silent_when_config_corrupt(self, tmp_path):
          """Corrupt .config → skip check silently, never crash."""
          zf = tmp_path / "zie-framework"
          zf.mkdir(parents=True)
          (zf / ".config").write_text("not valid json!!!")
          r = run_check(tmp_path)
          assert r.returncode == 0


  class TestDefaultModeUnchanged:
      def test_default_still_prints_hash(self, tmp_path):
          """Default mode (no --check) still prints hex hash to stdout."""
          r = subprocess.run(
              [sys.executable, SCRIPT, "--root", str(tmp_path)],
              capture_output=True, text=True,
          )
          assert r.returncode == 0
          assert len(r.stdout.strip()) == 64  # SHA-256 hex
  ```

  Run: `make test-unit` — must FAIL (no `--check` mode yet)

- [ ] **Step 2: Implement (GREEN)**

  Replace `hooks/knowledge-hash.py` content — keep existing hash logic, add `--check` branch:

  ```python
  #!/usr/bin/env python3
  """Compute knowledge_hash for a zie-framework project.

  Prints the SHA-256 hex digest to stdout.
  Usage: python3 hooks/knowledge-hash.py [--root <path>] [--check]
    --check  Compare stored hash in zie-framework/.config to current hash.
             Prints drift warning if mismatch, silent otherwise.
  """
  import argparse
  import hashlib
  import json
  import sys
  from pathlib import Path

  EXCLUDE = {
      'node_modules', '.git', 'build', 'dist', '.next',
      '__pycache__', 'coverage', 'zie-framework'
  }
  EXCLUDE_PATHS = {'zie-framework/plans/archive'}
  CONFIG_FILES = [
      'package.json', 'requirements.txt', 'pyproject.toml',
      'Cargo.toml', 'go.mod'
  ]

  parser = argparse.ArgumentParser()
  parser.add_argument('--root', default='.')
  parser.add_argument('--now', action='store_true',
                      help='Print current hash to stdout (default; accepted for compatibility)')
  parser.add_argument('--check', action='store_true',
                      help='Compare stored vs current hash; print drift warning if mismatch')
  args = parser.parse_args()

  root = Path(args.root)


  def compute_hash(root: Path) -> str:
      dirs = sorted(
          str(p.relative_to(root))
          for p in root.rglob('*')
          if p.is_dir()
          and not any(ex in p.parts for ex in EXCLUDE)
          and str(p.relative_to(root)) not in EXCLUDE_PATHS
      )
      counts = sorted(
          f'{d}:{len(list((root / d).iterdir()))}'
          for d in dirs
      )
      configs = ''
      for cf in CONFIG_FILES:
          p = root / cf
          if p.exists():
              configs += p.read_text()
      s = '\n'.join(dirs) + '\n---\n'
      s += '\n'.join(counts) + '\n---\n'
      s += configs
      return hashlib.sha256(s.encode()).hexdigest()


  if args.check:
      try:
          config_path = root / 'zie-framework' / '.config'
          if not config_path.exists():
              sys.exit(0)
          try:
              config = json.loads(config_path.read_text())
          except Exception:
              sys.exit(0)
          stored = config.get('knowledge_hash', '')
          if not stored:
              sys.exit(0)
          current = compute_hash(root)
          if current != stored:
              print(
                  '[zie-framework] Knowledge drift detected since last session'
                  ' — run /zie-resync to update project context'
              )
      except Exception:
          sys.exit(0)
  else:
      print(compute_hash(root))
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - `compute_hash` is now a named function — verify it's clean and DRY with no duplication
  - Confirm `--now` flag still accepted without error (backward compat)
  - Run: `make test-unit` — still PASS

---

## Task 2: Add drift detection call to `session-resume.py`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- When `knowledge-hash.py --check` prints a drift warning, `session-resume.py` prints it to stdout after the active-feature block
- When no drift, session-resume output is unchanged (still exactly 4 lines per existing test)
- If `knowledge-hash.py` crashes or returns non-zero, session-resume exits 0 and logs error to stderr — Claude is never blocked
- Drift detection is skipped if `zie-framework/` does not exist (existing early-exit guard applies)

**Files:**
- Modify: `hooks/session-resume.py`
- Modify: `tests/unit/test_hooks_session_resume.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append to `tests/unit/test_hooks_session_resume.py`:

  ```python
  # ---------------------------------------------------------------------------
  # Drift detection tests (Task 2)
  # ---------------------------------------------------------------------------

  class TestSessionResumeDriftDetection:
      def test_prints_drift_warning_when_hash_mismatch(self, tmp_path):
          """session-resume must print drift warning when knowledge-hash.py --check outputs one."""
          cwd = make_cwd(tmp_path, config={"knowledge_hash": "deadbeef0000"},
                         roadmap=SAMPLE_ROADMAP)
          r = run_hook(tmp_cwd=cwd)
          assert r.returncode == 0
          assert "Knowledge drift detected" in r.stdout

      def test_silent_when_hash_matches(self, tmp_path):
          """No drift warning printed when hashes match."""
          import subprocess as sp, sys as _sys
          REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
          kh = os.path.join(REPO, "hooks", "knowledge-hash.py")
          result = sp.run([_sys.executable, kh, "--root", str(tmp_path)],
                          capture_output=True, text=True)
          current_hash = result.stdout.strip()
          cwd = make_cwd(tmp_path, config={"knowledge_hash": current_hash},
                         roadmap=SAMPLE_ROADMAP)
          r = run_hook(tmp_cwd=cwd)
          assert r.returncode == 0
          assert "drift" not in r.stdout.lower()

      def test_exits_zero_when_knowledge_hash_crashes(self, tmp_path, monkeypatch):
          """If knowledge-hash.py is missing/crashes, hook exits 0 and logs to stderr."""
          import shutil
          REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
          # Point to a non-existent script via env
          cwd = make_cwd(tmp_path, config={"knowledge_hash": "abc"},
                         roadmap=SAMPLE_ROADMAP)
          env = {**os.environ, "CLAUDE_CWD": str(cwd),
                 "ZIE_KNOWLEDGE_HASH_SCRIPT": "/nonexistent/knowledge-hash.py"}
          result = subprocess.run([sys.executable, HOOK],
                                  input=json.dumps({}),
                                  capture_output=True, text=True, env=env)
          assert result.returncode == 0

      def test_output_line_count_unchanged_without_drift(self, tmp_path):
          """Without drift, output remains exactly 4 lines."""
          import subprocess as sp, sys as _sys
          REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
          kh = os.path.join(REPO, "hooks", "knowledge-hash.py")
          result = sp.run([_sys.executable, kh, "--root", str(tmp_path)],
                          capture_output=True, text=True)
          current_hash = result.stdout.strip()
          cwd = make_cwd(tmp_path, config={"knowledge_hash": current_hash},
                         roadmap=SAMPLE_ROADMAP)
          r = run_hook(tmp_cwd=cwd)
          assert len(r.stdout.strip().splitlines()) == 4
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  Append drift detection block to `hooks/session-resume.py` after `print("\n".join(lines))`:

  ```python
  # Drift detection — call knowledge-hash.py --check
  try:
      import subprocess as _sp
      _kh_script = os.environ.get(
          "ZIE_KNOWLEDGE_HASH_SCRIPT",
          os.path.join(os.path.dirname(__file__), "knowledge-hash.py"),
      )
      _result = _sp.run(
          [sys.executable, _kh_script, "--check", "--root", str(cwd)],
          capture_output=True, text=True, timeout=10,
      )
      if _result.stdout.strip():
          print(_result.stdout.strip())
  except Exception as e:
      print(f"[zie-framework] session-resume: drift check failed: {e}", file=sys.stderr)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - Confirm `ZIE_KNOWLEDGE_HASH_SCRIPT` env var fallback path is correct (`os.path.dirname(__file__)` resolves to `hooks/`)
  - Confirm existing `test_output_is_4_lines` still passes (it uses a project without a stored hash, so drift check is silent)
  - Run: `make test-unit` — still PASS

---

## Task 3: Add pipeline summary to `commands/zie-init.md` Step 13

<!-- depends_on: none -->

**Acceptance Criteria:**
- Step 13 of `zie-init.md` outputs the 3-line SDLC pipeline block immediately after the summary table
- The pipeline block reads exactly:
  ```
  SDLC pipeline:
    /zie-backlog → /zie-spec → /zie-plan → /zie-implement → /zie-release → /zie-retro
  Each stage enforces quality gates. Run /zie-status to see where you are.
  First feature: /zie-backlog "your idea"
  ```
- If migration ran in step 2.h, a migration summary line is appended: `Migration complete: <N> files moved to zie-framework/specs|plans|decisions/`
- Change is idempotent (safe to re-run; summary is always printed as part of Step 13 output)

**Files:**
- Modify: `commands/zie-init.md`
- Create: `tests/unit/test_commands_zie_init.py`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_commands_zie_init.py`:

  ```python
  """Tests for commands/zie-init.md content spec compliance."""
  import os

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  ZIE_INIT_MD = os.path.join(REPO_ROOT, "commands", "zie-init.md")


  def read_init():
      with open(ZIE_INIT_MD) as f:
          return f.read()


  class TestZieInitPipelineSummary:
      def test_pipeline_summary_present(self):
          """Step 13 must contain the SDLC pipeline block."""
          content = read_init()
          assert "SDLC pipeline:" in content

      def test_pipeline_all_stages_listed(self):
          """Pipeline block must list all 6 SDLC stages in order."""
          content = read_init()
          stages = [
              "/zie-backlog", "/zie-spec", "/zie-plan",
              "/zie-implement", "/zie-release", "/zie-retro",
          ]
          for stage in stages:
              assert stage in content, f"Missing stage: {stage}"

      def test_pipeline_quality_gates_line(self):
          content = read_init()
          assert "Each stage enforces quality gates" in content

      def test_pipeline_first_feature_hint(self):
          content = read_init()
          assert 'First feature: /zie-backlog' in content

      def test_pipeline_summary_after_step_13(self):
          """Pipeline block must appear within or after the Step 13 section."""
          content = read_init()
          step13_idx = content.find("13. **Print summary**")
          pipeline_idx = content.find("SDLC pipeline:")
          assert step13_idx != -1, "Step 13 not found in zie-init.md"
          assert pipeline_idx != -1, "SDLC pipeline block not found"
          assert pipeline_idx > step13_idx, (
              "Pipeline summary must appear after Step 13 header"
          )

      def test_migration_complete_line_documented(self):
          """Migration complete line must be documented in Step 13."""
          content = read_init()
          assert "Migration complete:" in content
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-init.md`, locate Step 13 and extend the printed output block. Replace the existing Step 13 block:

  Current Step 13 ends with:
  ```
     Next: Run /zie-status to see current state.
           Run /zie-backlog to start your first feature.
     ```
  ```

  Extend it to:

  ```markdown
  13. **Print summary**:

     ```text
     zie-framework initialized in <project>/

     Project type : <type>
     Test runner  : <runner>
     Frontend     : <yes|no>
     Playwright   : <enabled|disabled>
     Brain        : <enabled|disabled>

     Created:
       zie-framework/  (specs, plans, decisions, ROADMAP.md)
       CLAUDE.md       (<created|skipped — already exists>)
       Makefile        (<created|updated>)
       VERSION         (<created|kept>)

     Next: Run /zie-status to see current state.
           Run /zie-backlog to start your first feature.

     SDLC pipeline:
       /zie-backlog → /zie-spec → /zie-plan → /zie-implement → /zie-release → /zie-retro
     Each stage enforces quality gates. Run /zie-status to see where you are.
     First feature: /zie-backlog "your idea"
     ```

     If migration ran in step 2.h, append:
     ```text
     Migration complete: <N> files moved to zie-framework/specs|plans|decisions/
     ```
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - Read through zie-init.md Step 13 to confirm the text block is clean, properly indented, and consistent with surrounding step formatting
  - Run: `make test-unit` — still PASS

---

## Task 4: Full integration smoke test

<!-- depends_on: Task 1, Task 2, Task 3 -->

**Acceptance Criteria:**
- Full test suite passes with no regressions
- `knowledge-hash.py --check` with a stale hash produces the drift warning in session-resume stdout
- `knowledge-hash.py --check` with a matching hash produces no drift output
- All existing session-resume tests still pass (no line-count regressions)

**Files:**
- No new files — integration verification only

- [ ] **Step 1: Run full suite**

  ```bash
  make test-unit
  ```

  Expected: all tests pass, no failures.

- [ ] **Step 2: Manual smoke test — drift path**

  ```bash
  # In a temp dir with a zie-framework setup
  python3 hooks/knowledge-hash.py --check --root /tmp/smoke-test-project
  ```

  With a stale stored hash in `/tmp/smoke-test-project/zie-framework/.config`, confirm output is:
  ```
  [zie-framework] Knowledge drift detected since last session — run /zie-resync to update project context
  ```

- [ ] **Step 3: Manual smoke test — silent path**

  Compute current hash and store it, then re-run `--check`. Confirm no output.

- [ ] **Step 4: Confirm no bare `except: pass` in session-resume.py**

  Existing test `test_no_bare_pass_in_session_resume_inner_ops` must still pass — the new drift block uses `except Exception as e: print(...)` pattern.
