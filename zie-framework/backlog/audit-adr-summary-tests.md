# Targeted unit tests for adr_summary.py edge cases

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`adr_summary.py` contains non-trivial extraction logic (`_extract_decision`,
`_first_sentence`, `generate_summary_table`) with no dedicated tests for
boundary cases:

- `_first_sentence`: no period, period at end, multi-sentence input
- `generate_summary_table`: decision string containing `|` pipe character
  (line 77 does `decision.replace("|", "\\|")` — one-liner with no test)
- Truncation at 80 chars when decision is very long

A regression in pipe-escaping would produce broken Markdown in the ADR
summary table silently.

## Motivation

Add ~6 targeted unit tests covering these boundary cases in
`test_adr_summarization.py`.
