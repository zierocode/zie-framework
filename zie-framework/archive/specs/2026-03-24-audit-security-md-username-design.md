---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-security-md-username.md
---

# SECURITY.md Hardcoded Username — Design Spec

**Problem:** `SECURITY.md` line 17 contains a hardcoded GitHub URL using the
`zierocode` username; if the repo moves or is forked, the security advisory
link points to the wrong place.

**Approach:** Replace the hardcoded URL with the GitHub-standard relative
security advisory path pattern using the repository slug from `plugin.json`,
or use a more stable canonical form. Since this is a security reporting URL
that must be actionable (not a relative path), keep it absolute but use the
canonical repo slug from `.claude-plugin/plugin.json`.

**Components:**

- `SECURITY.md` — update advisory URL on line 17
- `tests/test_docs_standards.py` — update the SECURITY.md URL assertion if
  one exists

**Data Flow:**

1. Read `.claude-plugin/plugin.json` to confirm the canonical repository slug.
   Current value: `zierocode/zie-framework`.

2. The current URL in `SECURITY.md` line 17:

   ```
   https://github.com/zierocode/zie-framework/security/advisories/new
   ```

   This is in fact already the correct canonical URL. The finding is that the
   username is hardcoded rather than derived from configuration.

3. No URL change is needed for the canonical repo. The fix is documentation:
   add a comment in `SECURITY.md` noting the URL is intentionally tied to the
   canonical upstream repo, and that forks should update it:

   Add a note under the Contact line:

   ```markdown
   - **Contact:** Open a private GitHub Security Advisory at
     `https://github.com/zierocode/zie-framework/security/advisories/new`
     *(forks: replace with your repository path)*
   ```

4. Update `tests/test_docs_standards.py` SECURITY.md test if it asserts the
   exact URL without the fork note.

**Edge Cases:**

- GitHub does not support relative advisory URLs — the absolute form is
  required for security researchers to click through
- If the repo is forked, the fork owner must update this line manually; the
  note makes that obligation explicit

**Out of Scope:**

- Auto-deriving the URL from git remote at build time
- A CODEOWNERS file (separate concern)
