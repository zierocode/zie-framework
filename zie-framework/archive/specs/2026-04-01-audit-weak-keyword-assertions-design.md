---
slug: audit-weak-keyword-assertions
status: approved
date: 2026-04-01
---
# Spec: Replace Keyword Assertions with Structural Checks (zie-implement + zie-release)

## Problem

~335 test assertions across `test_sdlc_gates.py`, `test_sdlc_pipeline.py`,
`test_hybrid_release.py`, and similar files use the pattern:

```python
assert "keyword" in read("commands/zie-implement.md")
```

These checks guard against accidental content deletion, but provide no
structural guarantees. A command file can pass all keyword tests while having
its phases in the wrong order, missing required frontmatter, or containing
sections in the wrong location. When a command file is refactored, these tests
pass trivially as long as the keyword survives anywhere in the file.

This is distinct from `audit-weak-nocrash-assertions` (which covers
`returncode == 0` process checks). This backlog item covers Markdown content
presence checks only.

## Proposed Solution

For the two highest-traffic commands — `zie-implement.md` and `zie-release.md`
— introduce a `parse_sections(content)` test helper that returns an ordered
list of section headers and their positions. Use this helper to write
structural assertions:

- **Section existence at expected depth** — assert a specific `## Phase` or
  `### Step` header is present (not just a word somewhere in the file).
  Example: for `zie-implement.md`, assert the section `## RED` exists by
  checking `parse_sections()` returns a header named "RED" at depth 2.
- **Phase ordering** — assert that required phase sections within the command
  file appear in the correct relative order. Example in `zie-implement.md`:
  assert `## RED` header line number < `## GREEN` header line number <
  `## REFACTOR` header line number.
- **Required frontmatter** — assert that YAML frontmatter contains required
  keys (`slug`, `title`) when present.

New structural tests live alongside existing keyword tests in the same test
class. Existing keyword tests are removed only when a structural test covers
the same invariant. No keyword test is deleted without a replacement structural
test in the same commit.

Scope is limited to two command files. The remaining ~300+ keyword assertions
across other commands are out of scope for this sprint.

## Acceptance Criteria

- [ ] AC1: A `parse_sections(content: str) -> list[tuple[int, str, str]]` helper is added to `tests/unit/test_sdlc_gates.py`. Each tuple is `(line_number, hashes, title)` where `hashes` is the `#` prefix (e.g., `"##"`).
- [ ] AC2: At least 3 keyword assertions for `zie-implement.md` are replaced with structural assertions that verify section existence by header name (not substring anywhere in file).
- [ ] AC3: Phase ordering for `zie-implement.md` is asserted: the `## RED` section appears before `## GREEN`, and `## GREEN` before `## REFACTOR` (using line number comparison via `parse_sections`).
- [ ] AC4: At least 3 keyword assertions for `zie-release.md` are replaced with structural assertions that verify section existence by header name.
- [ ] AC5: Phase/step ordering for `zie-release.md` is asserted: at minimum 2 required phase sections (e.g., `## Changelog Approval` before `## Doc Sync Check`) appear in documented order (line number comparison).
- [ ] AC6: All replaced keyword assertions have a 1-to-1 structural replacement — no invariant is dropped without a replacement.
- [ ] AC7: `make test-ci` passes with zero regressions after the changes.
- [ ] AC8: The `parse_sections` helper is covered by at least 2 unit tests of its own (handles empty input, handles multiple heading depths).

## Out of Scope

- Converting keyword assertions for commands other than `zie-implement.md` and `zie-release.md`.
- Frontmatter parsing or YAML validation (separate concern, separate backlog item if needed).
- Changing how command files are structured — this spec only changes tests, not command content.
- Integration-test or subprocess-based structural checks (unit file only).
- Achieving 100% structural coverage of either command file in this sprint.
