---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-parse-section-dedup.md
---

# parse_section() Deduplication — Design Spec

**Problem:** `hooks/session-resume.py` defines an inline `parse_section(text,
header)` function (lines 41–52) that nearly duplicates the logic of
`parse_roadmap_now()` in `utils.py`; the two implementations can diverge
silently.

**Approach:** Generalise `parse_roadmap_now()` into a
`parse_roadmap_section(roadmap_path, section_name)` function in `utils.py`,
then remove the inline `parse_section()` from `session-resume.py` and replace
all three calls (`parse_roadmap_now`, `parse_section("next")`,
`parse_section("done")`) with the new helper.

**Components:**

- `hooks/utils.py` — add `parse_roadmap_section()`, keep
  `parse_roadmap_now()` as a thin wrapper for backwards compatibility
- `hooks/session-resume.py` — remove inline `parse_section()`, update all
  three call sites
- `tests/test_utils.py` — add tests for `parse_roadmap_section` with
  "next" and "done" headers

**Data Flow:**

1. Add to `hooks/utils.py`:

   ```python
   def parse_roadmap_section(roadmap_path, section_name: str) -> list:
       """Extract cleaned items from a named ## section of ROADMAP.md.

       section_name is matched case-insensitively against ## headers.
       Returns [] if file missing, section absent, or section empty.
       """
       path = Path(roadmap_path)
       if not path.exists():
           return []
       lines = []
       in_section = False
       for line in path.read_text().splitlines():
           if line.startswith("##") and section_name.lower() in line.lower():
               in_section = True
               continue
           if line.startswith("##") and in_section:
               break
           if in_section and line.strip().startswith("- "):
               clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line.strip())
               clean = clean.lstrip("- ").lstrip("[ ]").lstrip("[x]").strip()
               if clean:
                   lines.append(clean)
       return lines
   ```

2. Update `parse_roadmap_now()` to delegate:

   ```python
   def parse_roadmap_now(roadmap_path) -> list:
       return parse_roadmap_section(roadmap_path, "now")
   ```

3. In `session-resume.py`:
   - Remove the inline `parse_section()` function (lines 41–52)
   - Remove the `roadmap_text` variable (no longer needed for section parsing)
   - Replace `parse_roadmap_now(roadmap_file)` → unchanged (still works via
     wrapper)
   - Replace `parse_section(roadmap_text, "next")` →
     `parse_roadmap_section(roadmap_file, "next")`
   - Replace `parse_section(roadmap_text, "done")` →
     `parse_roadmap_section(roadmap_file, "done")`
   - Add `parse_roadmap_section` to the `from utils import` line

4. Note: `roadmap_text` in `session-resume.py` is also used for the 200-line
   truncation before printing. That truncation logic stays unchanged; only the
   `parse_section` calls are replaced. The `roadmap_text` variable is retained
   for the print block, but `raw_lines` and `roadmap_text` construction can
   be limited to that purpose.

5. Run `make test-unit` — `test_utils.py` must pass; add tests for
   `parse_roadmap_section("next")` and `parse_roadmap_section("done")`.

**Edge Cases:**

- `parse_roadmap_now()` callers in other hooks (none currently) are unaffected
  because the wrapper preserves the existing signature
- Section names with mixed case in ROADMAP (e.g. `## Now`, `## NOW`) — handled
  by `.lower()` comparison already in both implementations
- Inline `parse_section` in `session-resume.py` does NOT strip link markdown
  or `[x]`/`[ ]` prefixes — the new helper does. This is a behaviour
  improvement: next/done items will be cleaned consistently with now items

**Out of Scope:**

- Changing the roadmap_text truncation logic
- Parsing sections from non-ROADMAP files
