# Replace keyword-in-content assertions with structural checks for command files

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

~335 test assertions across `test_sdlc_gates.py`, `test_sdlc_pipeline.py`,
`test_hybrid_release.py` and similar files use the pattern:
`assert "keyword" in read("commands/...")`. These guard against content
deletion but tell you nothing about whether the logic is correct. When a
command file is updated, these tests pass trivially as long as the keyword
survives anywhere in the file.

This is distinct from `audit-weak-nocrash-assertions.md` (which covers
`returncode == 0`) — these are Markdown content presence checks.

## Motivation

Incrementally replace with structural checks: assert specific section headers
exist, assert required frontmatter keys are present, assert phase ordering is
correct. Don't remove all at once — prioritize the highest-traffic commands
(zie-implement, zie-release) first.
