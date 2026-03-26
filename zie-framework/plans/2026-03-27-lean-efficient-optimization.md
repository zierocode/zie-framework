---
approved: true
approved_at: 2026-03-27
backlog: backlog/lean-efficient-optimization.md
spec: specs/2026-03-27-lean-efficient-optimization-design.md
---

# Lean & Efficient Optimization — Implementation Plan

**Goal:** Reduce zie-framework token overhead from ~70% to ~40% of session cost by consolidating hooks, right-sizing models/effort, overhauling zie-audit, and removing arbitrary parallel caps.

**Architecture:** Five layers implemented in priority order. Layers 1–3 (hooks + audit + effort) deliver ~85% of savings and are pure Python/Markdown changes with no API surface changes. Layers 4–5 (command slimming + plans archive) are isolated cleanup with no test dependencies.

**Tech Stack:** Python 3.x hooks, Markdown commands/skills, JSON hooks.json, pytest for TDD.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `hooks/intent-sdlc.py` | Merged UserPromptSubmit hook (intent + SDLC context in one pass) |
| Delete | `hooks/intent-detect.py` | Replaced by intent-sdlc.py |
| Delete | `hooks/sdlc-context.py` | Replaced by intent-sdlc.py |
| Modify | `hooks/utils.py` | Add `get_cached_roadmap()` + `write_roadmap_cache()` |
| Modify | `hooks/hooks.json` | Replace 2 UserPromptSubmit entries with 1; add background:true to wip-checkpoint; default safety_check_mode regex |
| Modify | `hooks/subagent-context.py` | Use ROADMAP cache |
| Modify | `hooks/sdlc-compact.py` | Use ROADMAP cache |
| Modify | `hooks/failure-context.py` | Use ROADMAP cache |
| Modify | `commands/zie-audit.md` | 3 Sonnet agents + synthesis, effort:medium, WebSearch 15 |
| Modify | `skills/zie-audit/SKILL.md` | model:sonnet, effort:medium |
| Modify | `commands/zie-retro.md` | effort:high → effort:medium |
| Modify | `commands/zie-implement.md` | Remove parallel cap, trim to ~150 lines |
| Modify | `commands/zie-plan.md` | Remove parallel cap (effort already medium) |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update EXPECTED: zie-audit opus/high → sonnet/medium; zie-retro sonnet/high → sonnet/medium |
| Modify | `Makefile` | Add `archive-plans` target |
| Modify | `hooks/knowledge-hash.py` | Skip `plans/archive/` |
| Modify | `commands/zie-resync.md` | Exclude `plans/archive/` from scope |
| Create | `tests/unit/test_intent_sdlc.py` | Unit tests for merged hook |
| Create | `tests/unit/test_roadmap_cache.py` | Unit tests for cache functions |

---

## Task 1: ROADMAP Cache Utility Functions

**Acceptance Criteria:**
- `get_cached_roadmap(session_id, ttl=30)` returns cached content when cache file exists and is fresh (age < ttl)
- Returns `None` when no cache file exists
- Returns `None` when cache is stale (age ≥ ttl)
- `write_roadmap_cache(session_id, content)` writes to `/tmp/zie-{session_id}/roadmap.cache`, creating dirs as needed
- Both functions handle all exceptions silently (return None on error)

**Files:**
- Modify: `hooks/utils.py`
- Create: `tests/unit/test_roadmap_cache.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_roadmap_cache.py
  import time
  from pathlib import Path
  from unittest.mock import patch
  import pytest

  # Import after sys.path setup in conftest
  from hooks.utils import get_cached_roadmap, write_roadmap_cache

  def test_get_returns_none_when_no_cache(tmp_path):
      with patch("hooks.utils.Path") as mock_path:
          # no cache file exists
          result = get_cached_roadmap("sess-abc", ttl=30)
          assert result is None

  def test_write_then_read_within_ttl(tmp_path, monkeypatch):
      monkeypatch.setenv("TMPDIR", str(tmp_path))
      write_roadmap_cache("sess-abc", "# ROADMAP\n")
      result = get_cached_roadmap("sess-abc", ttl=30)
      assert result == "# ROADMAP\n"

  def test_get_returns_none_when_expired(tmp_path, monkeypatch):
      monkeypatch.setenv("TMPDIR", str(tmp_path))
      write_roadmap_cache("sess-abc", "# ROADMAP\n")
      cache_file = tmp_path / "zie-sess-abc" / "roadmap.cache"
      # backdate mtime by 60 seconds
      old_time = time.time() - 60
      import os; os.utime(cache_file, (old_time, old_time))
      result = get_cached_roadmap("sess-abc", ttl=30)
      assert result is None

  def test_get_returns_none_on_read_error():
      # session_id that produces path with no permissions — returns None, not raises
      result = get_cached_roadmap("", ttl=30)
      assert result is None

  def test_write_creates_parent_dirs(tmp_path, monkeypatch):
      monkeypatch.setenv("TMPDIR", str(tmp_path))
      write_roadmap_cache("new-sess", "content")
      cache_file = tmp_path / "zie-new-sess" / "roadmap.cache"
      assert cache_file.exists()
  ```

  Run: `make test-unit` — must **FAIL** (functions not yet defined)

- [ ] **Step 2: Implement (GREEN)**

  Add to `hooks/utils.py` after existing imports:

  ```python
  import time

  def get_cached_roadmap(session_id: str, ttl: int = 30) -> str | None:
      """Return cached ROADMAP content if fresh, else None."""
      try:
          cache_path = Path(f"/tmp/zie-{session_id}/roadmap.cache")
          if cache_path.exists():
              age = time.time() - cache_path.stat().st_mtime
              if age < ttl:
                  return cache_path.read_text()
          return None
      except Exception:
          return None

  def write_roadmap_cache(session_id: str, content: str) -> None:
      """Write ROADMAP content to session cache."""
      try:
          cache_dir = Path(f"/tmp/zie-{session_id}")
          cache_dir.mkdir(parents=True, exist_ok=True)
          (cache_dir / "roadmap.cache").write_text(content)
      except Exception:
          pass
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**
  - Ensure `time` import is not duplicated (utils.py may already import it via other functions — check and consolidate)
  - Run: `make test-unit` — still PASS

---

## Task 2: Merge intent-detect + sdlc-context → intent-sdlc

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `intent-sdlc.py` fires once per UserPromptSubmit and outputs combined intent + SDLC context in a single `additionalContext` JSON payload
- Reads ROADMAP.md via `get_cached_roadmap()` first; falls back to disk + writes cache
- Preserves all early-exit guards from intent-detect (len < 3, len > 1000, starts `---`, starts `/zie-`)
- Preserves intent detection logic (PATTERNS, COMPILED_PATTERNS, SUGGESTIONS) unchanged
- Preserves SDLC context logic (parse_roadmap_now, derive_stage, get_test_status) unchanged
- hooks.json UserPromptSubmit section has exactly 1 hook entry (intent-sdlc)
- intent-detect.py and sdlc-context.py deleted

**Files:**
- Create: `hooks/intent-sdlc.py`
- Delete: `hooks/intent-detect.py`
- Delete: `hooks/sdlc-context.py`
- Modify: `hooks/hooks.json`
- Create: `tests/unit/test_intent_sdlc.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_intent_sdlc.py
  import json, sys
  from pathlib import Path
  from unittest.mock import patch, MagicMock
  import pytest

  # Hook is tested via exec_module pattern (existing test convention)

  def make_event(prompt="implement the feature", cwd=None):
      return {"prompt": prompt, "cwd": str(cwd or "/tmp/test-project")}

  def test_intent_sdlc_outputs_combined_context(tmp_path, monkeypatch, capsys):
      """Both intent and SDLC context appear in single additionalContext output."""
      zie_dir = tmp_path / "zie-framework"
      zie_dir.mkdir()
      (zie_dir / "ROADMAP.md").write_text(
          "## Now\n- [ ] my-feature — implement\n"
      )
      # Run hook with implement prompt
      event = json.dumps(make_event(prompt="implement the feature", cwd=str(tmp_path)))
      with patch("sys.stdin.read", return_value=event):
          # execute hook module
          ...  # use project's exec_module test pattern
      captured = capsys.readouterr()
      out = json.loads(captured.out)
      ctx = out["additionalContext"]
      assert "implement" in ctx.lower()
      assert "sdlc" in ctx.lower() or "task" in ctx.lower()

  def test_intent_sdlc_early_exit_short_message(tmp_path, monkeypatch, capsys):
      """Messages shorter than 3 chars produce no output."""
      event = json.dumps(make_event(prompt="hi", cwd=str(tmp_path)))
      with patch("sys.stdin.read", return_value=event):
          ...
      captured = capsys.readouterr()
      assert captured.out.strip() == ""

  def test_intent_sdlc_reads_roadmap_once(tmp_path, monkeypatch):
      """ROADMAP.md is read at most once per hook invocation (cache check + optional disk read)."""
      zie_dir = tmp_path / "zie-framework"
      zie_dir.mkdir()
      roadmap = zie_dir / "ROADMAP.md"
      roadmap.write_text("## Now\n")
      read_count = 0
      original_read = Path.read_text
      def counting_read(self, **kwargs):
          nonlocal read_count
          if "ROADMAP" in str(self):
              read_count += 1
          return original_read(self, **kwargs)
      with patch.object(Path, "read_text", counting_read):
          ...  # invoke hook
      assert read_count <= 1
  ```

  Run: `make test-unit` — must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  Create `hooks/intent-sdlc.py` combining both hooks:
  - Copy PATTERNS, COMPILED_PATTERNS, SUGGESTIONS, MAX_MESSAGE_LEN from intent-detect.py
  - Copy STAGE_KEYWORDS, STAGE_COMMANDS, STALE_THRESHOLD_SECS, derive_stage(), get_test_status() from sdlc-context.py
  - Early-exit guards from intent-detect (before ROADMAP read — saves disk I/O on filtered messages)
  - Read ROADMAP once: `get_cached_roadmap(session_id)` → fallback disk read → `write_roadmap_cache()`
  - Extract `session_id` from `event.get("session_id", "default")`
  - Build combined context string:
    ```python
    parts = []
    if intent_cmd:
        parts.append(f"intent:{best} → {intent_cmd}")
    parts.append(f"task:{active_task} | stage:{stage} | next:{suggested_cmd} | tests:{test_status}")
    context = "[zie-framework] " + " | ".join(parts)
    print(json.dumps({"additionalContext": context}))
    ```

  Update `hooks/hooks.json` UserPromptSubmit:
  ```json
  "UserPromptSubmit": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/intent-sdlc.py\""
        }
      ]
    }
  ]
  ```

  Delete `hooks/intent-detect.py` and `hooks/sdlc-context.py`.

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**
  - Remove any duplicate imports between the two merged files
  - Ensure two-tier error handling: outer `try/except Exception → sys.exit(0)`, inner logs to stderr
  - Run: `make test` — all tests PASS (including integration)

---

## Task 3: Update ROADMAP Readers to Use Cache

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `subagent-context.py`, `sdlc-compact.py`, `failure-context.py` each call `get_cached_roadmap()` before disk read
- On cache miss: read from disk, call `write_roadmap_cache()`
- On cache hit: skip disk read entirely
- All three hooks still produce identical output compared to current behavior

**Files:**
- Modify: `hooks/subagent-context.py`
- Modify: `hooks/sdlc-compact.py`
- Modify: `hooks/failure-context.py`

- [ ] **Step 1: Write failing tests (RED)**

  For each hook, add a test asserting that when a valid cache exists, `Path.read_text` is NOT called for the ROADMAP path. Use existing hook test patterns.

  Run: `make test-unit` — must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  In each hook, replace the direct `roadmap_path.read_text()` pattern with:

  ```python
  from utils import get_cached_roadmap, write_roadmap_cache
  session_id = event.get("session_id", "default")
  roadmap_content = get_cached_roadmap(session_id)
  if roadmap_content is None:
      roadmap_content = roadmap_path.read_text()
      write_roadmap_cache(session_id, roadmap_content)
  ```

  Then pass `roadmap_content` to `parse_roadmap_now()` or equivalent parse call (adjust signature if needed — prefer passing content over path where possible).

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**
  - Confirm each hook still exits 0 on all error paths
  - Run: `make test` — PASS

---

## Task 4: hooks.json Config Changes

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `wip-checkpoint` PostToolUse hook entry has `"background": true`
- The default `safety_check_mode` documented in hooks.json (or `.config` template) is `"regex"`, not `"agent"`
- Integration test confirms wip-checkpoint runs in background (non-blocking)

**Files:**
- Modify: `hooks/hooks.json`
- Modify: `templates/.config.template` (if safety_check_mode documented there)

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # In existing test_hooks_json.py or new file
  def test_wip_checkpoint_is_background():
      hooks = json.loads((REPO_ROOT / "hooks/hooks.json").read_text())
      post_tool_hooks = hooks["hooks"]["PostToolUse"]
      wip_entries = [
          h for group in post_tool_hooks
          for h in group["hooks"]
          if "wip-checkpoint" in h["command"]
      ]
      assert len(wip_entries) == 1
      assert wip_entries[0].get("background") is True
  ```

  Run: `make test-unit` — must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/hooks.json` PostToolUse section, update wip-checkpoint entry:
  ```json
  {
    "type": "command",
    "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/wip-checkpoint.py\"",
    "background": true
  }
  ```

  Update `.config` template default (if `safety_check_mode` is present) to `"regex"`.
  Update `_hook_output_protocol` comment or inline docs if safety_check_mode is documented there.

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**
  - Verify `safety_check_agent.py` already handles `safety_check_mode: "regex"` as the fallback path (it should — check line 74 fallback)
  - Run: `make test` — PASS

---

## Task 5: zie-audit Command Rewrite

**Acceptance Criteria:**
- `commands/zie-audit.md` has `model: sonnet` and `effort: medium` in frontmatter
- Command spawns 3 parallel dimension agents (Security / Code Health / Structural) + 1 synthesis agent
- Each dimension agent: max 5 WebSearch queries
- Synthesis agent: 0 WebSearch, receives all 3 agent outputs, deduplicates + scores + ranks findings
- Total line count ≤ 160 lines
- No mention of Opus in the command

**Files:**
- Modify: `commands/zie-audit.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # test_model_effort_frontmatter.py — update EXPECTED (this test will FAIL
  # until zie-audit.md frontmatter is updated in GREEN step)
  # Change in EXPECTED:
  #   "commands/zie-audit.md": ("sonnet", "medium"),  # was ("opus", "high")
  ```

  Run: `make test-unit` — must **FAIL** (EXPECTED mismatch)

- [ ] **Step 2: Implement (GREEN)**

  Rewrite `commands/zie-audit.md`. New structure:

  ```markdown
  ---
  model: sonnet
  effort: medium
  ---

  # /zie-audit — 9-Dimension Project Audit

  Audit the codebase across Security, Code Health, and Structural dimensions.
  Produces scored findings for backlog prioritization.

  ## Phase 1 — Research Profile

  Read manifests (package.json / pyproject.toml / go.mod / etc.) to build:
  - `stack`: languages + frameworks
  - `domain`: app type (web API / CLI / plugin / data pipeline)
  - `deps`: key dependencies + versions

  ## Phase 2 — Parallel Dimension Scan

  Spawn 3 Agents simultaneously:

  **Agent 1 — Security**
  Focus: hardcoded secrets, shell injection, input validation, auth gaps,
  error leakage, path traversal. Max 5 WebSearch queries (CVEs, known patterns).
  Output: findings list with severity (CRITICAL / HIGH / MEDIUM / LOW).

  **Agent 2 — Code Health** (Lean + Quality + Testing)
  Focus: dead code, duplication, over-engineering, untested modules, weak
  assertions, coverage gaps, fragile tests. Max 5 WebSearch queries.
  Output: findings list with severity.

  **Agent 3 — Structural** (Docs + Architecture)
  Focus: stale docs, broken examples, coupling violations, SRP issues,
  inconsistent naming, silent failures, missing interfaces. Max 5 WebSearch.
  Output: findings list with severity.

  Wait for all 3 agents to complete before Phase 3.

  ## Phase 3 — Synthesis

  Spawn 1 Agent with all 3 dimension outputs:
  - Deduplicate overlapping findings
  - Score each finding (1–10 impact × 1–10 effort)
  - Rank: CRITICAL first, then by score descending
  - Flag any coverage gaps (dimensions that produced fewer than 3 findings)
  - Produce final scored report

  ## Phase 4 — Backlog Integration

  For each CRITICAL or HIGH finding:
  - Ask Zie: "Add to backlog? (yes / skip)"
  - If yes: create `zie-framework/backlog/<slug>.md` + update ROADMAP Next

  ## Output Format

  Print scored report with dimension headers, finding descriptions, severity,
  and recommended action. Save to `zie-framework/audit-<date>.md` if Zie confirms.
  ```

  Run: `make test-unit` — must **PASS** (after EXPECTED map updated in Task 6)

- [ ] **Step 3: Refactor**
  - Verify line count ≤ 160: `wc -l commands/zie-audit.md`
  - Run: `make test` — PASS

---

## Task 6: Update zie-audit SKILL.md + Test Frontmatter Map

<!-- depends_on: Task 5 -->

**Acceptance Criteria:**
- `skills/zie-audit/SKILL.md` frontmatter: `model: sonnet`, `effort: medium`
- `tests/unit/test_model_effort_frontmatter.py` EXPECTED map updated:
  - `"commands/zie-audit.md"`: `("sonnet", "medium")`
  - `"skills/zie-audit/SKILL.md"`: `("sonnet", "medium")`
- All frontmatter tests pass

**Files:**
- Modify: `skills/zie-audit/SKILL.md`
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  Update EXPECTED in test file:
  ```python
  "commands/zie-audit.md":     ("sonnet", "medium"),  # was ("opus", "high")
  "skills/zie-audit/SKILL.md": ("sonnet", "medium"),  # was ("opus", "high")
  ```

  Run: `make test-unit` — must **FAIL** (SKILL.md still has opus/high)

- [ ] **Step 2: Implement (GREEN)**

  Update `skills/zie-audit/SKILL.md` frontmatter:
  ```yaml
  ---
  model: sonnet
  effort: medium
  ---
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**
  - Confirm no other test files reference opus for zie-audit
  - Run: `make test` — PASS

---

## Task 7: Effort Right-sizing — zie-retro

**Acceptance Criteria:**
- `commands/zie-retro.md` frontmatter: `effort: medium` (was `high`)
- `tests/unit/test_model_effort_frontmatter.py` EXPECTED updated: `"commands/zie-retro.md": ("sonnet", "medium")`
- Verify `commands/zie-plan.md` is already `effort: medium` — no change needed

**Files:**
- Modify: `commands/zie-retro.md`
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing tests (RED)**

  Update EXPECTED:
  ```python
  "commands/zie-retro.md": ("sonnet", "medium"),  # was ("sonnet", "high")
  ```

  Run: `make test-unit` — must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  Update `commands/zie-retro.md` frontmatter: `effort: medium`

  Verify `commands/zie-plan.md` current frontmatter — if already `effort: medium`, no change.

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**
  - Run: `make test` — PASS

---

## Task 8: Slim zie-implement.md + Remove Parallel Cap

**Acceptance Criteria:**
- `commands/zie-implement.md` total line count ≤ 160 (from 351)
- No mention of "max parallel tasks: 4" or any hard parallel cap
- `depends_on` syntax and file-conflict detection logic preserved
- Core TDD flow (RED/GREEN/REFACTOR per task) intact

**Files:**
- Modify: `commands/zie-implement.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # test_command_line_counts.py (new or existing)
  def test_zie_implement_line_count():
      content = (REPO_ROOT / "commands/zie-implement.md").read_text()
      lines = content.splitlines()
      assert len(lines) <= 160, f"zie-implement.md is {len(lines)} lines (max 160)"

  def test_zie_implement_no_parallel_cap():
      content = (REPO_ROOT / "commands/zie-implement.md").read_text()
      assert "max parallel tasks: 4" not in content
      assert "max 4 parallel" not in content.lower()
  ```

  Run: `make test-unit` — must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/zie-implement.md`:
  - Replace parallelization section (30+ lines explaining parallel execution) with:
    ```
    Run tasks in parallel where possible. Tasks with `<!-- depends_on: TN -->` run
    after their dependency. Tasks sharing output files must be serialized.
    ```
  - Remove hard "Max parallel tasks: 4" constraint; replace with:
    ```
    Parallelize all independent tasks. Use `depends_on` for ordering, not caps.
    ```
  - Collapse dependency analysis walkthrough to 3 bullets
  - Remove repetitive "File conflict check" prose (keep single rule)
  - Keep: TDD loop (RED/GREEN/REFACTOR), impl-reviewer trigger logic, pre-ship verification

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**
  - Read the slimmed command once more — confirm TDD intent is clear despite brevity
  - Run: `make test` — PASS

---

## Task 9: Remove Parallel Cap from zie-plan.md

**Acceptance Criteria:**
- `commands/zie-plan.md` has no mention of "max 4 parallel Agents" or hard cap
- Core plan drafting logic intact

**Files:**
- Modify: `commands/zie-plan.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  def test_zie_plan_no_parallel_cap():
      content = (REPO_ROOT / "commands/zie-plan.md").read_text()
      assert "max 4 parallel" not in content.lower()
      assert "max parallel agents: 4" not in content.lower()
  ```

  Run: `make test-unit` — must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/zie-plan.md`:
  - Remove "Max parallel Agents: 4" constraint line
  - Replace with: "Spawn parallel Agents for each slug. Use `depends_on` for slugs sharing output files."

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**
  - Run: `make test` — PASS

---

## Task 10: Archive plans/ Infrastructure

**Acceptance Criteria:**
- `make archive-plans` moves `.md` files older than 60 days from `zie-framework/plans/` to `zie-framework/plans/archive/`
- `hooks/knowledge-hash.py` skips `zie-framework/plans/archive/` during hash computation
- `commands/zie-resync.md` mentions excluding `plans/archive/` from resync scope

**Files:**
- Modify: `Makefile`
- Modify: `hooks/knowledge-hash.py`
- Modify: `commands/zie-resync.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  def test_makefile_has_archive_plans_target():
      makefile = (REPO_ROOT / "Makefile").read_text()
      assert "archive-plans:" in makefile

  def test_knowledge_hash_skips_archive(tmp_path):
      # create a plans/archive/ file and verify hash computation skips it
      archive_dir = tmp_path / "zie-framework" / "plans" / "archive"
      archive_dir.mkdir(parents=True)
      (archive_dir / "old-plan.md").write_text("# old")
      # run knowledge-hash and verify archive file not included
      ...
  ```

  Run: `make test-unit` — must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  Add to `Makefile`:
  ```makefile
  archive-plans:
  	@mkdir -p zie-framework/plans/archive
  	@find zie-framework/plans -maxdepth 1 -name "*.md" \
  	  -mtime +60 -exec mv {} zie-framework/plans/archive/ \;
  	@echo "[zie-framework] Archived plans older than 60 days"
  ```

  In `hooks/knowledge-hash.py`, add exclusion for `plans/archive`:
  ```python
  # In the directory traversal loop — skip archive
  if "plans/archive" in str(path):
      continue
  ```

  In `commands/zie-resync.md`, add note:
  ```
  Exclude `zie-framework/plans/archive/` — historical plans, not active knowledge.
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**
  - Run `make archive-plans` manually and verify it works on the real `plans/` directory
  - Run: `make test` — PASS

---

## Execution Order

```
T1 (cache utils)
├── T2 (merge hooks)      ← depends_on T1
│   └── T4 (hooks.json)   ← depends_on T2
└── T3 (cache readers)    ← depends_on T1

T5 (audit rewrite)
└── T6 (SKILL + test map) ← depends_on T5

T7 (retro effort)         ← independent
T8 (slim implement)       ← independent
T9 (plan cap)             ← independent
T10 (archive plans)       ← independent

Parallel batch A: T2 + T3 (after T1)
Parallel batch B: T5, T7, T8, T9, T10 (all independent)
Sequential: T4 after T2; T6 after T5
```
