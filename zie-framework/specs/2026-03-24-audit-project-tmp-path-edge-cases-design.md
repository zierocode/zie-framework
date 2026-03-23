---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-project-tmp-path-edge-cases.md
---

# project_tmp_path() — Edge Case Tests for Pathological Input Names — Design Spec

**Problem:** `test_utils.py` has no tests for unicode/emoji project names, names with leading dashes, very long names (>255 chars), or path traversal attempts (`..` in the project name) — all plausible values for `cwd.name`.

**Approach:** Add a new test class `TestProjectTmpPathEdgeCases` to `test_utils.py`. Each test calls `project_tmp_path()` with a pathological input and asserts the returned path is valid and safe. If a test reveals a case where the current implementation produces an unsafe or OS-breaking path, fix `hooks/utils.py` before merging and update the spec's expected values accordingly.

**Components:**
- `tests/unit/test_utils.py` — new class `TestProjectTmpPathEdgeCases` appended after `TestProjectTmpPath`
- `hooks/utils.py` — `project_tmp_path()` (may require hardening)

**Data Flow — test cases to add:**

1. `test_unicode_project_name`: `project_tmp_path("last-test", "mon-projet-cafe")` (latin extended) → assert returned path string contains only ASCII-safe chars (the `re.sub(r'[^a-zA-Z0-9]', '-', ...)` regex replaces all non-alphanumeric chars including accented letters → `"mon-projet-caf-"` prefix). Verify path is a valid `Path` object.
2. `test_emoji_project_name`: `project_tmp_path("edit-count", "my-app-rocket-emoji")` with a name containing an emoji character → assert the emoji is replaced by `-` and the result is a valid path string with no multi-byte characters.
3. `test_leading_dash_project_name`: `project_tmp_path("last-test", "-myproject")` → assert the resulting path is `/tmp/zie--myproject-last-test` (leading dash in project name produces `--` prefix). Document that this is the current behaviour; no fix required unless it causes filesystem issues.
4. `test_very_long_project_name`: `project_tmp_path("edit-count", "x" * 256)` → assert `len(str(result.name)) > 255` (current implementation does NOT truncate). This test documents the known gap. If the OS filesystem limit is exceeded, the test should assert that `result.name` does not raise on construction (Path construction itself will not fail; the failure occurs at write time). Add a note in the test docstring that callers must handle `OSError` on write.
5. `test_path_traversal_attempt`: `project_tmp_path("last-test", "../etc")` → the `re.sub` replaces `.` and `/` with `-`, producing `/tmp/zie----etc-last-test`. Assert the result does NOT contain `..` or `/` in the project segment, confirming traversal is neutralised.
6. `test_dot_only_project_name`: `project_tmp_path("x", ".")` → `re.sub` → `"-"` → result is `/tmp/zie---x`. Assert it is a valid path and contains no unescaped dot segment.

**Edge Cases:**
- Python `Path` construction never fails on long strings — the `OSError` (ENAMETOOLONG) only surfaces at filesystem write time. The test for very long names (#4) therefore asserts the string length and documents the risk; it does not attempt to write the file.
- Emoji characters are multi-byte in UTF-8 but `re.sub` operates on Unicode code points — each emoji is a single non-`[a-zA-Z0-9]` character and is replaced with a single `-`. Resulting path length shrinks.
- The `re.sub` in `project_tmp_path` currently does NOT add any length cap — item #4 is a documentation test, not a fix test, unless Zie decides to add truncation.

**Out of Scope:**
- Truncating long project names in the implementation (decision deferred to Zie per audit finding).
- Testing the `name` parameter (first arg) for pathological values — the function is always called with short, controlled string literals in hook code.
- Filesystem write tests (those belong in integration tests).
