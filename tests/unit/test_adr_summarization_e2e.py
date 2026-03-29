"""End-to-end smoke tests for ADR summarization pipeline."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from hooks.adr_summary import generate_summary_table


def _make_adrs(directory: Path, count: int) -> list:
    paths = []
    for i in range(1, count + 1):
        p = directory / f"ADR-{i:03d}-slug-{i}.md"
        p.write_text(
            f"# ADR-{i:03d}: Slug {i}\n\n## Decision\n\nDecision text for ADR {i}.\n",
            encoding="utf-8",
        )
        paths.append(p)
    return paths


def _simulate_retro_summarization(directory: Path) -> dict:
    individual = sorted([
        p for p in directory.glob("ADR-*.md")
        if p.name != "ADR-000-summary.md"
    ])
    count = len(individual)
    summary_written = False
    compressed_count = 0

    if count > 30 and count > 10:
        to_compress = individual[:-10]
        summary_path = directory / "ADR-000-summary.md"
        table = generate_summary_table(to_compress)
        summary_path.write_text("# ADR Summary\n\n" + table, encoding="utf-8")
        for p in to_compress:
            p.unlink()
        summary_written = True
        compressed_count = len(to_compress)

    remaining = sorted([
        p for p in directory.glob("ADR-*.md")
        if p.name != "ADR-000-summary.md"
    ])
    return {
        "summary_written": summary_written,
        "compressed_count": compressed_count,
        "remaining_individual": len(remaining),
        "summary_exists": (directory / "ADR-000-summary.md").exists(),
    }


def test_35_adrs_triggers_summarization(tmp_path):
    _make_adrs(tmp_path, 35)
    result = _simulate_retro_summarization(tmp_path)
    assert result["summary_written"] is True
    assert result["compressed_count"] == 25
    assert result["remaining_individual"] == 10
    assert result["summary_exists"] is True


def test_10_adrs_no_summarization(tmp_path):
    _make_adrs(tmp_path, 10)
    result = _simulate_retro_summarization(tmp_path)
    assert result["summary_written"] is False
    assert result["compressed_count"] == 0
    assert result["summary_exists"] is False


def test_30_adrs_no_summarization(tmp_path):
    _make_adrs(tmp_path, 30)
    result = _simulate_retro_summarization(tmp_path)
    assert result["summary_written"] is False
    assert result["summary_exists"] is False


def test_31_adrs_triggers_summarization(tmp_path):
    _make_adrs(tmp_path, 31)
    result = _simulate_retro_summarization(tmp_path)
    assert result["summary_written"] is True
    assert result["compressed_count"] == 21
    assert result["remaining_individual"] == 10


def test_summary_table_has_correct_row_count(tmp_path):
    _make_adrs(tmp_path, 35)
    _simulate_retro_summarization(tmp_path)
    summary = (tmp_path / "ADR-000-summary.md").read_text()
    data_rows = [line for line in summary.splitlines() if line.startswith("| ADR-")]
    assert len(data_rows) == 25


def test_idempotent_rerun(tmp_path):
    _make_adrs(tmp_path, 35)
    _simulate_retro_summarization(tmp_path)
    content_after_first = (tmp_path / "ADR-000-summary.md").read_text()
    result2 = _simulate_retro_summarization(tmp_path)
    assert result2["summary_written"] is False
    content_after_second = (tmp_path / "ADR-000-summary.md").read_text()
    assert content_after_first == content_after_second
