---
approved: true
approved_at: 2026-04-01
backlog: backlog/zie-sprint.md
spec: specs/2026-04-01-zie-sprint-design.md
---

# zie-sprint — Implementation Plan

**Goal:** Deliver `/zie-sprint` command that clears the full backlog in one invocation via phase-parallel pipeline.
**Architecture:** Pure orchestration — new `commands/zie-sprint.md` (already created), intent hook update, documentation. Zero new Python hook files. Command markdown drives all behavior via existing Agent/Skill tools.
**Tech Stack:** Markdown command, Python (intent-sdlc.py patch), pytest unit tests.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Exists | `commands/zie-sprint.md` | Command logic (already created) |
| Create | `tests/unit/test_zie_sprint.py` | Unit tests for command contract |
| Modify | `hooks/intent-sdlc.py` | Add sprint intent detection |
| Modify | `CLAUDE.md` | Document `/zie-sprint` in SDLC Commands |
| Modify | `commands/zie-status.md` | Add `/zie-sprint` to always-available suggestions |

---

## Task 1: Unit tests for zie-sprint command contract

**Acceptance Criteria:**
- `tests/unit/test_zie_sprint.py` exists and all tests pass
- Tests verify: command file exists, frontmatter keys, all 5 phases documented, key behaviors (parallel spec, WIP=1, batch release, context bundle, dry-run, dependency detection, error handling per phase)
- `make test-unit` GREEN

**Files:**
- Create: `tests/unit/test_zie_sprint.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_zie_sprint.py
  """Tests for /zie-sprint command contract."""
  from pathlib import Path
  import re

  REPO_ROOT = Path(__file__).parents[2]
  CMD = REPO_ROOT / "commands" / "zie-sprint.md"


  def _text():
      return CMD.read_text()


  class TestCommandExists:
      def test_file_exists(self):
          assert CMD.exists(), "commands/zie-sprint.md must exist"

      def test_frontmatter_has_description(self):
          assert "description:" in _text(), "must have frontmatter description"

      def test_frontmatter_has_allowed_tools(self):
          assert "allowed-tools:" in _text(), "must declare allowed-tools"

      def test_frontmatter_model_sonnet(self):
          assert "model: sonnet" in _text(), "model must be sonnet (orchestration work)"

      def test_frontmatter_effort_high(self):
          assert "effort: high" in _text(), "effort must be high (full sprint cycle)"


  class TestAuditPhase:
      def test_has_audit_step(self):
          assert "AUDIT" in _text(), "must have AUDIT step to classify items"

      def test_audit_classifies_items(self):
          text = _text()
          assert "needs_spec" in text or "Needs Spec" in text, \
              "AUDIT must classify items needing spec"

      def test_audit_asks_confirmation(self):
          text = _text()
          assert "yes" in text.lower() and "cancel" in text.lower(), \
              "AUDIT must ask for confirmation before executing"

      def test_dry_run_flag(self):
          assert "--dry-run" in _text(), "must support --dry-run flag"

      def test_dependency_detection(self):
          assert "depends_on" in _text(), "AUDIT must detect depends_on annotations"


  class TestPhaseStructure:
      def test_has_five_phases(self):
          text = _text()
          for n in ("1", "2", "3", "4", "5"):
              assert f"PHASE {n}" in text, f"must have PHASE {n}"

      def test_phase1_spec_parallel(self):
          text = _text()
          assert "PHASE 1" in text
          # Phase 1 section must describe parallel agents
          phase1_idx = text.index("PHASE 1")
          phase2_idx = text.index("PHASE 2")
          phase1_section = text[phase1_idx:phase2_idx]
          assert "parallel" in phase1_section.lower() or "run_in_background" in phase1_section, \
              "Phase 1 must use parallel agents for spec"

      def test_phase1_uses_draft_plan_flag(self):
          assert "--draft-plan" in _text(), \
              "Phase 1 must use --draft-plan to combine spec+plan in one agent call"

      def test_phase3_sequential_wip1(self):
          text = _text()
          phase3_idx = text.index("PHASE 3")
          phase4_idx = text.index("PHASE 4")
          phase3_section = text[phase3_idx:phase4_idx]
          assert "sequential" in phase3_section.lower() or "WIP=1" in phase3_section, \
              "Phase 3 must be sequential (WIP=1)"

      def test_phase4_batch_release(self):
          text = _text()
          phase4_idx = text.index("PHASE 4")
          phase5_idx = text.index("PHASE 5")
          phase4_section = text[phase4_idx:phase5_idx]
          assert "release" in phase4_section.lower(), \
              "Phase 4 must invoke release"

      def test_phase5_retro(self):
          text = _text()
          phase5_idx = text.index("PHASE 5")
          phase5_section = text[phase5_idx:]
          assert "retro" in phase5_section.lower(), \
              "Phase 5 must invoke retro"


  class TestContextBundle:
      def test_context_bundle_loaded_once(self):
          text = _text()
          assert "context_bundle" in text, \
              "must load context_bundle once and pass to all downstream agents"

      def test_context_bundle_referenced_in_phase1(self):
          text = _text()
          phase1_idx = text.index("PHASE 1")
          phase2_idx = text.index("PHASE 2")
          phase1_section = text[phase1_idx:phase2_idx]
          assert "context_bundle" in phase1_section, \
              "context_bundle must be referenced in PHASE 1 agent spawning"

      def test_context_bundle_referenced_in_phase3(self):
          text = _text()
          phase3_idx = text.index("PHASE 3")
          phase4_idx = text.index("PHASE 4")
          phase3_section = text[phase3_idx:phase4_idx]
          assert "context_bundle" in phase3_section, \
              "context_bundle must be referenced in PHASE 3 agent spawning"

      def test_adrs_loaded(self):
          assert "decisions" in _text(), \
              "context bundle must load decisions/*.md (ADRs)"

      def test_context_md_loaded(self):
          assert "context.md" in _text(), \
              "context bundle must load project/context.md"


  class TestArgumentParsing:
      def test_skip_ready_flag(self):
          assert "--skip-ready" in _text(), "must support --skip-ready flag"

      def test_version_override_flag(self):
          assert "--version=" in _text(), "must support --version=X.Y.Z flag"

      def test_slug_filtering(self):
          text = _text()
          assert "slugs" in text or "slug" in text.lower(), \
              "must support filtering by specific slugs"


  class TestErrorHandling:
      def test_empty_backlog_handling(self):
          text = _text()
          assert "empty" in text.lower() or "Nothing" in text, \
              "must handle empty backlog gracefully"

      def test_wip_active_handling(self):
          text = _text()
          assert "WIP" in text or "active" in text.lower(), \
              "must warn when WIP item is active"

      def test_phase_failure_halts(self):
          text = _text()
          assert "halt" in text.lower() or "STOP" in text or "stop" in text.lower(), \
              "phase failure must halt sprint"

      def test_phase5_retro_non_blocking(self):
          text = _text()
          assert "non-blocking" in text.lower() or "Non-blocking" in text, \
              "Phase 5 retro failure must be non-blocking"


  class TestSummaryOutput:
      def test_has_summary_section(self):
          assert "SPRINT COMPLETE" in _text() or "Summary" in _text(), \
              "must print sprint summary on completion"

      def test_summary_shows_shipped_count(self):
          text = _text()
          assert "Shipped" in text, "summary must show how many items were shipped"
  ```

  Run: `make test-unit` — must **FAIL** (file doesn't exist yet)

- [ ] **Step 2: Implement (GREEN)**

  The `commands/zie-sprint.md` file already exists. Run tests to verify
  which pass and which fail. Fix failing assertions by updating
  `commands/zie-sprint.md` to match expected contract. Key items to verify:

  - `model: sonnet` and `effort: high` in frontmatter
  - `PHASE 1`, `PHASE 2`, `PHASE 3`, `PHASE 4`, `PHASE 5` headings
  - `context_bundle` appears ≥3 times
  - `--draft-plan` in Phase 1 section
  - `sequential` or `WIP=1` in Phase 3 section
  - `non-blocking` in Phase 5 section
  - `SPRINT COMPLETE` in Summary section

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**

  No refactor needed — test file is already clean.
  Run: `make test-unit` — still PASS

---

## Task 2: Add sprint intent detection to intent-sdlc.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `hooks/intent-sdlc.py` has `"sprint"` key in `PATTERNS` dict with Thai + English patterns
- `SUGGESTIONS["sprint"]` = `"/zie-sprint"`
- Tests verify pattern matching and suggestion lookup

**Files:**
- Modify: `hooks/intent-sdlc.py`
- Create: `tests/unit/test_intent_sdlc_sprint.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_intent_sdlc_sprint.py
  """Tests for sprint intent detection in intent-sdlc hook."""
  import re
  import sys
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]

  sys.path.insert(0, str(REPO_ROOT / "hooks"))
  from intent_sdlc import PATTERNS, COMPILED_PATTERNS, SUGGESTIONS  # noqa: E402


  class TestSprintPatterns:
      def test_sprint_key_in_patterns(self):
          assert "sprint" in PATTERNS, \
              "PATTERNS must have 'sprint' key"

      def test_sprint_suggestion(self):
          assert SUGGESTIONS.get("sprint") == "/zie-sprint", \
              "SUGGESTIONS['sprint'] must be '/zie-sprint'"

      def test_english_sprint_pattern(self):
          patterns = COMPILED_PATTERNS["sprint"]
          assert any(p.search("sprint") for p in patterns), \
              "must match English 'sprint'"

      def test_clear_backlog_pattern(self):
          patterns = COMPILED_PATTERNS["sprint"]
          assert any(p.search("clear backlog") for p in patterns), \
              "must match 'clear backlog'"

      def test_thai_clear_backlog_pattern(self):
          patterns = COMPILED_PATTERNS["sprint"]
          assert any(p.search("เคลียร์ backlog") for p in patterns), \
              "must match Thai 'เคลียร์ backlog'"

      def test_ship_all_pattern(self):
          patterns = COMPILED_PATTERNS["sprint"]
          assert any(p.search("ship all") for p in patterns), \
              "must match 'ship all'"

      def test_zie_sprint_pattern(self):
          patterns = COMPILED_PATTERNS["sprint"]
          assert any(p.search("zie-sprint") for p in patterns), \
              "must match 'zie-sprint'"
  ```

  Run: `make test-unit` — must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  Add to `hooks/intent-sdlc.py`:

  **Exact insertion in `hooks/intent-sdlc.py`:**

  1. In `PATTERNS` dict — insert after the `"retro"` entry, before `"status"`:
  ```python
      "retro": [
          ...
      ],
      "sprint": [
          r"\bsprint\b", r"zie.?sprint",
          r"clear.*backlog", r"เคลียร์.*backlog",
          r"ship.*all", r"ทำ.*ทั้งหมด",
          r"batch.*release", r"full.*pipeline",
      ],
      "status": [
  ```

  2. In `SUGGESTIONS` dict — insert after `"retro"` entry, before `"status"` entry:
  ```python
      "retro":     "/zie-retro",
      "sprint":    "/zie-sprint",
      "status":    "/zie-status",
  ```

  3. Verify valid Python syntax after edit:
  ```bash
  python3 -m py_compile hooks/intent-sdlc.py && echo "OK"
  ```
  Must print `OK`.

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**

  Import `intent_sdlc` in tests uses underscore — `hooks/intent-sdlc.py` is
  importable as `intent_sdlc` (Python converts `-` to `_` via sys.path insert).
  Confirmed by `py_compile` check in Step 2. No code changes needed.
  Run: `make test-unit` — still PASS

---

## Task 3: Documentation updates

<!-- depends_on: Task 1, Task 2 -->

**Acceptance Criteria:**
- `CLAUDE.md` SDLC Commands section mentions `/zie-sprint`
- `commands/zie-status.md` includes `/zie-sprint` in always-available list
- Tests verify both documentation items

**Files:**
- Modify: `CLAUDE.md`
- Modify: `commands/zie-status.md`
- Create: `tests/unit/test_zie_sprint_docs.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_zie_sprint_docs.py
  """Tests that /zie-sprint is documented in CLAUDE.md and zie-status."""
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]


  def _claude_md():
      return (REPO_ROOT / "CLAUDE.md").read_text()


  def _status_cmd():
      return (REPO_ROOT / "commands" / "zie-status.md").read_text()


  class TestClaudeMdDocumentation:
      def test_zie_sprint_in_claude_md(self):
          assert "/zie-sprint" in _claude_md(), \
              "CLAUDE.md must mention /zie-sprint"

      def test_zie_sprint_has_description_in_claude_md(self):
          text = _claude_md()
          idx = text.index("/zie-sprint")
          snippet = text[idx:idx + 120]
          assert "sprint" in snippet.lower() or "batch" in snippet.lower() or "backlog" in snippet.lower(), \
              "/zie-sprint entry in CLAUDE.md must describe sprint clear behavior"


  class TestZieStatusSuggestions:
      def test_zie_sprint_in_status_suggestions(self):
          assert "/zie-sprint" in _status_cmd(), \
              "zie-status.md must include /zie-sprint in always-available suggestions"
  ```

  Run: `make test-unit` — must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  **CLAUDE.md** — append to the `## SDLC State` section (last paragraph before the end of file).
  The `## SDLC State` section currently ends with:
  ```
  Managed by zie-framework itself — see `zie-framework/ROADMAP.md` for current
  backlog.
  ```
  Add a new `## SDLC Commands` section immediately after that paragraph:
  ```markdown
  ## SDLC Commands

  | Command | Purpose |
  | --- | --- |
  | `/zie-backlog` | Capture a new idea as a backlog item |
  | `/zie-spec` | Write design spec for a backlog item |
  | `/zie-plan` | Draft implementation plan from spec |
  | `/zie-implement` | TDD implementation loop (WIP=1) |
  | `/zie-release` | Release gate — merge dev→main, version bump |
  | `/zie-retro` | Post-release retrospective + ADRs |
  | `/zie-sprint` | Sprint clear — batch all items: spec + plan + implement + release + retro |
  | `/zie-fix` | Debug and fix failing tests or broken features |
  | `/zie-status` | Show current SDLC state |
  | `/zie-audit` | Project audit across 9 dimensions |
  ```

  **commands/zie-status.md** — locate the exact string `Always available:` (line 127).
  The current line reads:
  ```
  Always available: "/zie-status | /zie-backlog | /zie-implement | /zie-fix | /zie-release | /zie-retro"
  ```
  Replace with:
  ```
  Always available: "/zie-status | /zie-backlog | /zie-implement | /zie-fix | /zie-release | /zie-retro | /zie-sprint"
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**

  No refactor needed.
  Run: `make test-unit` — still PASS
