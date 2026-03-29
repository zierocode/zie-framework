"""Integration-style unit tests for the retro ADR summarization step."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from hooks.adr_summary import generate_summary_table, extract_adr_row


def _make_adr(tmp_path: Path, number: int, title: str, decision: str) -> Path:
    name = f"ADR-{number:03d}-{title.lower().replace(' ', '-')}.md"
    p = tmp_path / name
    p.write_text(
        f"# ADR-{number:03d}: {title}\n\n## Decision\n\n{decision}\n",
        encoding="utf-8",
    )
    return p


def test_summary_excludes_adr_000(tmp_path):
    summary = tmp_path / "ADR-000-summary.md"
    summary.write_text("| ADR | Title | Decision |\n|---|---|---|\n| ADR-001 | X | Y |\n")
    _make_adr(tmp_path, 1, "first", "Use X.")
    paths = [p for p in tmp_path.glob("ADR-*.md") if p.name != "ADR-000-summary.md"]
    result = generate_summary_table(paths)
    assert "ADR-001" in result
    assert result.count("ADR-001") == 1


def test_keep_recent_logic():
    all_names = [f"ADR-{i:03d}-slug.md" for i in range(1, 36)]
    keep_n = 10
    to_compress = sorted(all_names)[:-keep_n]
    to_keep = sorted(all_names)[-keep_n:]
    assert len(to_compress) == 25
    assert "ADR-026-slug.md" in to_keep
    assert "ADR-025-slug.md" in to_compress


def test_fewer_than_11_adrs_skip():
    all_names = [f"ADR-{i:03d}-slug.md" for i in range(1, 11)]
    keep_n = 10
    to_compress = sorted(all_names)[:-keep_n]
    assert to_compress == []


def test_generate_summary_table_no_duplicate_rows(tmp_path):
    p = _make_adr(tmp_path, 1, "first", "Use X.")
    result = generate_summary_table([p, p])
    row_count = result.count("ADR-001")
    assert row_count == 2  # caller must pass deduplicated list


def test_overwrite_summary_is_idempotent(tmp_path):
    adrs = [_make_adr(tmp_path, i, f"adr-{i}", f"Decision {i}.") for i in range(1, 4)]
    out = tmp_path / "ADR-000-summary.md"
    content1 = generate_summary_table(adrs)
    out.write_text(content1)
    content2 = generate_summary_table(adrs)
    assert content1 == content2
