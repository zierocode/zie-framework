---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-parse-roadmap-edge-cases.md
---

# parse_roadmap_now() — Edge Case Tests for Inline Markdown and Malformed Links — Design Spec

**Problem:** `test_utils.py` does not cover inline markdown formatting inside task lines (`**bold**`, `_italic_`), malformed link syntax with a missing closing parenthesis (`[title](url`), or HTML entities in task descriptions — all realistic ROADMAP content patterns that could cause tasks to be silently dropped or returned with noise.

**Approach:** Add a new test class `TestParseRoadmapNowEdgeCases` to `test_utils.py` with one test per edge-case pattern. Each test writes a minimal ROADMAP fixture, calls `parse_roadmap_now()`, and asserts the exact returned list. No changes to `hooks/utils.py` are required unless a test reveals a real bug — in that case, fix the parser and update the spec before merging.

**Components:**
- `tests/unit/test_utils.py` — new class `TestParseRoadmapNowEdgeCases` appended after `TestParseRoadmapNow`
- `hooks/utils.py` — `parse_roadmap_now()` (may require fix if tests expose a defect)

**Data Flow — test cases to add:**

1. `test_bold_inline_markdown_in_task`: ROADMAP `"## Now\n- [ ] **Refactor** the payment module\n"` → expected `["**Refactor** the payment module"]` (inline markdown is preserved — the function strips list prefix and checkbox only, not inline formatting).
2. `test_italic_inline_markdown_in_task`: ROADMAP `"## Now\n- [ ] fix _memory leak_ in cache\n"` → expected `["fix _memory leak_ in cache"]`.
3. `test_malformed_link_missing_closing_paren`: ROADMAP `"## Now\n- [ ] my feature — [plan](plans/foo.md\n"` → expected result is either `["my feature — [plan](plans/foo.md"]` (regex does not match, raw text preserved) or `["my feature — plan"]` (regex matches partial). Assert whichever reflects current `re.sub` behaviour — document the contract explicitly.
4. `test_html_entity_in_task_description`: ROADMAP `"## Now\n- [ ] support &amp; operator\n"` → expected `["support &amp; operator"]` (entities are not decoded — plain text passthrough).
5. `test_nested_bold_link_combo`: ROADMAP `"## Now\n- [ ] **bold link** — [spec](specs/foo.md)\n"` → expected `["**bold link** — spec"]` (link stripped, bold preserved).

**Edge Cases:**
- The existing `re.sub(r'\[([^\]]+)\]\([^\)]+\)', ...)` regex requires a closing `)` to match — a malformed link without `)` will NOT be stripped. Test #3 documents this known behaviour so it is explicit rather than accidental.
- HTML entities are never decoded by the function — this is intentional (ROADMAP is plain markdown, not HTML).
- Inline code spans (`` `code` ``) are not listed as a target in the backlog item but follow the same "preserved as-is" contract — a follow-up test can be added without a new spec.

**Out of Scope:**
- Changing the stripping behaviour for inline markdown (the function's purpose is task extraction, not full markdown rendering).
- Testing `parse_roadmap_now()` with binary/non-UTF-8 file content (separate concern).
- Performance testing on very large ROADMAP files.
