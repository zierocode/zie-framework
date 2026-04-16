"""ADR summary extraction helpers.

Used by /retro to compress old ADRs into ADR-000-summary.md.
"""

from __future__ import annotations

import re

_ADR_NUMBER_RE = re.compile(r"^(ADR-\d+)", re.IGNORECASE)
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_DECISION_SECTION_RE = re.compile(r"##\s+Decision\s*\n(.*?)(?=\n##|\Z)", re.DOTALL | re.IGNORECASE)
_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)

MAX_DECISION_LEN = 120


def extract_adr_row(filename: str, content: str) -> tuple[str, str, str]:
    """Return (number, title, decision) for a single ADR.

    number  — extracted from filename prefix (e.g. "ADR-010")
    title   — text of first # heading, minus the "ADR-NNN: " prefix if present
    decision — first sentence of ## Decision section, truncated to 120 chars;
               falls back to first non-heading paragraph; then placeholder.
    """
    m = _ADR_NUMBER_RE.match(filename)
    number = m.group(1).upper() if m else "???"

    h1_match = _H1_RE.search(content)
    raw_title = h1_match.group(1).strip() if h1_match else filename
    title = re.sub(r"^ADR-\d+[:\s\-–—]+", "", raw_title, flags=re.IGNORECASE).strip()

    decision = _extract_decision(content)

    return number, title, decision


def _extract_decision(content: str) -> str:
    """Extract first sentence of ## Decision section, with fallbacks."""
    m = _DECISION_SECTION_RE.search(content)
    if m:
        section_text = m.group(1).strip()
        if section_text:
            first_sentence = _first_sentence(section_text)
            return _truncate(first_sentence)

    for para in content.split("\n\n"):
        para = para.strip()
        if para and not _HEADING_RE.match(para):
            return _truncate(_first_sentence(para))

    return "(no decision text)"


def _first_sentence(text: str) -> str:
    idx = text.find(". ")
    if idx != -1:
        return text[: idx + 1].strip()
    return text.strip()


def _truncate(text: str) -> str:
    if len(text) > MAX_DECISION_LEN:
        return text[:MAX_DECISION_LEN] + "…"
    return text


def generate_summary_table(adr_paths: list) -> str:
    """Return Markdown table content for the given list of ADR Paths."""
    header = "| ADR | Title | Decision |\n|-----|-------|----------|\n"
    rows = []
    for path in sorted(adr_paths, key=lambda p: p.name):
        content = path.read_text(encoding="utf-8")
        number, title, decision = extract_adr_row(path.name, content)
        title = title.replace("|", "\\|")
        decision = decision.replace("|", "\\|")
        rows.append(f"| {number} | {title} | {decision} |")
    return header + "\n".join(rows) + ("\n" if rows else "")
