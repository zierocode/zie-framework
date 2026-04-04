---
approved: true
approved_at: 2026-04-04
backlog: backlog/remove-zie-prefix-from-command-names.md
---

# Remove zie- prefix from command names — Implementation Plan

**Goal:** Rename all 12 command files from `commands/zie-*.md` → `commands/*.md` and update every internal reference so the full invocation surface becomes `zie-framework:fix` instead of `zie-framework:zie-fix`.

**Architecture:** Pure rename-and-sweep refactor — no behaviour change. Command files are renamed with `git mv`. All internal references (hooks, skills, tests, docs, knowledge docs) are updated in place. The plugin namespace `zie-framework` is untouched; only the command name segment after the colon changes.

**Tech Stack:** Bash (git mv), Python (hook edits), Markdown (command/skill/doc edits), pytest (test suite verification).

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Rename | `commands/zie-audit.md` → `commands/audit.md` | Remove prefix |
| Rename | `commands/zie-backlog.md` → `commands/backlog.md` | Remove prefix |
| Rename | `commands/zie-fix.md` → `commands/fix.md` | Remove prefix |
| Rename | `commands/zie-implement.md` → `commands/implement.md` | Remove prefix |
| Rename | `commands/zie-init.md` → `commands/init.md` | Remove prefix |
| Rename | `commands/zie-plan.md` → `commands/plan.md` | Remove prefix |
| Rename | `commands/zie-release.md` → `commands/release.md` | Remove prefix |
| Rename | `commands/zie-resync.md` → `commands/resync.md` | Remove prefix |
| Rename | `commands/zie-retro.md` → `commands/retro.md` | Remove prefix |
| Rename | `commands/zie-spec.md` → `commands/spec.md` | Remove prefix |
| Rename | `commands/zie-sprint.md` → `commands/sprint.md` | Remove prefix |
| Rename | `commands/zie-status.md` → `commands/status.md` | Remove prefix |
| Modify | `hooks/intent-sdlc.py` | Update SUGGESTIONS, STAGE_COMMANDS, gate message strings, startswith guard |
| Modify | `hooks/session-resume.py` | Update `/zie-backlog`, `/zie-status` strings |
| Modify | `hooks/config-drift.py` | Update `/zie-resync` string |
| Modify | `hooks/knowledge-hash.py` | Update `/zie-resync` string |
| Modify | `hooks/adr_summary.py` | Update `/zie-retro` comment |
| Modify | `skills/*/SKILL.md` (13 files) | Update all `/zie-*` command references |
| Modify | `commands/*.md` (all 12, after rename) | Update cross-references to sibling commands |
| Modify | `tests/unit/test_sdlc_pipeline.py` | Update `cmd()` helper + file-path strings |
| Modify | `tests/unit/test_sdlc_gates.py` | Update file-path strings + command assertion |
| Modify | `tests/unit/test_hooks_intent_sdlc.py` | Update `/zie-*` assertion strings |
| Modify | `tests/unit/test_*.py` (remaining 36 files) | Update `commands/zie-*.md` path strings |
| Modify | `CLAUDE.md` | Update SDLC Commands table |
| Modify | `README.md` | Update Commands table + Pipeline diagram |
| Modify | `zie-framework/PROJECT.md` | Update command references |
| Modify | `zie-framework/ROADMAP.md` | Update command references in header comment |
| Modify | `zie-framework/project/components.md` | Update command references |

---

## Task 1: Rename command files with git mv

**Acceptance Criteria:**
- All 12 `commands/zie-*.md` files renamed to `commands/*.md` via `git mv`
- `commands/` directory contains no `zie-*.md` files
- Git tracks renames (not deletes+creates)

**Files:**
- Rename: all 12 `commands/zie-*.md` → `commands/*.md`

- [ ] **Step 1: Write failing test (RED)**
  ```python
  # Add to tests/unit/test_sdlc_pipeline.py temporarily or run manually:
  import os
  assert not os.path.exists("commands/zie-backlog.md"), "old file must not exist"
  assert os.path.exists("commands/backlog.md"), "new file must exist"
  ```
  Run: `make test-unit` — will FAIL (files not renamed yet)

- [ ] **Step 2: Execute renames (GREEN)**
  ```bash
  cd /Users/zie/Code/zie-framework
  git mv commands/zie-audit.md    commands/audit.md
  git mv commands/zie-backlog.md  commands/backlog.md
  git mv commands/zie-fix.md      commands/fix.md
  git mv commands/zie-implement.md commands/implement.md
  git mv commands/zie-init.md     commands/init.md
  git mv commands/zie-plan.md     commands/plan.md
  git mv commands/zie-release.md  commands/release.md
  git mv commands/zie-resync.md   commands/resync.md
  git mv commands/zie-retro.md    commands/retro.md
  git mv commands/zie-spec.md     commands/spec.md
  git mv commands/zie-sprint.md   commands/sprint.md
  git mv commands/zie-status.md   commands/status.md
  ```
  Verify: `ls commands/` — must show plain verb names only, no `zie-*.md`

- [ ] **Step 3: Refactor**
  None needed for this rename step.

---

## Task 2: Update test_sdlc_pipeline.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `cmd()` helper uses plain names (no `zie-` prefix)
- All `os.path.exists(cmd("..."))` assertions reference the new file paths
- `test_zie_backlog_exists`, etc. still pass (checking `commands/backlog.md`)

**Files:**
- Modify: `tests/unit/test_sdlc_pipeline.py`

- [ ] **Step 1: Write failing test (RED)**
  Run: `make test-unit` — `TestNewCommandsExist` tests FAIL because `cmd()` still appends `zie-` prefix.

- [ ] **Step 2: Implement (GREEN)**
  Change the `cmd()` helper and all `f"commands/zie-{name}.md"` strings:
  ```python
  # Before:
  def cmd(name):
      return os.path.join(REPO_ROOT, "commands", f"zie-{name}.md")

  # After:
  def cmd(name):
      return os.path.join(REPO_ROOT, "commands", f"{name}.md")
  ```
  Also update the assertion messages — e.g.:
  `"commands/zie-backlog.md must exist"` → `"commands/backlog.md must exist"`
  And `"commands/zie-idea.md must be removed"` error messages.
  Also update `read("commands/zie-plan.md")` → `read("commands/plan.md")` etc.
  Also update `TestIntentDetectUpdated.test_has_backlog_suggestion`:
  ```python
  assert '"/backlog"' in self._hook() or '"/zie-backlog"' in self._hook()
  ```
  (will be updated fully in Task 4 once hooks are patched)
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Clean up any stale comments referencing old names.
  Run: `make test-unit` — still PASS

---

## Task 3: Update remaining test files (batch)

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- All 36 remaining test files that reference `commands/zie-*.md` updated to `commands/*.md`
- No test references `commands/zie-*.md` paths after this task
- `make test-unit` passes

**Files:**
- Modify: `tests/unit/test_sdlc_gates.py`, `tests/unit/test_mcp_bundle.py`, `tests/unit/test_model_effort_frontmatter.py`, `tests/unit/test_workflow_lean.py`, `tests/unit/test_e2e_optimization.py`, `tests/unit/test_fork_superpowers_skills.py`, `tests/unit/test_zie_init_deep_scan.py`, `tests/unit/test_zie_init_templates.py`, `tests/unit/test_zie_audit.py`, `tests/unit/test_skills_advanced_features.py`, `tests/unit/test_knowledge_arch.py`, `tests/unit/test_dx_polish.py`, `tests/unit/test_model_routing_v2.py`, `tests/unit/test_commands_zie_init.py`, and all other affected unit test files

- [ ] **Step 1: Write failing test (RED)**
  Run: `make test-unit` — tests fail due to missing `commands/zie-*.md` files (renamed in Task 1)

- [ ] **Step 2: Implement (GREEN)**
  Bulk-replace `commands/zie-` with `commands/` in all test files (path references only):
  ```bash
  # Dry-run first:
  grep -rl 'commands/zie-' tests/unit/ --include='*.py'
  # Then apply:
  sed -i '' 's|commands/zie-|commands/|g' tests/unit/*.py
  ```
  Special cases to handle manually:
  - `test_sdlc_gates.py` line 156: `path = os.path.join(REPO_ROOT, "commands", "zie-plan.md")` → `"commands", "plan.md"`
  - `test_sdlc_gates.py` assertion: `"commands/zie-plan.md must exist"` → `"commands/plan.md must exist"`
  - `test_stop_guard.py` line 176: `"commands/zie-feature.md"` — this is a synthetic test path, leave as-is or rename to `"commands/feature.md"` (check test context)
  - `test_test_fast_script.py` line 40: `"commands/zie-implement.md"` → `"commands/implement.md"`
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify no remaining `commands/zie-` path references in tests:
  ```bash
  grep -r 'commands/zie-' tests/ --include='*.py'
  ```
  Must return empty.
  Run: `make test-unit` — still PASS

---

## Task 4: Update hooks/intent-sdlc.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `SUGGESTIONS` dict values use `/plan`, `/fix`, etc. (no `/zie-` prefix)
- `STAGE_COMMANDS` dict values use plain verbs
- Gate message strings use new command names
- `message.startswith("/zie-")` guard updated to handle new format
- Hook output contains `/plan` instead of `/zie-plan` (etc.)

**Files:**
- Modify: `hooks/intent-sdlc.py`

- [ ] **Step 1: Write failing test (RED)**
  `test_hooks_intent_sdlc.py::TestIntentSdlcHappyPath::test_fix_intent_detected` asserts `/zie-fix` in context — after hook update this will change to `/fix`.
  The test will need updating too, but run `make test-unit` first to see current state.

- [ ] **Step 2: Implement (GREEN)**
  Update `hooks/intent-sdlc.py`:

  ```python
  # SUGGESTIONS dict (lines 81–90) — before:
  SUGGESTIONS = {
      "init":      "/zie-init",
      "backlog":   "/zie-backlog",
      "spec":      "/zie-spec",
      "plan":      "/zie-plan",
      "implement": "/zie-implement",
      "fix":       "/zie-fix",
      "release":   "/zie-release",
      "retro":     "/zie-retro",
      "sprint":    "/zie-sprint",
      "status":    "/zie-status",
  }

  # After:
  SUGGESTIONS = {
      "init":      "/init",
      "backlog":   "/backlog",
      "spec":      "/spec",
      "plan":      "/plan",
      "implement": "/implement",
      "fix":       "/fix",
      "release":   "/release",
      "retro":     "/retro",
      "sprint":    "/sprint",
      "status":    "/status",
  }

  # STAGE_COMMANDS dict (lines 104–113) — after:
  STAGE_COMMANDS = {
      "spec":        "/spec",
      "plan":        "/plan",
      "implement":   "/implement",
      "fix":         "/fix",
      "release":     "/release",
      "retro":       "/retro",
      "in-progress": "/status",
      "idle":        "/status",
  }

  # Gate message strings — update all /zie-* references:
  # line 168: "You must run /zie-spec" → "You must run /spec"
  # line 184: "/zie-backlog → /zie-spec → /zie-plan" → "/backlog → /spec → /plan"
  # line 185: "/zie-implement" → "/implement"
  # line 211: "/zie-spec {slug}" → "/spec {slug}"
  # line 213: "/zie-plan {slug}" → "/plan {slug}"
  # line 214: "/zie-implement" → "/implement"

  # Early-exit guard (line 250) — update to use known command names:
  # Before: if message.startswith("/zie-"):
  # After: keep broad — any message starting with "/" is a direct command invocation
  if message.startswith("/") and len(message.split()[0]) < 20:
      sys.exit(0)
  ```

  Then update `test_hooks_intent_sdlc.py` assertions:
  ```python
  # TestIntentSdlcHappyPath: replace "/zie-fix" → "/fix", "/zie-implement" → "/implement", "/zie-release" → "/release"
  # TestPositionalGuidance: replace "zie-spec" → "spec", "zie-plan" → "plan", "zie-implement" → "implement"
  # TestIntentSdlcEarlyExit: update test prompt "/zie-implement now" → "/implement now"
  # TestIntentDetectPlan in test_sdlc_gates.py: update "/zie-plan" assertion → "/plan"
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify no `/zie-` strings remain in `hooks/intent-sdlc.py`:
  ```bash
  grep '/zie-' hooks/intent-sdlc.py
  ```
  Must return empty.
  Run: `make test-unit` — still PASS

---

## Task 5: Update remaining hooks + adr_summary.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `hooks/session-resume.py`: `/zie-backlog` → `/backlog`, `/zie-status` → `/status`
- `hooks/config-drift.py`: `/zie-resync` → `/resync`
- `hooks/knowledge-hash.py`: `/zie-resync` → `/resync`
- `hooks/adr_summary.py`: `Used by /zie-retro` comment → `Used by /retro`
- All hook tests pass

**Files:**
- Modify: `hooks/session-resume.py`, `hooks/config-drift.py`, `hooks/knowledge-hash.py`, `hooks/adr_summary.py`

- [ ] **Step 1: Write failing test (RED)**
  Run: `make test-unit` — `test_hooks_session_resume.py` may assert old command strings; verify.

- [ ] **Step 2: Implement (GREEN)**
  ```bash
  sed -i '' 's|/zie-backlog|/backlog|g; s|/zie-status|/status|g' hooks/session-resume.py
  sed -i '' 's|/zie-resync|/resync|g' hooks/config-drift.py
  sed -i '' 's|/zie-resync|/resync|g' hooks/knowledge-hash.py
  sed -i '' 's|/zie-retro|/retro|g' hooks/adr_summary.py
  ```
  Update `test_hooks_session_resume.py` if it asserts the old `/zie-*` strings.
  Update `test_hooks_config_drift.py` if it asserts `/zie-resync`.
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify no `/zie-` strings in any hook:
  ```bash
  grep -r '/zie-' hooks/
  ```
  Must return empty.
  Run: `make test-unit` — still PASS

---

## Task 6: Update skills and command cross-references

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- All `skills/*/SKILL.md` files updated: `/zie-*` → `/*` command references
- All `commands/*.md` (renamed files) cross-references updated: `→ /zie-plan` → `→ /plan` etc.
- `skills/zie-audit/SKILL.md` invocation line updated to `/audit`

**Files:**
- Modify: `skills/spec-design/SKILL.md`, `skills/spec-reviewer/SKILL.md`, `skills/plan-reviewer/SKILL.md`, `skills/impl-reviewer/SKILL.md`, `skills/verify/SKILL.md`, `skills/tdd-loop/SKILL.md`, `skills/docs-sync-check/SKILL.md`, `skills/zie-audit/SKILL.md`, `skills/test-pyramid/SKILL.md`
- Modify: `commands/backlog.md`, `commands/spec.md`, `commands/plan.md`, `commands/implement.md`, `commands/fix.md`, `commands/release.md`, `commands/retro.md`, `commands/sprint.md`, `commands/status.md`, `commands/init.md`, `commands/audit.md`, `commands/resync.md`

- [ ] **Step 1: Write failing test (RED)**
  Run: `make test-unit` — tests reading command content for `/zie-plan`, `/zie-spec` etc. will still see old references (in command body text). These tests check content, not filenames.

- [ ] **Step 2: Implement (GREEN)**
  ```bash
  # Update all skills:
  sed -i '' 's|/zie-init|/init|g; s|/zie-backlog|/backlog|g; s|/zie-spec|/spec|g; s|/zie-plan|/plan|g; s|/zie-implement|/implement|g; s|/zie-fix|/fix|g; s|/zie-release|/release|g; s|/zie-retro|/retro|g; s|/zie-sprint|/sprint|g; s|/zie-status|/status|g; s|/zie-resync|/resync|g; s|/zie-audit|/audit|g' skills/*/SKILL.md

  # Update all renamed command files:
  sed -i '' 's|/zie-init|/init|g; s|/zie-backlog|/backlog|g; s|/zie-spec|/spec|g; s|/zie-plan|/plan|g; s|/zie-implement|/implement|g; s|/zie-fix|/fix|g; s|/zie-release|/release|g; s|/zie-retro|/retro|g; s|/zie-sprint|/sprint|g; s|/zie-status|/status|g; s|/zie-resync|/resync|g; s|/zie-audit|/audit|g' commands/*.md
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  ```bash
  grep -r '/zie-' skills/ commands/
  ```
  Must return empty.
  Run: `make test-unit` — still PASS

---

## Task 7: Update CLAUDE.md, README.md, and knowledge docs

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `CLAUDE.md` SDLC Commands table shows new names (`/init`, `/backlog`, etc.)
- `README.md` Commands table and Pipeline diagram updated
- `zie-framework/PROJECT.md`, `ROADMAP.md`, `project/components.md` updated
- `test_claude_md_commands.py` and `test_docs_standards.py` pass

**Files:**
- Modify: `CLAUDE.md`, `README.md`, `zie-framework/PROJECT.md`, `zie-framework/ROADMAP.md`, `zie-framework/project/components.md`

- [ ] **Step 1: Write failing test (RED)**
  Any test asserting `/zie-spec` etc. in docs will now need the new name; run suite first.

- [ ] **Step 2: Implement (GREEN)**
  ```bash
  # CLAUDE.md and README.md:
  sed -i '' 's|/zie-init|/init|g; s|/zie-backlog|/backlog|g; s|/zie-spec|/spec|g; s|/zie-plan|/plan|g; s|/zie-implement|/implement|g; s|/zie-fix|/fix|g; s|/zie-release|/release|g; s|/zie-retro|/retro|g; s|/zie-sprint|/sprint|g; s|/zie-status|/status|g; s|/zie-resync|/resync|g; s|/zie-audit|/audit|g' CLAUDE.md README.md

  # Knowledge docs:
  sed -i '' 's|/zie-init|/init|g; s|/zie-backlog|/backlog|g; s|/zie-spec|/spec|g; s|/zie-plan|/plan|g; s|/zie-implement|/implement|g; s|/zie-fix|/fix|g; s|/zie-release|/release|g; s|/zie-retro|/retro|g; s|/zie-sprint|/sprint|g; s|/zie-status|/status|g; s|/zie-resync|/resync|g; s|/zie-audit|/audit|g' zie-framework/PROJECT.md zie-framework/ROADMAP.md zie-framework/project/components.md zie-framework/project/architecture.md 2>/dev/null || true
  ```
  Also update `CLAUDE.md` SDLC Commands table header row references (command filenames if present).
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  ```bash
  grep '/zie-' CLAUDE.md README.md zie-framework/PROJECT.md zie-framework/ROADMAP.md zie-framework/project/components.md
  ```
  Must return empty (excluding archive/ paths and feature slugs).
  Run: `make test-unit` — still PASS

---

## Task 8: Final verification

<!-- depends_on: Task 2, Task 3, Task 4, Task 5, Task 6, Task 7 -->

**Acceptance Criteria:**
- `make test-ci` exits 0
- `grep -r '/zie-' commands/ hooks/ skills/ CLAUDE.md README.md tests/unit/` returns empty
- `ls commands/zie-*` returns "no matches" — all old files gone
- `ls commands/*.md` shows 12 plain-verb files

**Files:**
- No file edits — verification only

- [ ] **Step 1: Sweep for stragglers**
  ```bash
  grep -r '/zie-' commands/ hooks/ skills/ tests/unit/ CLAUDE.md README.md \
    --include='*.py' --include='*.md' | grep -v archive/
  ```
  Address any remaining occurrences in the appropriate task's file.

- [ ] **Step 2: Full test suite (GREEN)**
  ```bash
  make test-ci
  ```
  Must exit 0 with ≥48% coverage.

- [ ] **Step 3: Smoke check invocation surface**
  ```bash
  ls commands/
  # Expected: audit.md backlog.md fix.md implement.md init.md plan.md
  #           release.md resync.md retro.md spec.md sprint.md status.md
  ls commands/zie-* 2>&1 | grep "No such file" || echo "FAIL: old files still exist"
  ```

---

## Notes

- Tasks 2–7 are all independent and can run in parallel after Task 1 completes.
- The sed commands above are macOS-compatible (`sed -i ''`). On Linux, use `sed -i`.
- `test_sdlc_pipeline.py::TestIntentDetectUpdated` checks `"/zie-backlog"` in hook source — this must be updated in Task 4 alongside the hook itself.
- Do NOT update files under `zie-framework/archive/` — they are historical records.
- Do NOT update backlog slugs like `zie-plan-notes-trim.md` — these are feature names, not command references.
- Agent file names `agents/zie-implement-mode.md` and `agents/zie-audit-mode.md` are out of scope (they are mode configurations, not commands invoked with `/`).
