---
approved: true
approved_at: 2026-04-11
backlog:
spec: zie-framework/specs/2026-04-11-brainstorming-skill-design.md
---

# Brainstorming Skill — Implementation Plan

> **Implementation:** Run via `claude --agent zie-framework:zie-implement-mode`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `zie-framework:brainstorm` skill that guides discovery (read project context → research → synthesize → discuss → write .zie/handoff.md) and wire brainstorm-intent detection into `intent-sdlc.py`.

**Architecture:** Two deliverables — (1) `skills/brainstorm/SKILL.md` is a 4-phase markdown skill file consumed by Claude as instructions; (2) `hooks/intent-sdlc.py` gains a new `"brainstorm"` entry in PATTERNS + SUGGESTIONS so the hook nudges users toward the skill when exploratory signals are detected. The brainstorm skill writes `.zie/handoff.md` and a `brainstorm-active` session flag so downstream hooks (conversation-capture spec) know not to double-write.

**Tech Stack:** Python 3.x (intent-sdlc.py hook), Markdown (SKILL.md), pytest (unit tests), `utils_io.project_tmp_path()` for session flag path.

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `skills/brainstorm/SKILL.md` | 4-phase brainstorm instructions for Claude |
| Modify | `hooks/intent-sdlc.py` | Add brainstorm PATTERNS + SUGGESTIONS entry |
| Create | `tests/unit/test_intent_sdlc.py` | Verify brainstorm signal matching in Thai + English |
| Create | `tests/unit/test_brainstorm_write_handoff.py` | Verify SKILL.md structure + handoff.md template |

---

### Task 1: Tests for brainstorm signal detection

**Files:**
- Create: `tests/unit/test_intent_sdlc.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for brainstorm intent detection in intent-sdlc hook (Area 0)."""
import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK_PATH = REPO_ROOT / "hooks" / "intent-sdlc.py"


def _source():
    return HOOK_PATH.read_text()


def _extract_dict_literal(source: str, var_name: str) -> dict:
    """Extract a module-level dict assignment by variable name using AST."""
    tree = ast.parse(source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    if isinstance(node.value, ast.Dict):
                        result = {}
                        for k, v in zip(node.value.keys, node.value.values):
                            if isinstance(k, ast.Constant):
                                if isinstance(v, ast.List):
                                    result[k.value] = [
                                        elt.value for elt in v.elts
                                        if isinstance(elt, ast.Constant)
                                    ]
                                elif isinstance(v, ast.Constant):
                                    result[k.value] = v.value
                        return result
    return {}


class TestBrainstormPatternInSource:
    def test_patterns_and_suggestions_are_dicts(self):
        """Guard: verify PATTERNS and SUGGESTIONS are extractable dicts before other tests run."""
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        suggestions = _extract_dict_literal(_source(), "SUGGESTIONS")
        assert isinstance(patterns, dict) and len(patterns) > 0, \
            "PATTERNS must be a non-empty dict extractable via AST"
        assert isinstance(suggestions, dict) and len(suggestions) > 0, \
            "SUGGESTIONS must be a non-empty dict extractable via AST"

    def test_brainstorm_key_in_patterns(self):
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        assert "brainstorm" in patterns, "PATTERNS must have 'brainstorm' key"

    def test_brainstorm_suggestion_is_skill(self):
        suggestions = _extract_dict_literal(_source(), "SUGGESTIONS")
        hint = suggestions.get("brainstorm", "")
        assert "brainstorm" in hint.lower(), (
            f"SUGGESTIONS['brainstorm'] must reference brainstorm skill, got: {hint!r}"
        )

    def test_brainstorm_patterns_not_empty(self):
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        assert len(patterns.get("brainstorm", [])) >= 4, (
            "brainstorm PATTERNS must have at least 4 signal strings"
        )


class TestBrainstormRegexMatching:
    """Extract brainstorm patterns and verify they match expected signals."""

    def _compiled(self):
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        compiled = []
        for p in patterns.get("brainstorm", []):
            try:
                compiled.append(re.compile(p, re.IGNORECASE))
            except re.error as e:
                pytest.fail(f"Invalid brainstorm regex pattern {p!r}: {e}")
        return compiled

    def test_matches_english_improve(self):
        compiled = self._compiled()
        assert any(p.search("improve") for p in compiled), "must match 'improve'"

    def test_matches_english_what_if(self):
        compiled = self._compiled()
        assert any(p.search("what if we added caching") for p in compiled), \
            "must match 'what if'"

    def test_matches_english_research(self):
        compiled = self._compiled()
        assert any(p.search("research this area") for p in compiled), \
            "must match 'research'"

    def test_matches_thai_should_add(self):
        compiled = self._compiled()
        assert any(p.search("น่าจะเพิ่ม") for p in compiled), \
            "must match Thai 'น่าจะเพิ่ม'"

    def test_does_not_match_clear_task(self):
        compiled = self._compiled()
        brainstorm_hits = sum(1 for p in compiled if p.search("fix bug in login"))
        assert brainstorm_hits < 2, (
            f"'fix bug in login' matched {brainstorm_hits} brainstorm signals — should be <2"
        )
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
make test-fast 2>&1 | tail -20
```
Expected: FAIL — `"brainstorm" not in PATTERNS`

---

### Task 2: Add brainstorm patterns to intent-sdlc.py
<!-- depends_on: T1 -->

**Files:**
- Modify: `hooks/intent-sdlc.py`

- [ ] **Step 0: Read the file and locate insertion points**

Read `hooks/intent-sdlc.py`. Find the `PATTERNS` dict — locate the `"spike"` entry (last entry in the dict). Find the `SUGGESTIONS` dict — locate the `"spike"` entry (last entry). Note the exact line numbers for both.

- [ ] **Step 1: Add brainstorm entry to PATTERNS dict**

In `hooks/intent-sdlc.py`, find the `"spike":` entry (the last key in PATTERNS). Insert the `"brainstorm"` entry immediately after the `"spike"` list closes (before the closing `}` of PATTERNS):

```python
    "brainstorm": [
        r"\bimprove\b", r"what if", r"\bresearch\b", r"deep dive",
        r"อยากให้มี", r"ควรจะ", r"น่าจะเพิ่ม", r"ปรับอะไรดี",
        r"คิดว่าขาดอะไร", r"\bexplore\b",
    ],
```

- [ ] **Step 2: Add brainstorm entry to SUGGESTIONS dict**

Find the `"spike":` entry (the last key in SUGGESTIONS). Insert immediately after it (before the closing `}` of SUGGESTIONS):

```python
    "brainstorm": "invoke zie-framework:brainstorm skill",
```

- [ ] **Step 3: Run tests to confirm they pass**

```bash
make test-fast 2>&1 | tail -20
```
Expected: PASS — all brainstorm signal tests green.

- [ ] **Step 4: Commit**

```bash
git add hooks/intent-sdlc.py tests/unit/test_intent_sdlc.py
git commit -m "feat(area-0): add brainstorm intent detection to intent-sdlc"
```

---

### Task 3: Tests for SKILL.md structure

**Files:**
- Create: `tests/unit/test_brainstorm_write_handoff.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for brainstorming SKILL.md structure and handoff.md template (Area 0)."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SKILL_PATH = REPO_ROOT / "skills" / "brainstorm" / "SKILL.md"


def _skill_text():
    return SKILL_PATH.read_text()


class TestBrainstormSkillExists:
    def test_skill_file_exists(self):
        assert SKILL_PATH.exists(), f"Expected skills/brainstorm/SKILL.md to exist"

    def test_skill_has_four_phases(self):
        text = _skill_text()
        for phase in ("Phase 1", "Phase 2", "Phase 3", "Phase 4"):
            assert phase in text, f"SKILL.md must contain '{phase}'"

    def test_skill_references_handoff_md(self):
        text = _skill_text()
        assert "handoff.md" in text, "SKILL.md must reference .zie/handoff.md"

    def test_skill_references_brainstorm_active_flag(self):
        text = _skill_text()
        assert "brainstorm-active" in text, (
            "SKILL.md must instruct writing brainstorm-active flag"
        )

    def test_skill_references_zie_dir(self):
        text = _skill_text()
        assert ".zie/" in text, "SKILL.md must reference the .zie/ directory"


class TestHandoffMdTemplate:
    def test_handoff_has_goals_section(self):
        text = _skill_text()
        assert "## Goals" in text, "SKILL.md handoff template must include ## Goals"

    def test_handoff_has_key_decisions_section(self):
        text = _skill_text()
        assert "## Key Decisions" in text, "SKILL.md handoff template must include ## Key Decisions"

    def test_handoff_has_next_step_section(self):
        text = _skill_text()
        assert "## Next Step" in text, "SKILL.md must include ## Next Step in handoff template"

    def test_handoff_has_frontmatter_fields(self):
        text = _skill_text()
        assert "captured_at:" in text, "SKILL.md handoff template must have captured_at: field"
        assert "source: brainstorm" in text, "SKILL.md handoff template must set source: brainstorm"

    def test_skill_references_project_tmp_path_in_phase_4(self):
        text = _skill_text()
        # Must appear in the Phase 4 section, not just anywhere in the file
        phase4_idx = text.find("Phase 4")
        assert phase4_idx != -1, "SKILL.md must contain a Phase 4 section"
        phase4_text = text[phase4_idx:]
        assert "project_tmp_path" in phase4_text, (
            "SKILL.md Phase 4 must reference project_tmp_path for the brainstorm-active flag"
        )


class TestFreshnessCheckInSkill:
    def test_skill_references_resync_on_stale(self):
        text = _skill_text()
        assert "/resync" in text, "SKILL.md Phase 1 must mention /resync when PROJECT.md is stale"

    def test_skill_references_tech_stack_detection(self):
        text = _skill_text()
        # Should mention detecting the tech stack for scoping research
        assert any(term in text for term in ("tech stack", "package.json", "pyproject.toml")), (
            "SKILL.md must reference tech stack detection (package.json/pyproject.toml)"
        )
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
make test-fast 2>&1 | tail -10
```
Expected: FAIL — `skills/brainstorm/SKILL.md does not exist`

---

### Task 4: Create skills/brainstorm/SKILL.md
<!-- depends_on: T3 -->

**Files:**
- Create: `skills/brainstorm/SKILL.md`

- [ ] **Step 1: Create the skills/brainstorm/ directory and SKILL.md**

Create `skills/brainstorm/SKILL.md` with the following content.

Note on handoff.md template sections: the brainstorm spec Phase 4 lists Goals, Key Decisions, Constraints, and Next Step. The template below also includes Open Questions and Context Refs — these are aligned with the companion conversation-capture spec's fuller handoff format and add value without conflicting.

```markdown
---
name: brainstorm
description: Discovery skill — read project context, research best practices, synthesize opportunities, discuss with Zie, write .zie/handoff.md ready for /sprint.
user-invocable: true
context: fork
agent: general-purpose
allowed-tools: Read, Grep, Glob, WebSearch, Bash, Write
argument-hint: "[topic]"
model: sonnet
effort: high
---

# zie-framework:brainstorm — Discovery & Handoff

Entry point skill for all new work. Run before /sprint or /backlog when you
want to understand the project state, research improvements, and form
requirements through discussion.

Runs 4 phases in sequence. Generic — works with any project.

---

## Phase 1 — Read Project Knowledge (not source files)

1. Discover knowledge artifacts generically:
   - `CLAUDE.md` (always present — read first)
   - `README.md` (if present)
   - `PROJECT.md` or `docs/` (if present)
   - `package.json` / `pyproject.toml` / `go.mod` — detect tech stack
   - `git log --oneline -20` — recent activity
2. Detect tech stack: language, framework, test runner — used to scope Phase 2.
3. If `zie-framework/` dir present (zie-framework project):
   - Read `zie-framework/ROADMAP.md`
   - Read `zie-framework/decisions/ADR-000-summary.md`
   - List `zie-framework/backlog/` items
4. Freshness check: compare `PROJECT.md` mtime vs latest commit mtime using
   `is_mtime_fresh(max_mtime=git_commit_mtime, written_at=project_md_mtime)`.
   - If stale → auto-run `/resync` before proceeding.
   - If no PROJECT.md → skip check, proceed with what's available.
5. Output: structured "project state snapshot" + detected tech stack.

---

## Phase 2 — Research (≤6 queries, scoped to project)

1. Read `zie-framework/decisions/ADR-000-summary.md` first — skip topics already
   decided in ADRs.
2. Derive search topics from Phase 1 gaps, **scoped to detected tech stack**.
   - E.g. "Python SDLC automation best practices" not "SDLC best practices"
3. Run targeted searches — 4 focus areas:
   - Similar tools/frameworks doing X better (scoped to stack)
   - Best practices for AI-assisted SDLC / Claude Code patterns for this stack
   - Solutions to specific gaps found in Phase 1
   - Emerging Claude Code ecosystem patterns relevant to this project type
4. Hard cap: ≤6 WebSearch calls total. Prefer depth over breadth.

---

## Phase 3 — Synthesize + Present + Confirm

Present findings in this format:

```
## Project Health
<gaps, pain points, strengths from Phase 1>

## Improvement Opportunities
1. [High impact] ...
2. [Medium impact] ...
3. [Quick win] ...

## Research Insights
- Pattern X from tool Y — applicable because Z (scoped to <detected stack>)
- Best practice W — currently missing in this project
```

After presenting, ask Zie:
> "Does this look right? Shall I continue to the discussion phase?"

Wait for confirmation before Phase 4.

---

## Phase 4 — Discuss → Narrow → Handoff

1. Discuss each opportunity with Zie — one at a time, ask priority + interest.
2. Narrow to 1-3 items to act on.
3. Create `$CWD/.zie/` dir if absent (mkdir -p).
4. Write `$CWD/.zie/handoff.md`:

```markdown
---
captured_at: YYYY-MM-DDTHH:MM:SSZ
feature: <name>
source: brainstorm
---

## Goals
- <bullet per goal>

## Key Decisions
- <bullet per decision made in discussion>

## Constraints
- <bullet per constraint>

## Open Questions
- <bullet per unresolved question>

## Context Refs
- <file paths or commands mentioned as relevant>

## Next Step
/sprint <feature-name>
```

5. Write `project_tmp_path("brainstorm-active", project)` flag file:
   - `project` = current working directory name (from `$CLAUDE_CWD` or `os.getcwd()`)
   - Path: `Path(tempfile.gettempdir()) / f"zie-{re.sub(r'[^a-zA-Z0-9]', '-', project)}-brainstorm-active"`
   - Content: `"active"` (plain text)
   - This signals `stop-capture.py` (conversation-capture spec) to skip its write.
6. Tell Zie: "Ready — run `/sprint <feature-name>` to start the pipeline."

---

## Error Handling

- Phase 1 artifact missing: skip gracefully, proceed with what's found.
- `/resync` unavailable: warn to stderr, continue with stale knowledge.
- Phase 2 search errors: skip failed query, continue with remaining budget.
- `.zie/` dir unwriteable: print handoff.md content inline instead, tell Zie
  to save manually.
- `brainstorm-active` flag write fails: log warning, continue — design-tracker
  may double-write (acceptable).
```

- [ ] **Step 2: Run tests to confirm they pass**

```bash
make test-fast 2>&1 | tail -10
```
Expected: PASS — all SKILL.md structure tests green.

- [ ] **Step 3: Commit**

```bash
git add skills/brainstorm/SKILL.md tests/unit/test_brainstorm_write_handoff.py
git commit -m "feat(area-0): brainstorm skill — 4-phase discovery + handoff.md"
```

---

### Task 5: Run full unit suite to confirm no regressions

- [ ] **Step 1: Run full unit test suite**

```bash
make test-unit 2>&1 | tail -20
```
Expected: all tests pass, no regressions in existing intent-sdlc tests.

- [ ] **Step 2: Verify clean working tree**

```bash
git status
```
Expected: clean working tree (all files committed in earlier tasks).
