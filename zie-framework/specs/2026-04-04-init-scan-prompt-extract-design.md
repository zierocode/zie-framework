# init-scan-prompt-extract — Design Spec

**Problem:** `commands/init.md` embeds a ~400-word Explore agent prompt inline (lines 68–115), making the command hard to read and the prompt difficult to iterate on independently; two other prose-heavy sections (re-run guard ~80 words, Makefile negotiation ~120 words) add further bloat.

**Approach:** Extract the self-contained agent prompt block to `templates/init-scan-prompt.md` and reference it with a single line in `init.md`. Compress the re-run guard and Makefile negotiation sections to tighter checklists. No logic changes — only structure and prose density.

**Components:**
- `commands/init.md` — remove inline prompt block; add reference line; compress re-run guard + Makefile sections
- `templates/init-scan-prompt.md` — new file containing the verbatim Explore agent prompt
- `tests/test_commands_zie_init.py` — verify all existing assertions still pass post-edit

**Data Flow:**
1. `/init` is invoked by Claude
2. Claude reads `commands/init.md` and encounters the reference line `Prompt: see templates/init-scan-prompt.md`
3. Claude reads `templates/init-scan-prompt.md` and passes the prompt verbatim to `Agent(subagent_type=Explore)`
4. Downstream behaviour is identical to today — only the source location of the prompt changes

**Edge Cases:**
- Template file missing at runtime → Claude surfaces a clear error ("templates/init-scan-prompt.md not found") rather than silently sending a blank prompt
- Test assertions that grep for strings inside the extracted block must target `templates/init-scan-prompt.md` not `commands/init.md` — verify no existing test does this before extraction

**Out of Scope:**
- Changing prompt content or agent behaviour
- Compressing any section beyond the re-run guard and Makefile negotiation blocks
- Migrating other commands to a template-reference pattern
- Automated template loading infrastructure (no new hook or loader)
