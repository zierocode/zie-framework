"""Structural test: no verbatim duplicate paragraph blocks in any SKILL.md."""

import glob
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MIN_PARAGRAPH_CHARS = 80
MIN_PARAGRAPH_LINES = 2


def _strip_frontmatter(content: str) -> str:
    if not content.startswith("---"):
        return content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content
    return parts[2]


def _get_paragraphs(content: str) -> list[str]:
    body = _strip_frontmatter(content)
    raw_blocks = body.split("\n\n")
    paragraphs = []
    for block in raw_blocks:
        stripped = block.strip()
        if not stripped:
            continue
        if stripped in ("---", "===", "***"):
            continue
        line_count = len(stripped.splitlines())
        if len(stripped) >= MIN_PARAGRAPH_CHARS or line_count >= MIN_PARAGRAPH_LINES:
            paragraphs.append(stripped)
    return paragraphs


def _find_skill_files() -> list[str]:
    pattern = os.path.join(REPO_ROOT, "skills", "*", "SKILL.md")
    return sorted(glob.glob(pattern))


class TestSkillDedupNoDuplicateParagraphs:
    def test_no_verbatim_duplicate_paragraphs_in_any_skill(self):
        """Each SKILL.md must not repeat a paragraph block verbatim."""
        skill_files = _find_skill_files()
        assert skill_files, "No SKILL.md files found — check REPO_ROOT"

        violations: list[str] = []
        for path in skill_files:
            with open(path) as f:
                content = f.read()
            paragraphs = _get_paragraphs(content)
            seen: dict[str, int] = {}
            for para in paragraphs:
                seen[para] = seen.get(para, 0) + 1
            duplicates = {p: count for p, count in seen.items() if count >= 2}
            if duplicates:
                rel = os.path.relpath(path, REPO_ROOT)
                for para, count in duplicates.items():
                    preview = para[:120].replace("\n", " ")
                    violations.append(f"{rel}: paragraph appears {count}x — '{preview}...'")

        assert not violations, "Verbatim duplicate paragraphs found in SKILL.md files:\n" + "\n".join(
            f"  - {v}" for v in violations
        )
