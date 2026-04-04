---
approved: true
approved_at: 2026-04-04
backlog: backlog/workflow-enforcement-escape-hatches.md
---

# Workflow Enforcement and Escape Hatches — Implementation Plan

**Goal:** Surface track-selection prompts when SDLC-adjacent activity is detected with no active track, and record bypass events in an append-only drift log.
**Architecture:** Extend `intent-sdlc.py` with a no-active-track check that calls a new `utils_roadmap.is_track_active()` helper; a new `utils_drift.py` module handles `.drift-log` append/read; three new lightweight commands (`/zie-hotfix`, `/zie-spike`, `/zie-chore`) give users compliant escape hatches; `/zie-status` gains a drift count row.
**Tech Stack:** Python 3.x (hooks), Markdown (commands), NDJSON (`.drift-log`)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils_roadmap.py` | Add `is_track_active(cwd) -> bool` helper |
| Create | `hooks/utils_drift.py` | Append drift event, read count, rolling 200-window trim |
| Modify | `hooks/intent-sdlc.py` | No-active-track check → emit track-selection suggestion |
| Modify | `commands/zie-status.md` | Show drift count row in status output |
| Create | `commands/zie-hotfix.md` | Lightweight hotfix command (describe → fix → ship) |
| Create | `commands/zie-spike.md` | Sandbox experiment command (no ROADMAP entry) |
| Create | `commands/zie-chore.md` | Maintenance task command (no spec required) |
| Create | `tests/unit/test_utils_drift.py` | Unit tests for utils_drift |
| Create | `tests/unit/test_is_track_active.py` | Unit tests for is_track_active |
| Modify | `tests/unit/test_hooks_intent_sdlc.py` | Tests for no-active-track suggestion |

---

## Task 1: Add `is_track_active()` to `utils_roadmap.py`

**Acceptance Criteria:**
- `is_track_active(cwd)` returns `True` when ROADMAP.md Now lane has at least one `[ ]` item
- `is_track_active(cwd)` returns `True` when `.drift-log` contains an open active-track marker (event without a `closed_at` field)
- `is_track_active(cwd)` returns `False` when Now lane is empty and no open drift marker exists
- `is_track_active(cwd)` returns `False` (does not raise) when ROADMAP.md is missing

**Files:**
- Modify: `hooks/utils_roadmap.py`
- Create: `tests/unit/test_is_track_active.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_is_track_active.py
  """Tests for utils_roadmap.is_track_active."""
  import json
  import os
  import sys
  from pathlib import Path

  sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
  from utils_roadmap import is_track_active


  def _make_cwd(tmp_path, roadmap_content=None, drift_lines=None):
      zf = tmp_path / "zie-framework"
      zf.mkdir(parents=True)
      if roadmap_content is not None:
          (zf / "ROADMAP.md").write_text(roadmap_content)
      if drift_lines is not None:
          (zf / ".drift-log").write_text("\n".join(drift_lines) + "\n")
      return tmp_path


  class TestIsTrackActive:
      def test_now_lane_open_item_returns_true(self, tmp_path):
          cwd = _make_cwd(tmp_path, "## Now\n- [ ] my-feature\n## Next\n")
          assert is_track_active(cwd) is True

      def test_now_lane_only_closed_items_returns_false(self, tmp_path):
          cwd = _make_cwd(tmp_path, "## Now\n- [x] my-feature\n## Next\n")
          assert is_track_active(cwd) is False

      def test_now_lane_empty_returns_false(self, tmp_path):
          cwd = _make_cwd(tmp_path, "## Now\n\n## Next\n")
          assert is_track_active(cwd) is False

      def test_missing_roadmap_returns_false(self, tmp_path):
          cwd = _make_cwd(tmp_path)  # no ROADMAP.md
          assert is_track_active(cwd) is False

      def test_open_drift_marker_returns_true(self, tmp_path):
          event = json.dumps({"track": "hotfix", "slug": "abc", "closed_at": None})
          cwd = _make_cwd(tmp_path, "## Now\n\n## Next\n", [event])
          assert is_track_active(cwd) is True

      def test_closed_drift_marker_returns_false(self, tmp_path):
          event = json.dumps({"track": "hotfix", "slug": "abc", "closed_at": "2026-04-04T00:00:00"})
          cwd = _make_cwd(tmp_path, "## Now\n\n## Next\n", [event])
          assert is_track_active(cwd) is False

      def test_unreadable_drift_log_does_not_raise(self, tmp_path):
          cwd = _make_cwd(tmp_path, "## Now\n\n## Next\n", ["not-json"])
          assert is_track_active(cwd) is False
  ```
  Run: `make test-unit` — must FAIL (ImportError: cannot import `is_track_active`)

- [ ] **Step 2: Implement (GREEN)**

  Add to the end of `hooks/utils_roadmap.py`:

  ```python
  def is_track_active(cwd) -> bool:
      """Return True if any active workflow track exists.

      Checks two sources:
      1. ROADMAP.md Now lane — any open [ ] item.
      2. zie-framework/.drift-log — any NDJSON line with closed_at == null.

      Returns False (never raises) when files are missing or unreadable.
      """
      cwd = Path(cwd)
      zf = cwd / "zie-framework"

      # Source 1: Now lane open item
      try:
          roadmap_path = zf / "ROADMAP.md"
          if roadmap_path.exists():
              content = roadmap_path.read_text()
              in_now = False
              for line in content.splitlines():
                  if line.startswith("##") and "now" in line.lower():
                      in_now = True
                      continue
                  if line.startswith("##") and in_now:
                      break
                  if in_now and re.search(r'-\s*\[\s*\]', line):
                      return True
      except Exception:
          pass

      # Source 2: open drift marker
      try:
          drift_path = zf / ".drift-log"
          if drift_path.exists():
              for raw in drift_path.read_text().splitlines():
                  raw = raw.strip()
                  if not raw:
                      continue
                  try:
                      event = json.loads(raw)
                      if event.get("closed_at") is None and "track" in event:
                          return True
                  except Exception:
                      continue
      except Exception:
          pass

      return False
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No structural changes needed. Confirm no import ordering issues (`json` is already imported in `utils_roadmap.py`).
  Run: `make test-unit` — still PASS

---

## Task 2: Create `utils_drift.py`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `append_drift_event(cwd, event_dict)` writes one NDJSON line to `zie-framework/.drift-log`
- Rolling window: trims file to last 200 lines after every write
- `read_drift_count(cwd)` returns integer count of all lines (events) in `.drift-log`
- `read_drift_count(cwd)` returns `0` when file is missing or unreadable
- `close_drift_track(cwd, slug)` sets `closed_at` to current ISO timestamp on matching open event

**Files:**
- Create: `hooks/utils_drift.py`
- Create: `tests/unit/test_utils_drift.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_utils_drift.py
  """Tests for hooks/utils_drift.py — drift log helpers."""
  import json
  import os
  import sys
  from pathlib import Path

  sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
  from utils_drift import append_drift_event, close_drift_track, read_drift_count


  def _zf(tmp_path):
      zf = tmp_path / "zie-framework"
      zf.mkdir(parents=True, exist_ok=True)
      return tmp_path


  class TestAppendDriftEvent:
      def test_creates_drift_log(self, tmp_path):
          cwd = _zf(tmp_path)
          append_drift_event(cwd, {"track": "hotfix", "slug": "abc"})
          log = tmp_path / "zie-framework" / ".drift-log"
          assert log.exists()

      def test_appends_ndjson_line(self, tmp_path):
          cwd = _zf(tmp_path)
          append_drift_event(cwd, {"track": "hotfix", "slug": "abc"})
          lines = (tmp_path / "zie-framework" / ".drift-log").read_text().splitlines()
          assert len(lines) == 1
          parsed = json.loads(lines[0])
          assert parsed["track"] == "hotfix"
          assert parsed["slug"] == "abc"

      def test_multiple_appends(self, tmp_path):
          cwd = _zf(tmp_path)
          for i in range(3):
              append_drift_event(cwd, {"track": "chore", "slug": f"task-{i}"})
          lines = (tmp_path / "zie-framework" / ".drift-log").read_text().splitlines()
          assert len(lines) == 3

      def test_rolling_trim_at_200(self, tmp_path):
          cwd = _zf(tmp_path)
          for i in range(205):
              append_drift_event(cwd, {"track": "chore", "slug": f"t-{i}"})
          lines = (tmp_path / "zie-framework" / ".drift-log").read_text().splitlines()
          assert len(lines) == 200

      def test_keeps_last_200_events(self, tmp_path):
          cwd = _zf(tmp_path)
          for i in range(205):
              append_drift_event(cwd, {"track": "chore", "slug": f"t-{i}"})
          lines = (tmp_path / "zie-framework" / ".drift-log").read_text().splitlines()
          last = json.loads(lines[-1])
          assert last["slug"] == "t-204"

      def test_no_crash_on_unwritable_parent(self, tmp_path):
          # Should not raise even if path is invalid
          append_drift_event(tmp_path / "nonexistent", {"track": "spike", "slug": "x"})


  class TestReadDriftCount:
      def test_missing_file_returns_zero(self, tmp_path):
          assert read_drift_count(tmp_path / "zie-framework") == 0

      def test_counts_lines(self, tmp_path):
          cwd = _zf(tmp_path)
          for i in range(5):
              append_drift_event(cwd, {"track": "chore", "slug": f"c-{i}"})
          assert read_drift_count(cwd) == 5

      def test_empty_file_returns_zero(self, tmp_path):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".drift-log").write_text("")
          assert read_drift_count(tmp_path) == 0


  class TestCloseDriftTrack:
      def test_closes_matching_open_event(self, tmp_path):
          cwd = _zf(tmp_path)
          append_drift_event(cwd, {"track": "hotfix", "slug": "my-fix", "closed_at": None})
          close_drift_track(cwd, "my-fix")
          log = tmp_path / "zie-framework" / ".drift-log"
          events = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
          closed = [e for e in events if e["slug"] == "my-fix"]
          assert len(closed) == 1
          assert closed[-1]["closed_at"] is not None

      def test_no_crash_on_missing_log(self, tmp_path):
          close_drift_track(tmp_path, "nonexistent")
  ```
  Run: `make test-unit` — must FAIL (ModuleNotFoundError: utils_drift)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/utils_drift.py
  #!/usr/bin/env python3
  """Drift log helpers — append, read count, close track."""
  import json
  import os
  import sys
  from datetime import datetime, timezone
  from pathlib import Path

  _MAX_EVENTS = 200


  def append_drift_event(cwd, event_dict: dict) -> None:
      """Append one NDJSON event to zie-framework/.drift-log.

      Trims log to last _MAX_EVENTS lines after write.
      Silently no-ops on any I/O error.
      """
      try:
          log_path = Path(cwd) / "zie-framework" / ".drift-log"
          line = json.dumps(event_dict, ensure_ascii=False)
          with open(log_path, "a", encoding="utf-8") as fh:
              fh.write(line + "\n")
          _trim_log(log_path)
      except Exception as e:
          print(f"[zie-framework] utils_drift.append_drift_event: {e}", file=sys.stderr)


  def read_drift_count(cwd) -> int:
      """Return number of events in .drift-log. Returns 0 on missing/unreadable file."""
      try:
          log_path = Path(cwd) / "zie-framework" / ".drift-log"
          if not log_path.exists():
              return 0
          lines = [l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
          return len(lines)
      except Exception:
          return 0


  def close_drift_track(cwd, slug: str) -> None:
      """Set closed_at on the last open event matching slug.

      Rewrites the log file with the updated event.
      Silently no-ops on any error.
      """
      try:
          log_path = Path(cwd) / "zie-framework" / ".drift-log"
          if not log_path.exists():
              return
          raw_lines = log_path.read_text(encoding="utf-8").splitlines()
          events = []
          for raw in raw_lines:
              raw = raw.strip()
              if not raw:
                  continue
              try:
                  events.append(json.loads(raw))
              except Exception:
                  events.append({"_raw": raw})

          # Close the last matching open event
          for i in range(len(events) - 1, -1, -1):
              ev = events[i]
              if ev.get("slug") == slug and ev.get("closed_at") is None:
                  events[i]["closed_at"] = datetime.now(timezone.utc).isoformat()
                  break

          new_content = "\n".join(
              e.get("_raw", json.dumps(e, ensure_ascii=False)) for e in events
          ) + "\n"
          log_path.write_text(new_content, encoding="utf-8")
      except Exception as e:
          print(f"[zie-framework] utils_drift.close_drift_track: {e}", file=sys.stderr)


  def _trim_log(log_path: Path) -> None:
      """Keep only the last _MAX_EVENTS non-empty lines in log_path."""
      try:
          lines = [l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
          if len(lines) > _MAX_EVENTS:
              log_path.write_text("\n".join(lines[-_MAX_EVENTS:]) + "\n", encoding="utf-8")
      except Exception:
          pass
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify `_trim_log` is called exactly once per append. Confirm `close_drift_track` handles `_raw` fallback records without corrupting other lines.
  Run: `make test-unit` — still PASS

---

## Task 3: Extend `intent-sdlc.py` with no-active-track check

<!-- depends_on: Task 1, Task 2 -->

**Acceptance Criteria:**
- When intent is `implement` or `fix` AND `is_track_active()` returns `False`, the hook emits a track-selection suggestion containing `/zie-hotfix`, `/zie-spike`, `/zie-chore`, and the standard pipeline path
- Suggestion fires on every matching prompt (no persistent suppression) until a track becomes active
- When `is_track_active()` returns `True`, the no-track suggestion is NOT emitted
- General chat (no SDLC keyword) does NOT trigger the suggestion
- Existing gate/intent logic is unaffected

**Files:**
- Modify: `hooks/intent-sdlc.py`
- Modify: `tests/unit/test_hooks_intent_sdlc.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append to `tests/unit/test_hooks_intent_sdlc.py`:

  ```python
  class TestNoActiveTrackSuggestion:
      """intent-sdlc emits escape-hatch prompt when no active track detected."""

      def _ctx(self, r):
          assert r.returncode == 0
          out = r.stdout.strip()
          assert out, f"no output; stderr={r.stderr}"
          return json.loads(out)["additionalContext"]

      def test_fix_intent_no_active_track_emits_track_options(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path, "## Now\n\n## Next\n")
          r = run_hook({"prompt": "there is a bug in the auth module"}, tmp_cwd=cwd)
          ctx = self._ctx(r)
          assert "/zie-hotfix" in ctx

      def test_implement_intent_no_active_track_emits_track_options(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path, "## Now\n\n## Next\n")
          r = run_hook({"prompt": "start coding this task now"}, tmp_cwd=cwd)
          ctx = self._ctx(r)
          assert "/zie-hotfix" in ctx

      def test_no_suggestion_when_now_lane_active(self, tmp_path):
          cwd = make_cwd_with_zf(
              tmp_path, "## Now\n- [ ] my-feature — implement\n\n## Next\n"
          )
          r = run_hook({"prompt": "there is a bug in the auth module"}, tmp_cwd=cwd)
          ctx = self._ctx(r)
          # Standard gate fires instead (no active-track prompt)
          assert "no active track" not in ctx.lower()

      def test_general_chat_no_suggestion(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path, "## Now\n\n## Next\n")
          r = run_hook({"prompt": "what is the weather in bangkok"}, tmp_cwd=cwd)
          # No SDLC keyword → empty output
          assert r.stdout.strip() == ""

      def test_spike_and_chore_options_present(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path, "## Now\n\n## Next\n")
          r = run_hook({"prompt": "implement this new feature"}, tmp_cwd=cwd)
          ctx = self._ctx(r)
          assert "/zie-spike" in ctx
          assert "/zie-chore" in ctx
  ```
  Run: `make test-unit` — must FAIL (new assertions not yet met)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/intent-sdlc.py`, after the existing imports add:
  ```python
  from utils_roadmap import is_track_active
  ```

  Then, inside the inner operations block, add a new check after the pipeline gate check:

  ```python
  # ── No-active-track check ─────────────────────────────────────────────────
  no_track_msg = None
  if gate_msg is None and best in ("implement", "fix"):
      if not is_track_active(cwd):
          no_track_msg = (
              "no active track — pick one: "
              "standard: /zie-backlog → /zie-spec → /zie-plan → /zie-implement | "
              "hotfix: /zie-hotfix | "
              "spike: /zie-spike | "
              "chore: /zie-chore"
          )
  ```

  Then include `no_track_msg` in the parts assembly (before positional guidance):
  ```python
  if gate_msg:
      parts.append(gate_msg)
  elif no_track_msg:
      parts.append(no_track_msg)
  elif intent_cmd:
      parts.append(f"intent:{best} → {intent_cmd}")
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm `no_track_msg` is only emitted when `gate_msg is None` and `best in ("implement", "fix")` — no other categories trigger it. Run `make lint`.
  Run: `make test-unit` — still PASS

---

## Task 4: Create `/zie-hotfix` command

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- Command file at `commands/zie-hotfix.md` exists
- Frontmatter has `description`, `argument-hint`, `allowed-tools`, `model`, `effort`
- Steps: derive slug from description or argument → write open drift marker → fix → ship → close drift marker
- Creates minimal ROADMAP backlog entry tagged `hotfix` in Done after ship
- Differs from `/zie-implement`: skips backlog/spec/plan stages
- `description` required when no `slug` argument provided

**Files:**
- Create: `commands/zie-hotfix.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_zie_hotfix_command.py
  """Structural tests for commands/zie-hotfix.md."""
  import os
  import re
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]
  CMD = REPO_ROOT / "commands" / "zie-hotfix.md"


  def test_file_exists():
      assert CMD.exists(), "commands/zie-hotfix.md must exist"


  def test_frontmatter_keys():
      text = CMD.read_text()
      assert "description:" in text
      assert "argument-hint:" in text
      assert "allowed-tools:" in text
      assert "model:" in text
      assert "effort:" in text


  def test_has_drift_log_write_step():
      text = CMD.read_text()
      assert ".drift-log" in text or "drift" in text.lower()


  def test_has_ship_step():
      text = CMD.read_text()
      assert "/zie-release" in text or "ship" in text.lower()


  def test_slug_derivation_described():
      text = CMD.read_text()
      assert "slug" in text.lower()
  ```
  Run: `make test-unit` — must FAIL (file does not exist)

- [ ] **Step 2: Implement (GREEN)**
  ```markdown
  ---
  description: Lightweight hotfix — describe → fix → ship in a single session, no spec/plan required.
  argument-hint: "[slug] <description>"
  allowed-tools: Read, Write, Edit, Bash, Glob, Grep
  model: sonnet
  effort: medium
  ---

  # /zie-hotfix — Hotfix Track

  Fast path for urgent fixes that skip backlog/spec/plan. Creates a minimal ROADMAP
  entry tagged `hotfix` in Done after ship.

  ## Arguments

  - `[slug]` — optional kebab-case identifier (auto-derived from description when omitted)
  - `<description>` — required when no slug provided; describes what is being fixed

  ## Steps

  1. **Resolve slug and description**
     - If argument matches `^[a-z][a-z0-9-]+$` → use as `slug`; prompt for description if not provided.
     - Otherwise → derive `slug` from first 5 words of description (kebab-case, max 40 chars).

  2. **Open drift marker**
     Append to `zie-framework/.drift-log`:
     ```json
     {"ts": "<ISO8601>", "track": "hotfix", "slug": "<slug>", "reason": "<description>", "closed_at": null}
     ```
     Use Python one-liner:
     ```bash
     python3 -c "
     import json, datetime, pathlib
     p = pathlib.Path('zie-framework/.drift-log')
     line = json.dumps({'ts': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'track': 'hotfix', 'slug': '<slug>', 'reason': '<description>', 'closed_at': None})
     with open(p, 'a') as f: f.write(line + '\n')
     "
     ```

  3. **Add Now lane entry to ROADMAP.md**
     Prepend to `## Now` section:
     ```
     - [ ] <slug> — hotfix: <description>
     ```

  4. **Diagnose and fix**
     - Reproduce the issue (run tests or describe observed behavior)
     - Implement minimal fix targeting root cause
     - Write or update regression test
     - Run `make test-unit` — must PASS

  5. **Ship**
     - Move ROADMAP Now entry from `[ ]` to `[x]`
     - Run `/zie-release` (standard release gate)
     - After successful release, append Done entry:
       ```
       - [x] <slug> — hotfix: <description> (v<VERSION>, <YYYY-MM-DD>)
       ```

  6. **Close drift marker**
     Update the open marker in `.drift-log` by setting `closed_at`:
     ```bash
     python3 -c "
     import json, datetime, pathlib
     p = pathlib.Path('zie-framework/.drift-log')
     lines = p.read_text().splitlines()
     out = []
     closed = False
     for raw in reversed(lines):
         if not closed:
             try:
                 ev = json.loads(raw)
                 if ev.get('slug') == '<slug>' and ev.get('closed_at') is None:
                     ev['closed_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                     raw = json.dumps(ev)
                     closed = True
             except Exception:
                 pass
         out.append(raw)
     p.write_text('\n'.join(reversed(out)) + '\n')
     "
     ```

  ## Notes

  - Never skip `make test-unit` before ship
  - Hotfix does not require a spec or plan — but the fix must be regression-tested
  - If the fix grows beyond 1 session, escalate to the full pipeline via `/zie-backlog`
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm frontmatter is valid YAML. Verify no trailing whitespace issues that could affect markdown lint.
  Run: `make test-unit` — still PASS

---

## Task 5: Create `/zie-spike` command

<!-- depends_on: Task 4 -->

**Acceptance Criteria:**
- Command file at `commands/zie-spike.md` exists
- Does NOT write to ROADMAP.md — output is a local `spike-<slug>/` directory only
- Frontmatter has required keys
- Steps describe creating the sandbox directory, experimenting, and cleaning up or promoting to backlog

**Files:**
- Create: `commands/zie-spike.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_zie_spike_command.py
  """Structural tests for commands/zie-spike.md."""
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]
  CMD = REPO_ROOT / "commands" / "zie-spike.md"


  def test_file_exists():
      assert CMD.exists(), "commands/zie-spike.md must exist"


  def test_frontmatter_keys():
      text = CMD.read_text()
      assert "description:" in text
      assert "allowed-tools:" in text


  def test_no_roadmap_write():
      text = CMD.read_text()
      # Must explicitly state it does NOT write to ROADMAP
      assert "ROADMAP" not in text.replace("no ROADMAP", "").replace("NOT", "").replace("does not", "") \
          or "no ROADMAP" in text.lower() or "not write" in text.lower() or "does not write" in text.lower()


  def test_spike_directory_mentioned():
      text = CMD.read_text()
      assert "spike-" in text
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  ```markdown
  ---
  description: Sandbox experiment track — explore an idea without committing to the backlog or ROADMAP.
  argument-hint: "<slug> [description]"
  allowed-tools: Read, Write, Edit, Bash, Glob, Grep
  model: sonnet
  effort: low
  ---

  # /zie-spike — Spike / Experiment Track

  Time-boxed sandbox for exploring ideas. Does NOT write to ROADMAP.md.
  Output lives in a local `spike-<slug>/` directory only.

  ## Arguments

  - `<slug>` — required kebab-case identifier for the spike
  - `[description]` — optional description of what is being explored

  ## Steps

  1. **Create sandbox directory**
     ```bash
     mkdir -p spike-<slug>
     ```
     Create `spike-<slug>/README.md` with:
     ```markdown
     # Spike: <slug>
     **Date:** <YYYY-MM-DD>
     **Goal:** <description>
     **Time-box:** 1 session

     ## Findings
     (fill in during spike)

     ## Outcome
     - [ ] Promote to backlog via /zie-backlog
     - [ ] Discard (delete this directory)
     ```

  2. **Experiment**
     Work freely in `spike-<slug>/`. No tests required during exploration.
     Keep notes in `spike-<slug>/README.md`.

  3. **Close the spike**
     Choose one outcome:
     - **Promote:** Run `/zie-backlog <slug>` with findings as motivation → delete `spike-<slug>/`
     - **Discard:** `rm -rf spike-<slug>/`

  ## Notes

  - Does NOT write to ROADMAP.md or `.drift-log`
  - No release required — spike output is local only
  - Time-box strictly to 1 session; escalate to full pipeline if scope grows
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Ensure the no-ROADMAP contract is unambiguous in the command text.
  Run: `make test-unit` — still PASS

---

## Task 6: Create `/zie-chore` command

<!-- depends_on: Task 5 -->

**Acceptance Criteria:**
- Command file at `commands/zie-chore.md` exists
- No spec required; creates minimal ROADMAP Done entry after completion
- Frontmatter has required keys
- Steps describe the maintenance task workflow

**Files:**
- Create: `commands/zie-chore.md`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_zie_chore_command.py
  """Structural tests for commands/zie-chore.md."""
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]
  CMD = REPO_ROOT / "commands" / "zie-chore.md"


  def test_file_exists():
      assert CMD.exists(), "commands/zie-chore.md must exist"


  def test_frontmatter_keys():
      text = CMD.read_text()
      assert "description:" in text
      assert "allowed-tools:" in text


  def test_no_spec_required():
      text = CMD.read_text()
      assert "no spec" in text.lower() or "spec required" not in text.lower()


  def test_done_entry_mentioned():
      text = CMD.read_text()
      assert "Done" in text or "done" in text.lower()
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  ```markdown
  ---
  description: Maintenance task track — dependency upgrades, refactors, config cleanup. No spec required.
  argument-hint: "<slug> <description>"
  allowed-tools: Read, Write, Edit, Bash, Glob, Grep
  model: haiku
  effort: low
  ---

  # /zie-chore — Maintenance / Chore Track

  Lightweight track for housekeeping tasks. No spec or plan required.
  Creates a minimal Done entry in ROADMAP after completion.

  ## Arguments

  - `<slug>` — required kebab-case identifier
  - `<description>` — required description of the maintenance task

  ## Steps

  1. **Add Now lane entry**
     Prepend to `## Now` in ROADMAP.md:
     ```
     - [ ] <slug> — chore: <description>
     ```

  2. **Do the work**
     Perform the maintenance task. Run `make test-unit` to verify nothing broke.

  3. **Complete**
     - Mark ROADMAP Now entry `[x]`
     - Append to `## Done`:
       ```
       - [x] <slug> — chore: <description> (<YYYY-MM-DD>)
       ```
     - Commit: `git add -p && git commit -m "chore: <description>"`

  ## Notes

  - No spec required — but if the task grows to >1 session, escalate to `/zie-backlog`
  - No release gate required for pure maintenance (no version bump)
  - If tests break, fix them before marking complete
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm tone/format matches existing commands (zie-fix.md style).
  Run: `make test-unit` — still PASS

---

## Task 7: Update `/zie-status` to show drift count

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `/zie-status` output includes a `Drift` row showing `N bypass events` from `.drift-log`
- Row shows `0 bypass events` when `.drift-log` is missing
- Row is part of the main status table

**Files:**
- Modify: `commands/zie-status.md`
- Create: `tests/unit/test_zie_status_drift.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_zie_status_drift.py
  """Tests that /zie-status spec references drift count display."""
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]
  CMD = REPO_ROOT / "commands" / "zie-status.md"


  def test_drift_row_in_status():
      text = CMD.read_text()
      assert "drift" in text.lower(), "zie-status must reference drift count"


  def test_drift_log_read_mentioned():
      text = CMD.read_text()
      assert ".drift-log" in text
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-status.md`, update Step 7 table to add a Drift row:

  Find the existing table in step 7:
  ```markdown
  | Brain | \<enabled\|disabled> |
  | Knowledge | \<✓ synced (date) \| ⚠ drift: /zie-resync \| ? no baseline> |
  ```

  Replace with:
  ```markdown
  | Brain | \<enabled\|disabled> |
  | Knowledge | \<✓ synced (date) \| ⚠ drift: /zie-resync \| ? no baseline> |
  | Drift | \<N bypass events (read from `zie-framework/.drift-log` line count; 0 if missing)> |
  ```

  Also add to Step 2 read-files list:
  ```markdown
  `zie-framework/.drift-log` — count non-empty lines for drift count; 0 if missing.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify the Drift row description matches the spec wording (`N bypass events`).
  Run: `make test-unit` — still PASS

---

## Task 8: Lint and integration smoke

<!-- depends_on: Task 3, Task 4, Task 5, Task 6, Task 7 -->

**Acceptance Criteria:**
- `make lint` passes with zero violations
- `make test-ci` passes with existing coverage gate met
- `utils_drift` module is importable from `hooks/`
- `is_track_active` is importable from `utils_roadmap`

**Files:**
- No new files; verify existing

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_escape_hatch_imports.py
  """Smoke test — all new modules and symbols importable."""
  import os
  import sys

  sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))


  def test_utils_drift_importable():
      import utils_drift  # noqa: F401
      assert hasattr(utils_drift, "append_drift_event")
      assert hasattr(utils_drift, "read_drift_count")
      assert hasattr(utils_drift, "close_drift_track")


  def test_is_track_active_importable():
      from utils_roadmap import is_track_active
      assert callable(is_track_active)
  ```
  Run: `make test-unit` — must FAIL if any module missing

- [ ] **Step 2: Implement (GREEN)**
  All modules already created by prior tasks. This task confirms they're present and lint-clean.
  ```bash
  make lint
  make test-ci
  ```
  Both must pass.

- [ ] **Step 3: Refactor**
  No changes. Final state: zero lint violations, all tests green, coverage gate met.
