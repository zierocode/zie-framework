---
approved: true
approved_at: 2026-04-04
backlog: backlog/sec-shell-injection-stop-guard-slug.md
---

# sec-shell-injection-stop-guard-slug — Implementation Plan

**Goal:** Replace the `shell=True` piped subprocess in `stop-guard.py`'s Nudge 1 with two sequential Python-native calls — `git log` via `shell=False` + in-Python line filtering — eliminating the shell injection surface.
**Architecture:** `_run_nudges()` currently pipes `git log | grep` through a shell, interpolating `slug` directly into the command string. The fix splits this into: (1) a safe `subprocess.run(["git", "log", ...], shell=False)` capturing stdout, then (2) Python `re` scanning of that stdout — no shell involved at any point.
**Tech Stack:** Python 3, `subprocess`, `re`, `pytest`

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/stop-guard.py` | Replace shell=True pipe with shell=False + Python re scan; hoist import re; remove nosec annotation |
| Modify | `tests/unit/test_stop_guard.py` | Add TestNudge1ShellInjection class with metacharacter + empty slug tests |

## Task Sizing

2 tasks — S plan (single session).

---

## Task 1: Replace shell=True with shell=False + Python filtering in Nudge 1

**Acceptance Criteria:**
- `stop-guard.py` contains no `shell=True` in the Nudge 1 block
- `stop-guard.py` contains no `# nosec B602` annotation
- `import re as _re` appears once, hoisted to the top of the `try:` block (not inside the `for slug` loop)
- `git log` is called with a list arg (`shell=False`) capturing stdout
- `result.stdout` is scanned with `re` in Python — no `grep` subprocess
- Slug safety: `re.escape(slug)` used when building the pattern
- `result.returncode != 0` triggers `continue` (not nudge emission)
- Behaviorally identical to current Nudge 1 for non-malicious slugs

**Files:**
- Modify: `hooks/stop-guard.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add `TestNudge1ShellInjection` class to `tests/unit/test_stop_guard.py`:

  ```python
  class TestNudge1SourceInvariants:
      """Source-level checks that verify the shell injection fix is in place."""

      def test_no_shell_true_in_nudge1(self):
          """Nudge 1 block must not use shell=True."""
          source = Path(HOOK).read_text()
          # The git log call must not be a shell=True invocation
          assert "shell=True" not in source, "shell=True must be removed from stop-guard.py"

      def test_no_nosec_b602_annotation(self):
          """nosec B602 annotation must be removed (no longer needed)."""
          source = Path(HOOK).read_text()
          assert "nosec B602" not in source, "# nosec B602 annotation must be removed"

      def test_re_escape_used_in_nudge1(self):
          """re.escape must be used when building the slug pattern."""
          source = Path(HOOK).read_text()
          assert "re.escape" in source or "re.escape" in source, (
              "re.escape(slug) must be used to build the search pattern"
          )

      def test_git_log_uses_list_form(self):
          """git log must be called with a list (not a string) to prevent shell injection."""
          source = Path(HOOK).read_text()
          assert '"git", "log"' in source or "'git', 'log'" in source, (
              "git log must be called with shell=False list form"
          )
  ```

  Run: `make test-unit` — must FAIL (current code has `shell=True` and `nosec B602`)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/stop-guard.py`, replace lines 60–85 (the `for slug in now_items_raw:` block) with:

  ```python
  import re as _re
  for slug in now_items_raw:
      try:
          result = subprocess.run(
              [
                  "git", "log", "--all", "-p", "--",
                  "zie-framework/ROADMAP.md",
              ],
              cwd=str(cwd),
              capture_output=True,
              text=True,
              timeout=subprocess_timeout,
              shell=False,
          )
          if result.returncode != 0:
              continue
          # Scan lines in Python — no shell, no injection surface
          pattern = re.compile(
              r'^\+- \[ \] ' + _re.escape(slug),
          )
          lines = result.stdout.splitlines()
          date_match = None
          for i, line in enumerate(lines):
              if pattern.match(line):
                  # Scan backward up to 5 lines for a Date: header
                  for j in range(max(0, i - 5), i):
                      dm = _re.search(r'^Date:\s+(\d{4}-\d{2}-\d{2})', lines[j])
                      if dm:
                          date_match = dm
                          break
                  if date_match:
                      break
          if date_match:
              commit_date = _dt.date.fromisoformat(date_match.group(1))
              days = (_dt.date.today() - commit_date).days
              if days > 2:
                  print(
                      f"[zie-framework] nudge: RED phase '{slug}' has been active for "
                      f"{days} days — consider splitting or committing partial progress"
                  )
      except Exception:
          pass
  ```

  Also remove the stale `import re as _re` that was inside the loop body (line 62 of original).

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Confirm `import re as _re` appears exactly once in the Nudge 1 try block (hoisted above the for loop)
  - Confirm no `shell=True` remains anywhere in the file for git commands
  - Confirm `# nosec B602` comment is gone
  - Run: `make test-unit` — still PASS

---

## Task 2: Add metacharacter + edge-case tests for Nudge 1

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- A slug containing shell metacharacters (`$(cmd)`, backtick, `|`, `;`, `&`) does not cause the hook to crash or produce unexpected output
- An empty-string slug causes the hook to exit 0 silently (no nudge, no crash)
- Both tests pass against the fixed implementation
- Tests use a real git repo fixture so Nudge 1 code path is actually exercised

**Files:**
- Modify: `tests/unit/test_stop_guard.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_stop_guard.py`:

  ```python
  class TestNudge1ShellInjection:
      """Verify Nudge 1 is safe when slug contains shell metacharacters."""

      def _init_repo_with_roadmap(self, tmp_path, slug):
          """Create a git repo with a ROADMAP.md containing the given slug in the Now lane."""
          git_env = {
              **os.environ,
              "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.com",
              "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.com",
          }
          subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
          # Create zie-framework/ROADMAP.md with the slug in the Now lane
          roadmap_dir = tmp_path / "zie-framework"
          roadmap_dir.mkdir()
          roadmap = roadmap_dir / "ROADMAP.md"
          roadmap.write_text(
              f"## Now\n- [ ] [{slug}](backlog/{slug}.md)\n\n## Next\n"
          )
          subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), check=True, capture_output=True)
          subprocess.run(
              ["git", "commit", "-m", "init"],
              cwd=str(tmp_path), check=True, capture_output=True, env=git_env,
          )
          return roadmap

      def test_slug_with_pipe_does_not_crash(self, tmp_path):
          """Slug containing | must not crash the hook."""
          slug = "feat|rm -rf /"
          self._init_repo_with_roadmap(tmp_path, slug)
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "Traceback" not in r.stderr

      def test_slug_with_subshell_does_not_crash(self, tmp_path):
          """Slug containing $(...) must not crash the hook."""
          slug = "feat$(echo pwned)"
          self._init_repo_with_roadmap(tmp_path, slug)
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "Traceback" not in r.stderr

      def test_slug_with_semicolon_does_not_crash(self, tmp_path):
          """Slug containing ; must not crash the hook."""
          slug = "feat;touch /tmp/injected"
          self._init_repo_with_roadmap(tmp_path, slug)
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "Traceback" not in r.stderr

      def test_empty_slug_does_not_crash(self, tmp_path):
          """Empty slug must not crash or emit a nudge."""
          subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
          roadmap_dir = tmp_path / "zie-framework"
          roadmap_dir.mkdir()
          (roadmap_dir / "ROADMAP.md").write_text("## Now\n- [ ] \n\n## Next\n")
          git_env = {
              **os.environ,
              "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.com",
              "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.com",
          }
          subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), check=True, capture_output=True)
          subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path),
                         check=True, capture_output=True, env=git_env)
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "Traceback" not in r.stderr
  ```

  Run: `make test-unit` — tests for metacharacter slugs will FAIL against old `shell=True` code (or PASS against fixed code — if Task 1 is already done, confirm these pass cleanly)

- [ ] **Step 2: Implement (GREEN)**
  No code changes needed in this task — tests pass once Task 1 fix is in place. If Task 1 is complete, run:

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Review test fixture for duplication — if `_init_repo_with_roadmap` is reused elsewhere, consider a shared conftest helper (defer unless obvious)
  - Run: `make test-unit` — still PASS
