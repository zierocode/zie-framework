from pathlib import Path

CMD = Path(__file__).parents[2] / "commands" / "implement.md"


def text():
    return CMD.read_text()


class TestRiskClassificationBlockPresent:
    def test_command_file_exists(self):
        assert CMD.exists()

    def test_risk_classification_heading_present(self):
        assert "Risk Classification" in text(), "zie-implement.md must contain a Risk Classification section"

    def test_risk_level_variable_defined(self):
        assert "risk_level" in text(), "zie-implement.md must define a risk_level variable"

    def test_high_risk_label_present(self):
        assert "HIGH" in text(), "zie-implement.md must reference the HIGH risk label"

    def test_low_risk_label_present(self):
        assert "LOW" in text(), "zie-implement.md must reference the LOW risk label"


class TestHighRiskSignals:
    def test_new_function_keyword(self):
        assert "new function" in text().lower() or "new function/class" in text().lower(), (
            "HIGH signals must mention new function/class"
        )

    def test_changed_behavior_keyword(self):
        assert "changed behavior" in text().lower(), "HIGH signals must mention changed behavior"

    def test_external_api_keyword(self):
        assert "external api" in text().lower(), "HIGH signals must mention external API call"

    def test_security_sensitive_keyword(self):
        t = text().lower()
        assert "auth" in t or "file i/o" in t or "subprocess" in t, "HIGH signals must mention auth/file-IO/subprocess"

    def test_review_required_annotation(self):
        assert "review: required" in text(), "HIGH signals must mention review: required annotation override"


class TestLowRiskSignals:
    def test_test_only_keyword(self):
        t = text().lower()
        assert "test only" in t or "test-only" in t or "add/edit test" in t, "LOW signals must mention test-only tasks"

    def test_docs_config_keyword(self):
        t = text().lower()
        assert "docs" in t and "config" in t, "LOW signals must mention docs/config changes"

    def test_rename_reformat_keyword(self):
        t = text().lower()
        assert "rename" in t or "reformat" in t, "LOW signals must mention rename/reformat"

    def test_minor_addition_keyword(self):
        t = text().lower()
        assert "minor" in t, "LOW signals must mention minor additions"


class TestReviewerGate:
    def test_reviewer_gated_on_high(self):
        t = text()
        assert "risk_level" in t and "HIGH" in t, "Reviewer invocation must be gated by risk_level=HIGH"

    def test_inline_review_gated_on_high(self):
        t = text().lower()
        assert "inline" in t and "high" in t, "Inline review must be present and gated on HIGH risk"

    def test_low_path_runs_make_test_unit(self):
        t = text()
        assert "make test-unit" in t, "make test-unit must remain present for the LOW path"

    def test_reviewer_not_invoked_unconditionally(self):
        t = text().lower()
        lines = t.splitlines()
        reviewer_lines = [i for i, ln in enumerate(lines) if "impl-review" in ln and "skill" in ln]
        assert reviewer_lines, "Skill(zie-framework:impl-review) line must exist in implement.md"
        for idx in reviewer_lines:
            context_block = "\n".join(lines[max(0, idx - 10) : idx + 1])
            assert "high" in context_block, f"impl-review Skill at line {idx + 1} must be inside a HIGH risk guard"
