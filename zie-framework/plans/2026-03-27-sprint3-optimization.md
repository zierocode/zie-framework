---
approved: true
approved_at: 2026-03-27
backlog: zie-framework/specs/2026-03-27-sprint3-optimization-design.md
---

# Sprint 3: Framework Optimization — Implementation Plan

**Goal:** Deliver 12 targeted optimizations across effort routing, token efficiency, parallelism, archive strategy, SDLC guards, and standards compliance as v1.11.0.
**Architecture:** Three independent parallel tracks (A/B/C) across hooks, commands, skills, tests, and CI — no shared state, no migration risk. All changes are additive or drop-in replacements within existing files. Track B introduces the `zie-framework/archive/` directory tree and a new `utils.py` helper; Track C closes standards gaps in tests and CI.
**Tech Stack:** Python 3.x, pytest, Markdown

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Edit | `skills/write-plan/SKILL.md` | A1 — change `effort: high` → `effort: medium` |
| Edit | `skills/docs-sync-check/SKILL.md` | A1 — verify `effort: low` (already correct, note) |
| Edit (verify) | `hooks/intent-sdlc.py` | A3 — confirm COMPILED_PATTERNS at module level; add regression test |
| Edit | `hooks/session-resume.py` | C1a — fix any remaining `[zie]` log prefixes → `[zie-framework] session-resume:` |
| Edit (verify) | `hooks/task-completed-gate.py` | C1b — confirm TEST_INDICATORS from config; add unit test for config path |
| Edit | `hooks/utils.py` | B3 — add `parse_roadmap_ready()` helper |
| Edit | `commands/zie-implement.md` | A2 + B3 — token trim intro + pre-flight Ready lane guard |
| Edit | `commands/zie-release.md` | A2 + B2 — token trim intro + add archive step after merge |
| Edit | `commands/zie-retro.md` | A2 + B1 — token trim intro + parallel Agent calls for ADR+ROADMAP |
| Edit | `.github/workflows/ci.yml` | C2b — `make test` → `make test-unit` |
| Edit | `CLAUDE.md` | C2c — note integration tests require live Claude session |
| Edit | `tests/unit/test_versioning_gate.py` | C2a — verify VERSION==plugin.json assertion exists and passes |
| Create | `tests/unit/test_utils_ready.py` | B3 — unit test for parse_roadmap_ready() |
| Create | `tests/unit/test_task_completed_gate_config.py` | C1b — unit test for TEST_INDICATORS from config |
| Create | `tests/unit/test_intent_sdlc_regex.py` | A3 — regression test for module-level COMPILED_PATTERNS |
| Create | `zie-framework/archive/backlog/.gitkeep` | B2 — archive directory for completed backlog items |
| Create | `zie-framework/archive/specs/.gitkeep` | B2 — archive directory for shipped specs |
| Create | `zie-framework/archive/plans/.gitkeep` | B2 — archive directory for shipped plans |
| Edit | `Makefile` | B2 — add `make archive` target |
| Create | `zie-framework/decisions/ADR-022-effort-routing-strategy.md` | A1b — document effort routing rationale |
| Create | `zie-framework/decisions/ADR-023-archive-strategy.md` | B2 — document archive strategy |

---

## Batch 1 — Independent (Tasks 1–4)

## Task 1: A1 — Effort Frontmatter Audit
<!-- depends_on: none -->

**What:** Audit `effort:` fields in all `skills/*/SKILL.md` and `commands/*.md` files. Update `write-plan` from `high` → `medium`. All other skills and commands are already correct; document findings.

**Acceptance Criteria:**
- `grep -r "effort: high" skills/ commands/` returns only `skills/spec-design/SKILL.md` (full dialogue justifies high)
- `write-plan/SKILL.md` reads `effort: medium`
- No other skill or command effort values changed
- Note: `zie-implement` command was already `effort: medium` — verified, no change needed

**RED — write failing test:**

```python
# tests/unit/test_effort_audit.py
from pathlib import Path
import pytest

SKILLS_DIR = Path(__file__).parents[2] / "skills"
ALLOWED_HIGH = {"spec-design"}  # only skill justified at high


def test_no_unexpected_high_effort_skills():
    """Only spec-design may have effort: high."""
    violations = []
    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        text = skill_md.read_text()
        lines = text.splitlines()
        for line in lines:
            if line.strip().startswith("effort:") and "high" in line:
                skill_name = skill_md.parent.name
                if skill_name not in ALLOWED_HIGH:
                    violations.append(f"{skill_md}: {line.strip()}")
    assert not violations, f"Unexpected high-effort skills: {violations}"
```

Run: `pytest tests/unit/test_effort_audit.py` → FAIL (write-plan is `high`)

**GREEN — make it pass:**

Edit `/Users/zie/Code/zie-framework/skills/write-plan/SKILL.md`:
```
effort: high
```
→
```
effort: medium
```

Run: `pytest tests/unit/test_effort_audit.py` → PASS

**REFACTOR:** No cleanup needed. Test is clean.

---

## Task 2: A3 — Intent-SDLC Regex Caching Verification
<!-- depends_on: none -->

**What:** Verify `COMPILED_PATTERNS` is already at module level in `hooks/intent-sdlc.py` (it is, lines 75–78). Add a regression test to lock this in and prevent future regressions.

**Current state (verified):** `intent-sdlc.py` lines 75–78 already define:
```python
COMPILED_PATTERNS = {
    cat: [re.compile(p) for p in pats]
    for cat, pats in PATTERNS.items()
}
```
No code change needed in the hook — only the regression test.

**Acceptance Criteria:**
- `grep "re.compile" hooks/intent-sdlc.py` shows patterns at module level, not inside any function
- Regression test passes and would fail if COMPILED_PATTERNS were moved inside a function

**RED — write failing test:**

```python
# tests/unit/test_intent_sdlc_regex.py
import ast
from pathlib import Path

HOOK_PATH = Path(__file__).parents[2] / "hooks" / "intent-sdlc.py"


def _get_module_level_names(tree: ast.Module) -> set:
    """Return names assigned at module level (direct children of Module)."""
    names = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def _has_compile_inside_function(tree: ast.Module) -> bool:
    """Return True if re.compile() appears inside any function definition."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Attribute) and func.attr == "compile":
                        return True
                    if isinstance(func, ast.Name) and func.id == "compile":
                        return True
    return False


def test_compiled_patterns_at_module_level():
    """COMPILED_PATTERNS must be a module-level assignment."""
    source = HOOK_PATH.read_text()
    tree = ast.parse(source)
    module_names = _get_module_level_names(tree)
    assert "COMPILED_PATTERNS" in module_names, (
        "COMPILED_PATTERNS must be defined at module level, not inside a function"
    )


def test_no_re_compile_inside_functions():
    """re.compile must not be called inside any function (patterns compiled once)."""
    source = HOOK_PATH.read_text()
    tree = ast.parse(source)
    assert not _has_compile_inside_function(tree), (
        "re.compile() found inside a function — move pattern compilation to module level"
    )
```

Run: `pytest tests/unit/test_intent_sdlc_regex.py` → should PASS immediately (already correct). If it fails, the hook regressed.

**GREEN:** No hook changes needed — test verifies existing correct state.

**REFACTOR:** None.

---

## Task 3: C1a — Session-Resume Log Prefix Verification
<!-- depends_on: none -->

**What:** The spec targets `[zie] warning:` → `[zie-framework] session-resume:` at line 26 of `session-resume.py`. Current file uses `[zie-framework]` throughout. Add a regression test to lock in the correct prefix.

**Current state (verified):** All log lines in `session-resume.py` already use `[zie-framework]`. No `[zie]` bare prefix found.

**Acceptance Criteria:**
- `grep "\[zie\]" hooks/` returns no matches
- Regression test passes

**RED — write failing test:**

```python
# tests/unit/test_session_resume_prefix.py
from pathlib import Path
import re

HOOKS_DIR = Path(__file__).parents[2] / "hooks"


def test_no_bare_zie_prefix_in_hooks():
    """No hook file may use bare [zie] log prefix — must be [zie-framework]."""
    violations = []
    pattern = re.compile(r'\[zie\]')  # bare [zie] only, not [zie-framework]
    for hook_py in HOOKS_DIR.glob("*.py"):
        text = hook_py.read_text()
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{hook_py.name}:{lineno}: {line.strip()}")
    assert not violations, (
        f"Bare [zie] log prefix found (use [zie-framework] instead):\n"
        + "\n".join(violations)
    )
```

Run: `pytest tests/unit/test_session_resume_prefix.py` → PASS (already correct). Test locks in the invariant.

**GREEN:** No hook changes needed.

**REFACTOR:** None.

---

## Task 4: C1b — Task-Completed-Gate TEST_INDICATORS Config Verification
<!-- depends_on: none -->

**What:** The spec requires `TEST_INDICATORS` to be read from `load_config(cwd).get("test_indicators", DEFAULT_INDICATORS)`. This is already implemented in `task-completed-gate.py` via `_load_test_indicators()` (lines 27–39). Add a unit test to verify the config path and the empty-list fallback behavior.

**Current state (verified):** `_load_test_indicators()` already reads from config with fallback to `_DEFAULT_TEST_INDICATORS`. Empty config → returns `_DEFAULT_TEST_INDICATORS`.

**Acceptance Criteria:**
- Unit test covers: (a) config key absent → default used, (b) config has `test_indicators` → custom value used, (c) empty string in config → default used (never empty tuple)
- `make test-unit` green

**RED — write failing test:**

```python
# tests/unit/test_task_completed_gate_config.py
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Allow importing hook module
sys.path.insert(0, str(Path(__file__).parents[2] / "hooks"))
from task_completed_gate import _load_test_indicators, _DEFAULT_TEST_INDICATORS  # noqa: E402


def test_default_when_config_missing(tmp_path):
    """When .config is absent, returns _DEFAULT_TEST_INDICATORS."""
    cwd = tmp_path
    result = _load_test_indicators(cwd)
    assert result == _DEFAULT_TEST_INDICATORS


def test_custom_indicators_from_config(tmp_path):
    """When config has test_indicators, returns parsed tuple."""
    zf = tmp_path / "zie-framework"
    zf.mkdir()
    config = {"test_indicators": "test_, _spec., .check."}
    (zf / ".config").write_text(json.dumps(config))
    result = _load_test_indicators(tmp_path)
    assert result == ("test_", "_spec.", ".check.")


def test_empty_string_in_config_falls_back_to_default(tmp_path):
    """Empty string in config must fall back to default — never empty tuple."""
    zf = tmp_path / "zie-framework"
    zf.mkdir()
    config = {"test_indicators": ""}
    (zf / ".config").write_text(json.dumps(config))
    result = _load_test_indicators(tmp_path)
    assert result == _DEFAULT_TEST_INDICATORS
    assert len(result) > 0, "Gate must never have zero indicators"


def test_whitespace_only_entries_stripped(tmp_path):
    """Whitespace-only entries after split are excluded."""
    zf = tmp_path / "zie-framework"
    zf.mkdir()
    config = {"test_indicators": "test_, , _test."}
    (zf / ".config").write_text(json.dumps(config))
    result = _load_test_indicators(tmp_path)
    assert "" not in result
    assert "test_" in result
    assert "_test." in result
```

Note: the hook file is `task-completed-gate.py` (hyphenated). Import it as a module by path:

```python
# Alternative import approach for hyphenated filename:
import importlib.util
spec = importlib.util.spec_from_file_location(
    "task_completed_gate",
    Path(__file__).parents[2] / "hooks" / "task-completed-gate.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
_load_test_indicators = mod._load_test_indicators
_DEFAULT_TEST_INDICATORS = mod._DEFAULT_TEST_INDICATORS
```

Run: `pytest tests/unit/test_task_completed_gate_config.py` → PASS (already correct).

**GREEN:** No hook changes needed — existing implementation passes all cases.

**REFACTOR:** None.

---

## Batch 2 — Independent (Tasks 5–8)

## Task 5: A2 — Token Trim zie-implement, zie-release, zie-retro
<!-- depends_on: none -->

**What:** Remove redundant intro sentences in the three command files that restate the frontmatter `description:`. Target ≥10% word count reduction in each. Do NOT remove workflow steps or acceptance criteria.

**Current word counts:**
- `zie-implement.md`: 716 words → target ≤644 words (≥72 words removed)
- `zie-release.md`: 1163 words → target ≤1047 words (≥116 words removed)
- `zie-retro.md`: 1051 words → target ≤946 words (≥105 words removed)

**Acceptance Criteria:**
- Word count of each file reduced by ≥10%
- All workflow steps intact
- No acceptance criteria removed

**RED — write failing test:**

```python
# tests/unit/test_token_trim.py
from pathlib import Path
import subprocess

COMMANDS_DIR = Path(__file__).parents[2] / "commands"

# Word count targets (≤ these values after trim)
TARGETS = {
    "zie-implement.md": 644,
    "zie-release.md": 1047,
    "zie-retro.md": 946,
}


def _word_count(path: Path) -> int:
    text = path.read_text()
    return len(text.split())


def test_zie_implement_word_count():
    count = _word_count(COMMANDS_DIR / "zie-implement.md")
    assert count <= TARGETS["zie-implement.md"], (
        f"zie-implement.md has {count} words, target ≤{TARGETS['zie-implement.md']}"
    )


def test_zie_release_word_count():
    count = _word_count(COMMANDS_DIR / "zie-release.md")
    assert count <= TARGETS["zie-release.md"], (
        f"zie-release.md has {count} words, target ≤{TARGETS['zie-release.md']}"
    )


def test_zie_retro_word_count():
    count = _word_count(COMMANDS_DIR / "zie-retro.md")
    assert count <= TARGETS["zie-retro.md"], (
        f"zie-retro.md has {count} words, target ≤{TARGETS['zie-retro.md']}"
    )
```

Run: `pytest tests/unit/test_token_trim.py` → FAIL (all three over target)

**GREEN — trim the files:**

**zie-implement.md** — remove the redundant sentence immediately after the heading (the frontmatter `description` already says the same thing).

Remove this exact line:
```
Implement the active feature using Test-Driven Development.
```
Result: heading is followed directly by `## ตรวจสอบก่อนเริ่ม` (with blank line between).

**zie-release.md** — remove the redundant intro paragraph immediately after the heading.

Remove these exact lines:
```
Full automated release gate. Runs all tests, verifies, bumps version, merges
dev→main, tags, and updates ROADMAP. Nothing ships without passing every gate.
```
Result: heading is followed directly by `## ตรวจสอบก่อนเริ่ม` (with blank line between).

**zie-retro.md** — remove the redundant intro paragraph immediately after the heading.

Remove these exact lines:
```
Post-release or end-of-session retrospective. Documents what happened, extracts
architectural decisions as ADRs, updates ROADMAP, and stores learnings in the
brain.
```
Result: heading is followed directly by `## ตรวจสอบก่อนเริ่ม` (with blank line between).

If removing intro paragraphs alone does not achieve ≥10% reduction in all three files, also remove redundant `## ขั้นตอนถัดไป` / `## Notes` sentences that repeat information stated elsewhere in the same file.

Run: `pytest tests/unit/test_token_trim.py` → PASS

**REFACTOR:** Verify all steps still present. Run `make test-unit` → green.

---

## Task 6: B3 — utils.py `parse_roadmap_ready()` Helper
<!-- depends_on: none -->

**What:** Add `parse_roadmap_ready(roadmap_path, warn_on_empty: bool = False) -> list` to `hooks/utils.py`. Mirrors `parse_roadmap_now()` exactly, delegating to `parse_roadmap_section()`.

**Acceptance Criteria:**
- `parse_roadmap_ready()` returns items from `## Ready` section
- Empty/missing file → returns `[]`
- `warn_on_empty=True` + empty section → prints warning to stderr
- Imported successfully from `utils`

**RED — write failing test:**

```python
# tests/unit/test_utils_ready.py
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "hooks"))
from utils import parse_roadmap_ready  # noqa: E402


ROADMAP_WITH_READY = """
## Now
- [ ] active task

## Ready
- approved-plan-slug

## Next
- future item
"""

ROADMAP_WITHOUT_READY = """
## Now
- [ ] active task

## Next
- future item
"""

ROADMAP_EMPTY_READY = """
## Ready

## Next
- future item
"""


def test_parse_roadmap_ready_returns_items(tmp_path):
    """Returns list of items from ## Ready section."""
    f = tmp_path / "ROADMAP.md"
    f.write_text(ROADMAP_WITH_READY)
    result = parse_roadmap_ready(f)
    assert result == ["approved-plan-slug"]


def test_parse_roadmap_ready_missing_section(tmp_path):
    """Returns [] when ## Ready section absent."""
    f = tmp_path / "ROADMAP.md"
    f.write_text(ROADMAP_WITHOUT_READY)
    result = parse_roadmap_ready(f)
    assert result == []


def test_parse_roadmap_ready_empty_section(tmp_path):
    """Returns [] when ## Ready section is present but empty."""
    f = tmp_path / "ROADMAP.md"
    f.write_text(ROADMAP_EMPTY_READY)
    result = parse_roadmap_ready(f)
    assert result == []


def test_parse_roadmap_ready_missing_file(tmp_path):
    """Returns [] when file does not exist."""
    result = parse_roadmap_ready(tmp_path / "nonexistent.md")
    assert result == []


def test_parse_roadmap_ready_warn_on_empty(tmp_path, capsys):
    """warn_on_empty=True prints warning to stderr when section empty."""
    f = tmp_path / "ROADMAP.md"
    f.write_text(ROADMAP_EMPTY_READY)
    parse_roadmap_ready(f, warn_on_empty=True)
    captured = capsys.readouterr()
    assert "[zie-framework]" in captured.err
    assert "Ready" in captured.err
```

Run: `pytest tests/unit/test_utils_ready.py` → FAIL (`parse_roadmap_ready` not found)

**GREEN — add to utils.py:**

Add immediately after the `parse_roadmap_now()` function definition:

```python
def parse_roadmap_ready(roadmap_path, warn_on_empty: bool = False) -> list:
    """Extract cleaned items from the ## Ready section of ROADMAP.md.

    Returns [] if the file is missing, the Ready section is absent, or it is empty.
    Accepts Path or str.

    If warn_on_empty=True and the file exists but the Ready section is absent
    or empty, prints a warning to stderr.
    """
    path = Path(roadmap_path)
    items = parse_roadmap_section(path, "ready")
    if warn_on_empty and path.exists() and not items:
        print(
            "[zie-framework] WARNING: ROADMAP.md Ready section is empty or missing",
            file=sys.stderr,
        )
    return items
```

Run: `pytest tests/unit/test_utils_ready.py` → PASS

**REFACTOR:** None. Pattern mirrors `parse_roadmap_now()` exactly.

---

## Task 7: C2a — test_versioning_gate.py VERSION==plugin.json Assertion
<!-- depends_on: none -->

**What:** Verify the `test_version_files_match` test already exists in `test_versioning_gate.py` (it does, lines 36–43). Ensure it runs cleanly, is not skipped, and the assertion logic is correct.

**Current state (verified):** `test_version_files_match` at lines 36–43 already asserts:
```python
assert version_file == plugin_json["version"]
```

**Acceptance Criteria:**
- `pytest tests/unit/test_versioning_gate.py::TestVersioningGate::test_version_files_match` exits 0
- If VERSION ≠ plugin.json version, test fails with clear message referencing `make bump`

**RED — run existing test:**

```bash
pytest tests/unit/test_versioning_gate.py::TestVersioningGate::test_version_files_match -v
```

Expected: PASS (current repo has VERSION == plugin.json). If FAIL, run `make sync-version` to fix.

**GREEN — no code change needed.** Test is already correct.

**REFACTOR:** Add `test_version_files_match` explicitly to CI run scope check (see Task 8).

---

## Task 8: C2b+c — CI `make test-unit` + CLAUDE.md Integration Test Note
<!-- depends_on: none -->

**What:** Change `.github/workflows/ci.yml` to run `make test-unit` instead of `make test`. Add a note to `CLAUDE.md` that integration tests require a live Claude session.

**Acceptance Criteria:**
- `ci.yml` runs `make test-unit` (not `make test`)
- `CLAUDE.md` under Development Commands includes: "Integration tests require live Claude session — run `make test-int` separately"
- Existing branch filter (push/PR to main and dev) preserved

**RED — write failing test:**

```python
# tests/unit/test_ci_config.py
from pathlib import Path
import re

CI_YML = Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"
CLAUDE_MD = Path(__file__).parents[2] / "CLAUDE.md"


def test_ci_runs_make_test_unit():
    """CI must run make test-unit, not make test (integration tests need live Claude)."""
    text = CI_YML.read_text()
    assert "make test-unit" in text, "ci.yml must run 'make test-unit'"
    assert re.search(r'^\s*run:\s*make test\s*$', text, re.MULTILINE) is None, (
        "ci.yml must not run bare 'make test' (includes integration tests)"
    )


def test_ci_preserves_branch_filter():
    """CI branch filter must include both main and dev."""
    text = CI_YML.read_text()
    assert "main" in text
    assert "dev" in text


def test_claude_md_documents_integration_test_exclusion():
    """CLAUDE.md must note that integration tests require live Claude session."""
    text = CLAUDE_MD.read_text()
    assert "make test-int" in text
    assert "live" in text.lower() or "session" in text.lower(), (
        "CLAUDE.md must explain why make test-int is excluded from CI"
    )
```

Run: `pytest tests/unit/test_ci_config.py` → FAIL (`make test` in ci.yml, note missing from CLAUDE.md)

**GREEN — edit the files:**

**`.github/workflows/ci.yml`** — change:
```yaml
      - name: Run tests
        run: make test
```
→
```yaml
      - name: Run tests
        run: make test-unit
```

**`CLAUDE.md`** — under `## Development Commands`, add after `make test`:
```
make test-int         # run integration tests (require live Claude session — not in CI)
```
Or append a note after the `make test` line:

```
> Integration tests (`make test-int`) require a live Claude session — run separately, not in CI.
```

Run: `pytest tests/unit/test_ci_config.py` → PASS

**REFACTOR:** None.

---

## Batch 3 — Some depend on Batch 2 (Tasks 9–12)

## Task 9: B1 — zie-retro.md Parallel Agent Calls for ADR + ROADMAP
<!-- depends_on: none -->

**What:** Update `zie-retro.md` to launch ADR write and ROADMAP update as parallel Agent calls (both `run_in_background=true`). Brain store only after both complete. Markdown change only — no Python.

**Current state:** The current `### Invoke Background Agents (concurrent)` section already launches two agents in parallel (retro-format and docs-sync-check). The ADR write and ROADMAP update steps (`### บันทึก ADRs` and `### อัปเดต ROADMAP`) are sequential prose steps — make them explicitly parallelizable with agent delegation when applicable.

**Acceptance Criteria:**
- `zie-retro.md` has explicit parallel Agent invocation block for ADR write + ROADMAP update
- Brain store step appears after both agents complete (depends on both)
- Failure mode documented: if either agent fails → brain store skipped

**RED — write failing test:**

```python
# tests/unit/test_retro_parallel.py
from pathlib import Path

RETRO_MD = Path(__file__).parents[2] / "commands" / "zie-retro.md"


def test_retro_has_parallel_agent_note():
    """zie-retro.md must document parallel ADR + ROADMAP agent execution."""
    text = RETRO_MD.read_text()
    assert "run_in_background" in text, (
        "zie-retro.md must use run_in_background for parallel agents"
    )
    assert "simultaneous" in text.lower() or "parallel" in text.lower() or "concurrent" in text.lower(), (
        "zie-retro.md must note parallel/concurrent execution"
    )


def test_retro_brain_store_after_agents():
    """Brain store section must appear after parallel agent section."""
    text = RETRO_MD.read_text()
    agent_pos = text.find("run_in_background")
    brain_pos = text.find("brain")
    assert agent_pos < brain_pos, (
        "Brain store must appear after parallel agent invocation"
    )


def test_retro_failure_mode_documented():
    """Failure handling for parallel agents must be documented."""
    text = RETRO_MD.read_text()
    assert "fail" in text.lower() or "fallback" in text.lower(), (
        "zie-retro.md must document failure handling for parallel agents"
    )
```

Run: `pytest tests/unit/test_retro_parallel.py` → may partially PASS (parallel agents exist for retro-format/docs-sync-check but not ADR+ROADMAP explicitly)

**GREEN — update zie-retro.md (markdown edit only, no Python):**

This is a markdown command file change. The intent is to REPLACE the sequential `### บันทึก ADRs` step and the sequential `### อัปเดต ROADMAP` step with two parallel Agent calls.

Find the `### บันทึก ADRs` section heading in `commands/zie-retro.md` and replace the entire sequential write-ADR prose block AND the `### อัปเดต ROADMAP` section heading + prose with:

```markdown
### บันทึก ADRs + อัปเดต ROADMAP (parallel)

Launch both as parallel Agent calls — two Agent tool uses in one message. ADR files and ROADMAP.md are different paths, no write conflict:

1. `Agent(subagent_type="zie-framework:retro-format", run_in_background=True, prompt="Write ADRs for decisions: {decisions_json}. Next ADR number: {next_adr_n}. Write each to zie-framework/decisions/ADR-<NNN>-<slug>.md")` — creates ADR files in `zie-framework/decisions/`
2. `Agent(subagent_type="zie-framework:retro-format", run_in_background=True, prompt="Update ROADMAP Done section for shipped items: {shipped_items}. File: zie-framework/ROADMAP.md")` — updates Done lane in `zie-framework/ROADMAP.md`

Await both. Then proceed to brain store.

**Failure mode:** If either Agent call fails → skip brain store entirely. Do not retry.

<!-- fallback: if Agent tool unavailable, run ADR write and ROADMAP update inline (blocking, sequential) -->
```

Run: `pytest tests/unit/test_retro_parallel.py` → PASS

**REFACTOR:** Verify existing parallel section (retro-format + docs-sync-check in `### Invoke Background Agents`) is not disrupted — this new parallel block comes later in the file.

---

## Task 10: B2 — Archive Directories + `make archive` + zie-release.md Archive Step
<!-- depends_on: none -->

**What:** Create `zie-framework/archive/` directory tree. Add `make archive` target to `Makefile`. Add archive step to `zie-release.md` post-merge.

**Acceptance Criteria:**
- `zie-framework/archive/backlog/`, `archive/specs/`, `archive/plans/` exist (with `.gitkeep`)
- `make archive` target moves Done-lane items + linked specs/plans to archive by slug matching
- `zie-release.md` references archive step after merge
- Archive dirs excluded from reviewer context bundles (read from active dirs only)

**RED — write failing test:**

```python
# tests/unit/test_archive_structure.py
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
ZF = REPO_ROOT / "zie-framework"
MAKEFILE = REPO_ROOT / "Makefile"
RELEASE_CMD = REPO_ROOT / "commands" / "zie-release.md"


def test_archive_dirs_exist():
    """Archive subdirectories must exist."""
    assert (ZF / "archive" / "backlog").exists(), "archive/backlog/ missing"
    assert (ZF / "archive" / "specs").exists(), "archive/specs/ missing"
    assert (ZF / "archive" / "plans").exists(), "archive/plans/ missing"


def test_makefile_has_archive_target():
    """Makefile must have an 'archive' target."""
    text = MAKEFILE.read_text()
    assert "archive:" in text or "archive :" in text, (
        "Makefile must define an 'archive' target"
    )


def test_release_md_references_archive():
    """zie-release.md must reference the archive step after merge."""
    text = RELEASE_CMD.read_text()
    assert "archive" in text.lower(), (
        "zie-release.md must reference archive step"
    )
    assert "make archive" in text, (
        "zie-release.md must include 'make archive' command"
    )
```

Run: `pytest tests/unit/test_archive_structure.py` → FAIL (dirs missing, no Makefile target)

**GREEN — create files and edit Makefile + release command:**

**Create directories:**
```
zie-framework/archive/backlog/.gitkeep
zie-framework/archive/specs/.gitkeep
zie-framework/archive/plans/.gitkeep
```

**Makefile** — add after existing `clean` or `release` targets:

```makefile
## Archive shipped SDLC artifacts (move Done-lane items to archive/)
archive:
	@python3 scripts/archive_shipped.py || echo "[zie-framework] archive: no items to move"
```

Or inline shell (if no scripts directory):

```makefile
archive:
	@echo "Archiving shipped backlog/specs/plans..."
	@python3 -c "
import re, shutil, sys
from pathlib import Path

zf = Path('zie-framework')
roadmap_path = zf / 'ROADMAP.md'
try:
    roadmap = roadmap_path.read_text()
except FileNotFoundError:
    print('ROADMAP.md not found — skipping archive')
    sys.exit(0)

# Extract Done lane slugs
done_match = re.search(r'## Done(.*?)(?=^## |\Z)', roadmap, re.DOTALL | re.MULTILINE)
slugs = []
if done_match:
    for line in done_match.group(1).splitlines():
        m = re.search(r'[-*]\s+\[x\].*?([a-z0-9-]+)', line.lower())
        if m:
            slugs.append(m.group(1))

for slug in slugs:
    for src in (zf / 'backlog').glob(f'*{slug}*'):
        dst = zf / 'archive' / 'backlog' / src.name
        if not dst.exists():
            shutil.move(str(src), str(dst))
            print(f'  archived backlog: {src.name}')
    for src in (zf / 'specs').glob(f'*{slug}*'):
        dst = zf / 'archive' / 'specs' / src.name
        if not dst.exists():
            shutil.move(str(src), str(dst))
            print(f'  archived spec: {src.name}')
    for src in (zf / 'plans').glob(f'*{slug}*'):
        dst = zf / 'archive' / 'plans' / src.name
        if not dst.exists():
            shutil.move(str(src), str(dst))
            print(f'  archived plan: {src.name}')
print('Archive complete.')
"
```

**`zie-release.md`** — add after Step 10 (auto-run `/zie-retro`) or after `make release`:

```markdown
**[Step 10b/10] Archive shipped SDLC artifacts:**

```bash
make archive
```

Moves completed backlog items, specs, and plans from active directories to
`zie-framework/archive/` by slug matching Done-lane entries. Git history
preserves all content — working tree reflects only active work.
```

Run: `pytest tests/unit/test_archive_structure.py` → PASS

**REFACTOR:** Verify `make archive` is idempotent (already-archived items not double-moved: `if not dst.exists()` guard handles this).

---

## Task 11: B3 Continue — zie-implement.md Pre-Flight Guard
<!-- depends_on: Task 6 -->
<!-- depends_on: Task 5 -->

**What:** Add pre-flight guard to `zie-implement.md` startup: if Ready lane empty → print error + stop. If Now lane has `[ ]` active item → print WIP error + stop. If ROADMAP.md missing → print clear error. Reads Ready lane using `parse_roadmap_ready()` from utils.py (added in Task 6).

**Acceptance Criteria:**
- Guard block appears in `ตรวจสอบก่อนเริ่ม` section
- Empty Ready lane → clear error message + stop
- `[ ]` in Now lane → WIP error + stop (already partially present — strengthen)
- ROADMAP.md missing → "ROADMAP.md not found — run /zie-init" (not crash)
- `make test-unit` green

**RED — write failing test:**

```python
# tests/unit/test_implement_preflight.py
from pathlib import Path

IMPLEMENT_MD = Path(__file__).parents[2] / "commands" / "zie-implement.md"


def test_implement_has_ready_lane_guard():
    """zie-implement.md must check Ready lane and stop if empty."""
    text = IMPLEMENT_MD.read_text()
    assert "Ready" in text
    assert "empty" in text.lower() or "no approved plan" in text.lower(), (
        "zie-implement.md must handle empty Ready lane explicitly"
    )


def test_implement_has_missing_roadmap_guard():
    """zie-implement.md must handle missing ROADMAP.md gracefully."""
    text = IMPLEMENT_MD.read_text()
    assert "not found" in text.lower() or "missing" in text.lower(), (
        "zie-implement.md must handle missing ROADMAP.md"
    )
    assert "zie-init" in text, (
        "zie-implement.md must reference /zie-init when ROADMAP.md missing"
    )
```

Run: `pytest tests/unit/test_implement_preflight.py` → FAIL (missing ROADMAP guard language)

**GREEN — update zie-implement.md `ตรวจสอบก่อนเริ่ม` section:**

Replace current step 2–3 block:
```markdown
2. Read `zie-framework/ROADMAP.md` → check Now lane:
   - `[ ]` in Now → STOP: "ยังไม่เสร็จ ทำต่อหรือ /zie-fix ก่อน"
   - `[x]` in Now → batch pending release, continue
   - Now empty → continue
3. Check Ready lane for approved plan: Read plan header only: everything up to (not including) the first `### Task` heading
   — check frontmatter for `approved: true`.
   - Empty → auto-run `/zie-plan` → get approval → continue.
```

With:
```markdown
2. **Pre-flight: ROADMAP guard** — check `zie-framework/ROADMAP.md` exists:
   - Missing → STOP: "ROADMAP.md not found — run /zie-init to initialize this project."
   - Read Now lane:
     - `[ ]` in Now → STOP: "WIP task in progress — complete it or run /zie-fix before starting a new one."
     - `[x]` in Now → batch pending release, continue
     - Now empty → continue
3. **Pre-flight: Ready lane guard** — read Ready lane:
   - Empty → STOP: "Ready lane is empty — run /zie-plan to prepare an approved plan first."
   - Check plan frontmatter for `approved: true`:
     - Not approved → STOP: "Plan in Ready lane is not approved — run /zie-plan to get approval."
```

Run: `pytest tests/unit/test_implement_preflight.py` → PASS

**REFACTOR:** Verify existing step numbering intact (steps 4–8 shift by +0, just step text updated).

---

## Task 12: A1b — Write ADR-022 and ADR-023
<!-- depends_on: none -->

**What:** Write two ADRs documenting Sprint 3 architectural decisions. ADR-022: effort routing strategy. ADR-023: archive strategy (introduced in Task 10).

**Note:** Current highest ADR is ADR-021. Next are ADR-022 and ADR-023.

**Acceptance Criteria:**
- `zie-framework/decisions/ADR-022-effort-routing-strategy.md` exists with valid ADR structure
- `zie-framework/decisions/ADR-023-archive-strategy.md` exists with valid ADR structure
- Both have: Context, Decision, Consequences sections

**RED — write failing test:**

```python
# tests/unit/test_adr_sprint3.py
from pathlib import Path

DECISIONS_DIR = Path(__file__).parents[2] / "zie-framework" / "decisions"


def _valid_adr(path: Path) -> list:
    """Return list of issues found in ADR file."""
    issues = []
    if not path.exists():
        return [f"{path.name} does not exist"]
    text = path.read_text()
    for section in ("Context", "Decision", "Consequences"):
        if f"## {section}" not in text:
            issues.append(f"Missing section: ## {section}")
    if "Status:" not in text:
        issues.append("Missing Status field")
    return issues


def test_adr_022_exists_and_valid():
    path = DECISIONS_DIR / "ADR-022-effort-routing-strategy.md"
    issues = _valid_adr(path)
    assert not issues, f"ADR-022 issues: {issues}"


def test_adr_023_exists_and_valid():
    path = DECISIONS_DIR / "ADR-023-archive-strategy.md"
    issues = _valid_adr(path)
    assert not issues, f"ADR-023 issues: {issues}"
```

Run: `pytest tests/unit/test_adr_sprint3.py` → FAIL (ADR-022 and ADR-023 missing)

**GREEN — create ADR files:**

**`zie-framework/decisions/ADR-022-effort-routing-strategy.md`:**
```markdown
# ADR-022: Effort Routing Strategy for Skills and Commands
Date: 2026-03-27
Status: Accepted

## Context
zie-framework routes tasks to different model tiers based on `effort:` frontmatter
in skills and commands. With Sonnet 4.6 as the default medium model, `effort: high`
should be reserved for tasks requiring deep reasoning loops or full dialogue cycles.
Sprint 3 audit found `write-plan` skill incorrectly tagged as `high` — it follows
a deterministic template pattern that fits `medium`.

## Decision
`effort: high` is reserved for skills/commands that require full deliberative
reasoning cycles: `spec-design` (open-ended problem framing, multi-turn dialogue)
only. All other skills and commands use `effort: medium` (Sonnet 4.6) or
`effort: low` (fast reviewer/formatter tasks). `write-plan` changed from `high`
→ `medium`. Commands audit confirmed all commands already at `medium` or `low`.

## Consequences
- Lower cost per `/zie-plan` invocation (write-plan no longer triggers high-effort routing)
- `spec-design` retains `high` for full dialogue quality
- Future skills default to `medium` unless deep reasoning loop explicitly required
- Documented in SKILL.md frontmatter — any regression caught by test_effort_audit.py
```

**`zie-framework/decisions/ADR-023-archive-strategy.md`:**
```markdown
# ADR-023: SDLC Artifact Archive Strategy
Date: 2026-03-27
Status: Accepted

## Context
zie-framework accumulates backlog items, specs, and plans over time. Shipped
artifacts remain in active directories (backlog/, specs/, plans/) indefinitely,
creating noise in reviewer context bundles and slowing glob reads. The release
step already deletes shipped artifacts (Step 4 in /zie-release), but this is
destructive — git history preserves content but local working tree loses files
without a trace for quick reference.

## Decision
Introduce `zie-framework/archive/` with three subdirectories: `archive/backlog/`,
`archive/specs/`, `archive/plans/`. Add `make archive` target that moves Done-lane
items (matched by slug) to archive after release. `zie-release.md` calls `make archive`
post-merge. Archive dirs are excluded from reviewer context bundles (reviewers read
from active dirs only). Slug matching (not exact filename) handles date-prefixed files.

## Consequences
- Active dirs contain only in-flight work — cleaner reviewer context
- Shipped artifacts queryable locally in archive/ without git log
- `make archive` is idempotent (skip if already archived)
- Reviewer skills must continue reading from active dirs only (no archive reads)
- Archive dirs tracked in git via .gitkeep; content excluded via .gitignore if desired
```

Run: `pytest tests/unit/test_adr_sprint3.py` → PASS

**REFACTOR:** None.

---

## Acceptance Criteria Checklist

| # | Criterion | Task | Verified By |
|---|-----------|------|-------------|
| 1 | `grep -r "effort: high" skills/ commands/` → only spec-design | Task 1 | test_effort_audit.py |
| 2 | Word count of zie-implement, zie-release, zie-retro each -≥10% | Task 5 | test_token_trim.py |
| 3 | COMPILED_PATTERNS at module level in intent-sdlc.py | Task 2 | test_intent_sdlc_regex.py |
| 4 | archive/ dirs exist; `make archive` moves Done items | Task 10 | test_archive_structure.py |
| 5 | `/zie-implement` empty Ready → error + stop | Task 11 | test_implement_preflight.py |
| 6 | `parse_roadmap_ready()` in utils.py | Task 6 | test_utils_ready.py |
| 7 | zie-retro.md parallel Agent calls for ADR + ROADMAP | Task 9 | test_retro_parallel.py |
| 8 | test_versioning_gate.py VERSION==plugin.json passes | Task 7 | Direct pytest run |
| 9 | `grep "\[zie\]" hooks/` → no matches | Task 3 | test_session_resume_prefix.py |
| 10 | ci.yml runs `make test-unit` | Task 8 | test_ci_config.py |
| 11 | TEST_INDICATORS configurable via .config; default unchanged | Task 4 | test_task_completed_gate_config.py |
| 12 | All existing tests pass — `make test-unit` green | All | make test-unit |

---

## Execution Order

```
Batch 1 (parallel): Task 1, Task 2, Task 3, Task 4
Batch 2 (parallel): Task 5, Task 6, Task 7, Task 8
Batch 3 (Task 6 must complete first for Task 11):
  - Task 9, Task 10, Task 12 (parallel)
  - Task 11 (after Task 6)
```
