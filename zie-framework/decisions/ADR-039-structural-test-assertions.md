# ADR-039: Structural Test Assertions Over Keyword Presence

## Status
Accepted

## Context
The test suite had ~335 assertions of the form `assert "keyword" in content` checking that command files contain certain words. These tests passed even when required sections were reordered, moved, or the keyword appeared in the wrong context. The pattern gave false confidence.

## Decision
Replace keyword-presence checks with structural assertions that verify semantic properties: section ordering (via `assert_sections_ordered(content, *headers)`), header presence (via `section_headers(content)`), and frontmatter properties. The `assert_sections_ordered` helper verifies all headers appear in content in the given order using `str.find()` positions.

## Consequences
**Positive:** Tests catch regressions where content is present but structurally wrong (e.g., version bump step before gates). False positive rate reduced.
**Negative:** Slightly more verbose test code per assertion.
**Neutral:** Applies to command/*.md files; hooks and utils tests use different patterns.

## Alternatives
Considered: AST parsing of markdown (ADR-036 already decided against for hook testing — same reasoning applies). Section ordering checks are simpler and sufficient.
