import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()


def assert_sections_ordered(content: str, *headers: str) -> None:
    """Assert that all headers appear in content in the given order."""
    positions = []
    for h in headers:
        idx = content.find(h)
        assert idx != -1, f"Section header not found: {h!r}"
        positions.append(idx)
    assert positions == sorted(positions), \
        f"Sections out of order: {list(zip(headers, positions))}"


def section_headers(content: str) -> list:
    """Return all lines starting with ## or ### from content."""
    return [line for line in content.splitlines() if line.startswith("## ") or line.startswith("### ")]


import json
import subprocess
import sys


class TestZieInitBacklog:
    def test_init_creates_backlog_dir(self):
        content = read("commands/zie-init.md")
        assert "backlog" in content, \
            "/zie-init must create zie-framework/backlog/ directory"

class TestZieReleaseVersionSuggest:
    def test_ship_suggests_version_bump(self):
        content = read("commands/zie-release.md")
        # Structural: all three bump types defined inside the release gate section
        assert "major" in content and "minor" in content and "patch" in content, \
            "/zie-release must define rules for major, minor, and patch bumps"
        # Version bump step must appear inside the release gate section
        assert_sections_ordered(content, "## All Gates Passed", "major")

    def test_ship_version_rules_cover_all_three(self):
        content = read("commands/zie-release.md")
        # Structural: verify all three bump types appear in that section
        headers = section_headers(content)
        assert len(headers) >= 3, f"/zie-release must have ≥3 section headers, got: {headers}"


class TestZieReleaseChangelog:
    def test_ship_changelog_has_approve_flow(self):
        content = read("commands/zie-release.md")
        # Structural: CHANGELOG section must exist and version section appears before it
        assert_sections_ordered(content, "## ลำดับการตรวจสอบ", "## All Gates Passed")

    def test_ship_changelog_handles_first_release(self):
        content = read("commands/zie-release.md")
        assert "max-parents=0" in content or "rev-list" in content, \
            "/zie-release must handle first release (no previous tag) via git rev-list fallback"


class TestZieReleaseDocSync:
    def test_ship_has_doc_sync_gate(self):
        content = read("commands/zie-release.md")
        # Structural: docs-sync-check skill must be invoked, and doc sync precedes the release gate
        assert "docs-sync-check" in content, \
            "/zie-release must invoke docs-sync-check for doc sync gate"
        assert_sections_ordered(content, "docs-sync-check", "## All Gates Passed")


class TestZieReleaseMemory:
    def test_ship_reads_wip_before_write(self):
        content = read("commands/zie-release.md")
        # Structural: pre-flight check section exists before the release gate
        assert_sections_ordered(content, "## ตรวจสอบก่อนเริ่ม", "## All Gates Passed")

class TestZieRetroMemory:
    def test_retro_recalls_all_since_last(self):
        content = read("commands/zie-retro.md")
        # Structural: retro command must have at least 3 section headers
        headers = section_headers(content)
        assert len(headers) >= 3, f"/zie-retro must have ≥3 section headers, got: {headers}"


class TestIntentDetectPlan:
    def test_plan_pattern_in_code(self):
        content = read("hooks/intent-sdlc.py")
        assert '"plan"' in content or "'plan'" in content, \
            "intent-sdlc.py must have a plan category"

    def test_plan_suggestion_maps_to_zie_plan(self):
        content = read("hooks/intent-sdlc.py")
        assert "/zie-plan" in content, \
            "intent-sdlc.py must suggest /zie-plan"

    def test_plan_intent_detected_thai(self):
        """Test that Thai planning phrases trigger plan intent."""
        hook = os.path.join(REPO_ROOT, "hooks", "intent-sdlc.py")
        event = {"prompt": "อยากวางแผน feature ใหม่"}
        env = {**os.environ, "CLAUDE_CWD": REPO_ROOT}
        result = subprocess.run(
            [sys.executable, hook],
            input=json.dumps(event),
            capture_output=True, text=True, env=env
        )
        assert "/zie-plan" in result.stdout, \
            f"Thai planning phrase should trigger /zie-plan, got: {result.stdout!r}"


class TestZieImplementGates:
    def test_build_checks_wip_limit(self):
        content = read("commands/zie-implement.md")
        # Gate 1: [ ] = block (in-progress), [x] = leave in Now for batch release (zie-ship moves to Done)
        assert "[ ]" in content and "[x]" in content and "Now" in content, \
            "/zie-implement Gate 1 must handle both in-progress ([ ]) and done ([x]) items in Now lane"

    def test_build_does_not_move_done_to_done_section(self):
        content = read("commands/zie-implement.md")
        # [x] items must NOT be moved to Done by zie-build — only zie-ship does that
        assert "ย้าย item ไป Done" not in content and "move.*Done" not in content, \
            "/zie-implement must NOT move [x] items to Done — only /zie-release does that on release"

    def test_build_checks_approved_plan(self):
        content = read("commands/zie-implement.md")
        assert "approved: true" in content, \
            "/zie-implement must check for approved: true in plan frontmatter"

    def test_build_has_auto_fallback(self):
        content = read("commands/zie-implement.md")
        # Structural: /zie-plan referenced and approved: true appears before Steps section
        assert "/zie-plan" in content, "/zie-implement must reference /zie-plan as fallback"
        assert_sections_ordered(content, "approved: true", "## Steps")

    def test_build_has_parallel_agents(self):
        content = read("commands/zie-implement.md")
        # Structural: Task Parallelism section exists before Steps
        assert_sections_ordered(content, "## Task Parallelism", "## Steps")

    def test_build_has_depends_on(self):
        content = read("commands/zie-implement.md")
        assert "depends_on" in content, \
            "/zie-implement must parse depends_on for task dependency ordering"

    def test_build_has_micro_learning(self):
        content = read("commands/zie-implement.md")
        # Structural: Steps section must appear before the test failure section
        assert_sections_ordered(content, "## Steps", "## เมื่อ test ล้มเหลว")


class TestZiePlanCommand:
    def test_command_file_exists(self):
        path = os.path.join(REPO_ROOT, "commands", "zie-plan.md")
        assert os.path.isfile(path), "commands/zie-plan.md must exist"

    def test_command_handles_no_args(self):
        content = read("commands/zie-plan.md")
        assert "No arguments" in content or "no args" in content.lower() \
            or "empty" in content.lower() or "list" in content.lower(), \
            "/zie-plan with no args must list backlog items"

    def test_command_has_approval_gate(self):
        content = read("commands/zie-plan.md")
        assert "approved: true" in content, \
            "/zie-plan must set approved: true in plan frontmatter"

    def test_command_moves_to_ready(self):
        content = read("commands/zie-plan.md")
        assert "Ready" in content, \
            "/zie-plan must move approved plan to Ready lane"

    def test_command_has_parallel_agents(self):
        content = read("commands/zie-plan.md")
        assert "parallel" in content.lower() and "4" in content, \
            "/zie-plan must support parallel agents capped at 4"

    def test_command_has_memory_integration(self):
        content = read("commands/zie-plan.md")
        assert "recall" in content.lower() and "remember" in content.lower(), \
            "/zie-plan must have zie-memory READ and WRITE steps"


class TestZieBacklogFirst:
    def test_idea_writes_to_next_not_now(self):
        content = read("commands/zie-backlog.md")
        assert "Next section" in content or "ROADMAP Next" in content \
            or "## Next" in content or '"Next"' in content, \
            "/zie-backlog must write to Next (backlog), not Now"

    def test_idea_does_not_move_to_now(self):
        content = read("commands/zie-backlog.md")
        assert 'Add feature to "Now" section' not in content, \
            "/zie-backlog must not move feature to Now"

    def test_idea_has_memory_recall(self):
        content = read("commands/zie-backlog.md")
        assert "recall" in content.lower(), \
            "/zie-backlog must recall memories before capturing idea"

    def test_idea_has_memory_store(self):
        content = read("commands/zie-backlog.md")
        assert "remember" in content.lower() or "store" in content.lower(), \
            "/zie-backlog must store backlog item in zie-memory"


class TestZieImplementTestPyramid:
    def test_build_has_inline_test_guidance(self):
        content = read("commands/zie-implement.md")
        assert "Test level selection" in content, \
            "/zie-implement must contain inline Test level selection guidance"

    def test_build_tdd_loop_skill_for_deep(self):
        content = read("commands/zie-implement.md")
        assert "zie-framework:tdd-loop" in content, \
            "/zie-implement must reference zie-framework:tdd-loop for tdd: deep path"

    def test_build_guidance_printed_before_red_phase(self):
        content = read("commands/zie-implement.md")
        guidance_pos = content.find("Test level selection")
        tdd_pos = content.find("→ TDD loop")
        if tdd_pos == -1:
            tdd_pos = content.find("Skill(zie-framework:tdd-loop)")
        assert guidance_pos != -1 and tdd_pos != -1, \
            "/zie-implement must have both Test level selection guidance and TDD loop invocation"
        assert guidance_pos < tdd_pos, \
            "Test level selection guidance must appear before the TDD loop invocation"

    def test_build_pyramid_guides_test_level(self):
        content = read("commands/zie-implement.md")
        assert "unit" in content and "integration" in content and "e2e" in content, \
            "/zie-implement must mention unit/integration/e2e levels (guided by test-pyramid)"


class TestZieStatusHealth:
    def test_status_checks_lastfailed_file(self):
        content = read("commands/zie-status.md")
        assert ".pytest_cache/v/cache/lastfailed" in content, \
            "/zie-status step 4 must check .pytest_cache/v/cache/lastfailed"

    def test_status_detects_fail_on_nonempty_lastfailed(self):
        content = read("commands/zie-status.md")
        assert "non-empty" in content or "nonempty" in content or "not empty" in content, \
            "/zie-status step 4 must treat non-empty lastfailed as fail (✗)"

    def test_status_detects_pass_on_empty_lastfailed(self):
        content = read("commands/zie-status.md")
        assert "empty" in content and ("pass" in content.lower() or "✓" in content), \
            "/zie-status step 4 must treat empty lastfailed as pass (✓)"

    def test_status_detects_stale_on_no_cache(self):
        content = read("commands/zie-status.md")
        assert "no .pytest_cache" in content or "no cache" in content.lower() \
            or ".pytest_cache/` at all" in content or "no `.pytest_cache" in content, \
            "/zie-status step 4 must report ? stale when .pytest_cache is absent"

    def test_status_detects_stale_on_newer_test_files(self):
        content = read("commands/zie-status.md")
        assert "mtime" in content or "modified" in content.lower() or "newer" in content, \
            "/zie-status step 4 must compare mtime of cache vs test files"


class TestZieFixMemory:
    def test_fix_uses_batch_recall_with_domain(self):
        content = read("commands/zie-fix.md")
        assert "domain" in content and "tags=[bug" in content, \
            "/zie-fix must use batch recall with domain= and tags=[bug, ...]"

    def test_fix_recall_has_limit(self):
        content = read("commands/zie-fix.md")
        assert "limit=10" in content, \
            "/zie-fix recall must set limit=10 for batch query"

    def test_fix_stores_root_cause_and_pattern(self):
        content = read("commands/zie-fix.md")
        assert "root cause" in content.lower() and "pattern" in content.lower(), \
            "/zie-fix must store root cause and recurring/one-off pattern in remember call"

    def test_fix_remember_tags_use_domain_not_module_slug(self):
        content = read("commands/zie-fix.md")
        assert "tags=[bug, <project>, <domain>]" in content, \
            "/zie-fix remember must use tags=[bug, <project>, <domain>] not module-slug"


class TestROADMAPReadyLane:
    def test_template_has_ready_section(self):
        content = read("templates/ROADMAP.md.template")
        assert "## Ready" in content, "ROADMAP template must have Ready lane"

    def test_template_ready_before_now(self):
        content = read("templates/ROADMAP.md.template")
        ready_pos = content.find("## Ready")
        now_pos = content.find("## Now")
        assert ready_pos < now_pos, "Ready lane must appear before Now in template"


class TestCommandLineCounts:
    def test_zie_implement_line_count(self):
        content = read("commands/zie-implement.md")
        lines = content.splitlines()
        assert len(lines) <= 160, f"zie-implement.md is {len(lines)} lines (max 160)"

    def test_zie_implement_no_parallel_cap(self):
        content = read("commands/zie-implement.md")
        assert "max parallel tasks: 4" not in content.lower()
        assert "max 4 parallel" not in content.lower()

    def test_zie_plan_no_parallel_cap(self):
        content = read("commands/zie-plan.md")
        assert "max 4 parallel" not in content.lower()
        assert "max parallel agents: 4" not in content.lower()
