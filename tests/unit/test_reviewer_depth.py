from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SKILLS = ROOT / "skills"


def read_skill(name):
    return (SKILLS / name / "SKILL.md").read_text()


# ── spec-reviewer ────────────────────────────────────────────────────────────

def test_spec_reviewer_has_context_bundle():
    content = read_skill("spec-reviewer")
    assert "context bundle" in content.lower() or "Context Bundle" in content


def test_spec_reviewer_reads_decisions():
    content = read_skill("spec-reviewer")
    assert "decisions/" in content or "decisions/*.md" in content


def test_spec_reviewer_reads_roadmap():
    content = read_skill("spec-reviewer")
    assert "ROADMAP" in content


def test_spec_reviewer_checks_file_existence():
    content = read_skill("spec-reviewer")
    assert "FILE NOT FOUND" in content or "file exist" in content.lower()


def test_spec_reviewer_checks_adr_conflict():
    content = read_skill("spec-reviewer")
    assert "ADR" in content or "conflict" in content.lower()


def test_spec_reviewer_checks_roadmap_conflict():
    content = read_skill("spec-reviewer")
    assert "ROADMAP conflict" in content or "duplicate" in content.lower()


# ── plan-reviewer ────────────────────────────────────────────────────────────

def test_plan_reviewer_has_context_bundle():
    content = read_skill("plan-reviewer")
    assert "context bundle" in content.lower() or "Context Bundle" in content


def test_plan_reviewer_reads_decisions():
    content = read_skill("plan-reviewer")
    assert "decisions/" in content or "decisions/*.md" in content


def test_plan_reviewer_checks_file_existence():
    content = read_skill("plan-reviewer")
    assert "FILE NOT FOUND" in content or "file exist" in content.lower()


def test_plan_reviewer_checks_adr_conflict():
    content = read_skill("plan-reviewer")
    assert "ADR" in content or "conflict" in content.lower()


def test_plan_reviewer_checks_roadmap_conflict():
    content = read_skill("plan-reviewer")
    assert "ROADMAP conflict" in content or "duplicate" in content.lower()


def test_plan_reviewer_checks_pattern_match():
    content = read_skill("plan-reviewer")
    assert "pattern" in content.lower()


# ── impl-reviewer ────────────────────────────────────────────────────────────

def test_impl_reviewer_has_context_bundle():
    content = read_skill("impl-reviewer")
    assert "context bundle" in content.lower() or "Context Bundle" in content


def test_impl_reviewer_reads_decisions():
    content = read_skill("impl-reviewer")
    assert "decisions/" in content or "decisions/*.md" in content


def test_impl_reviewer_checks_file_existence():
    content = read_skill("impl-reviewer")
    assert "FILE NOT FOUND" in content or "file exist" in content.lower()


def test_impl_reviewer_no_roadmap_conflict_check():
    content = read_skill("impl-reviewer")
    assert "ROADMAP conflict" not in content


def test_impl_reviewer_checks_pattern_match():
    content = read_skill("impl-reviewer")
    assert "pattern" in content.lower()
