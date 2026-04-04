---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-subagent-context-idle-overhead.md
---

# Lean Subagent Context — Implementation Plan

**Goal:** Eliminate subagent-context.py overhead when the Now lane is idle and split the combined `"Explore|Plan"` hooks.json matcher into two explicit entries.

**Architecture:** Two targeted changes: (1) add a one-line early-exit guard in `subagent-context.py` after the ROADMAP read — if `feature_slug == "none"` skip all remaining I/O and emit nothing; (2) replace the single `"Explore|Plan"` SubagentStart entry in `hooks.json` with two separate entries (one `"Explore"`, one `"Plan"`) both pointing to the same script. Tests cover both idle-state no-output and split-matcher assertions.

**Tech Stack:** Python 3.x, pytest, JSON

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/subagent-context.py` | Add idle early-exit guard after ROADMAP read |
| Modify | `hooks/hooks.json` | Split SubagentStart into two entries: `"Explore"` and `"Plan"` |
| Modify | `tests/unit/test_hooks_subagent_context.py` | Add idle-state no-output tests; update matcher assertion |
| Modify | `tests/unit/test_hooks_json.py` | Update SubagentStart matcher test to assert two entries |

---

## Task 1: Add idle early-exit to subagent-context.py

<!-- depends_on: none -->

**Acceptance Criteria:**
- When Now lane is empty (`feature_slug == "none"`), the hook emits no stdout and exits 0
- When Now lane has an active task, the hook continues normally and emits context
- Existing tests remain green

**Files:**
- Modify: `hooks/subagent-context.py`
- Modify: `tests/unit/test_hooks_subagent_context.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_hooks_subagent_context.py` inside `TestSubagentContextMissingFiles`:

  ```python
  def test_explore_idle_no_active_task_produces_no_output(self, tmp_path):
      """Explore agent when Now lane is empty → no output (idle early-exit)."""
      # No roadmap means feature_slug == "none"
      cwd = make_cwd(tmp_path, context_md=SAMPLE_CONTEXT_MD)
      r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
      assert r.returncode == 0
      assert r.stdout.strip() == "", (
          f"Expected no output when idle, got: {r.stdout!r}"
      )

  def test_plan_idle_no_active_task_produces_no_output(self, tmp_path):
      """Plan agent when Now lane is empty → no output (idle early-exit)."""
      cwd = make_cwd(tmp_path, context_md=SAMPLE_CONTEXT_MD)
      r = run_hook({"agentType": "Plan"}, tmp_cwd=cwd)
      assert r.returncode == 0
      assert r.stdout.strip() == "", (
          f"Expected no output when idle, got: {r.stdout!r}"
      )

  def test_explore_active_task_still_emits_context(self, tmp_path):
      """Sanity: active Now lane still emits context payload after guard."""
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                     context_md=SAMPLE_CONTEXT_MD)
      r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
      ctx = parse_context(r)
      assert "Active:" in ctx
      assert r.stdout.strip() != ""
  ```

  Run: `make test-unit` — must FAIL (no early-exit guard yet)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/subagent-context.py`, after the ROADMAP read block (after `feature_slug` is set), add:

  ```python
  # Early-exit when idle — no active task, no useful context to inject
  if feature_slug == "none":
      sys.exit(0)
  ```

  Insert this block immediately after the `except Exception as e:` / `print(...)` close of the ROADMAP read try/except — before the plans/ glob block and before the ADR count read.

  Final position in script (after line ~48 in current file):
  ```python
  except Exception as e:
      print(f"[zie-framework] subagent-context: {e}", file=sys.stderr)

  # Early-exit when idle — no active task, no useful context to inject
  if feature_slug == "none":
      sys.exit(0)

  # Find most-recent plan file...
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the guard placement is clean: it sits after `feature_slug` is fully resolved but before all I/O that depends on an active task. No other changes needed — the guard is one block.

  Run: `make test-unit` — still PASS

---

## Task 2: Split hooks.json SubagentStart matcher

<!-- depends_on: none -->

**Acceptance Criteria:**
- `hooks.json` SubagentStart has exactly two entries: one with matcher `"Explore"`, one with matcher `"Plan"`
- Both entries point to the same `subagent-context.py` script
- The old `"Explore|Plan"` combined entry is gone
- Existing test `test_subagentstart_matcher_is_explore_or_plan` is updated to assert two entries

**Files:**
- Modify: `hooks/hooks.json`
- Modify: `tests/unit/test_hooks_subagent_context.py`
- Modify: `tests/unit/test_hooks_json.py`

- [ ] **Step 1: Write failing tests (RED)**

  Update `tests/unit/test_hooks_subagent_context.py` — in class `TestHooksJsonRegistration`, replace `test_subagentstart_matcher_is_explore_or_plan`:

  ```python
  def test_subagentstart_has_two_entries(self):
      """SubagentStart must have exactly two entries: Explore and Plan."""
      hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
      data = json.loads(hooks_json.read_text())
      entries = data["hooks"]["SubagentStart"]
      assert len(entries) == 2, (
          f"Expected 2 SubagentStart entries (Explore + Plan), got {len(entries)}"
      )

  def test_subagentstart_has_explore_matcher(self):
      hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
      data = json.loads(hooks_json.read_text())
      matchers = [e.get("matcher") for e in data["hooks"]["SubagentStart"]]
      assert "Explore" in matchers, f"No 'Explore' matcher in SubagentStart: {matchers}"

  def test_subagentstart_has_plan_matcher(self):
      hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
      data = json.loads(hooks_json.read_text())
      matchers = [e.get("matcher") for e in data["hooks"]["SubagentStart"]]
      assert "Plan" in matchers, f"No 'Plan' matcher in SubagentStart: {matchers}"

  def test_subagentstart_combined_matcher_gone(self):
      """The old combined 'Explore|Plan' matcher must not exist."""
      hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
      data = json.loads(hooks_json.read_text())
      matchers = [e.get("matcher") for e in data["hooks"]["SubagentStart"]]
      assert "Explore|Plan" not in matchers, (
          "Old combined 'Explore|Plan' matcher still present — must be split"
      )

  def test_both_entries_reference_same_script(self):
      """Both SubagentStart entries must point to subagent-context.py."""
      hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
      data = json.loads(hooks_json.read_text())
      for entry in data["hooks"]["SubagentStart"]:
          cmd = entry["hooks"][0]["command"]
          assert "subagent-context.py" in cmd, (
              f"SubagentStart entry does not reference subagent-context.py: {cmd}"
          )
  ```

  Also add to `tests/unit/test_hooks_json.py` a new class:

  ```python
  class TestHooksJsonSubagentStartSplit:
      def _load(self):
          with open(HOOKS_JSON) as f:
              return json.load(f)

      def test_subagentstart_has_two_entries(self):
          data = self._load()
          entries = data["hooks"]["SubagentStart"]
          assert len(entries) == 2, (
              f"Expected 2 SubagentStart entries (Explore + Plan), got {len(entries)}"
          )

      def test_subagentstart_explore_matcher_present(self):
          data = self._load()
          matchers = [e.get("matcher") for e in data["hooks"]["SubagentStart"]]
          assert "Explore" in matchers

      def test_subagentstart_plan_matcher_present(self):
          data = self._load()
          matchers = [e.get("matcher") for e in data["hooks"]["SubagentStart"]]
          assert "Plan" in matchers

      def test_subagentstart_combined_matcher_absent(self):
          data = self._load()
          matchers = [e.get("matcher") for e in data["hooks"]["SubagentStart"]]
          assert "Explore|Plan" not in matchers, (
              "Old combined matcher must be gone"
          )
  ```

  Run: `make test-unit` — must FAIL (hooks.json still has combined entry)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/hooks.json`, replace the SubagentStart section:

  **Before:**
  ```json
  "SubagentStart": [
    {
      "matcher": "Explore|Plan",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/subagent-context.py\""
        }
      ]
    }
  ],
  ```

  **After:**
  ```json
  "SubagentStart": [
    {
      "matcher": "Explore",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/subagent-context.py\""
        }
      ]
    },
    {
      "matcher": "Plan",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/subagent-context.py\""
        }
      ]
    }
  ],
  ```

  Also update `_hook_output_protocol` comment for SubagentStart:

  **Before:**
  ```json
  "SubagentStart": "JSON {\"additionalContext\": \"...\"} printed to stdout for Explore|Plan agents",
  ```

  **After:**
  ```json
  "SubagentStart": "JSON {\"additionalContext\": \"...\"} printed to stdout for Explore and Plan agents (two separate matcher entries)",
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Remove the now-obsolete `test_subagentstart_matcher_is_explore_or_plan` test from `tests/unit/test_hooks_subagent_context.py` since it is superseded by the four new split-matcher tests.

  Run: `make test-unit` — still PASS

---

## Task 3: Final verification

<!-- depends_on: Task 1, Task 2 -->

**Acceptance Criteria:**
- Full test suite passes with no regressions
- `make lint` reports no violations

**Files:**
- No code changes — verification only

- [ ] **Step 1: Run full suite**

  ```bash
  make test-ci
  ```

  Expected: all unit tests pass, coverage gate holds, lint clean.

- [ ] **Step 2: Smoke check hooks**

  ```bash
  python3 hooks/subagent-context.py <<< '{"agentType": "Explore", "session_id": "smoke-test"}'
  ```

  Expected: no output (Now lane is empty in current repo state).

  ```bash
  python3 -c "import json; print(json.dumps({'agentType': 'Plan', 'session_id': 'smoke-plan'}))" | python3 hooks/subagent-context.py
  ```

  Expected: no output (Now lane empty).

- [ ] **Step 3: Confirm hooks.json is valid JSON**

  ```bash
  python3 -c "import json; json.load(open('hooks/hooks.json')); print('OK')"
  ```

  Expected: `OK`
