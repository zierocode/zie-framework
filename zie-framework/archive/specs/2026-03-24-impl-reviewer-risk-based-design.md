---
approved: true
approved_at: 2026-03-24
backlog: backlog/impl-reviewer-risk-based.md
---

# impl-reviewer Risk-Based Invocation — Design Spec

**Problem:** `/zie-implement` invokes `impl-reviewer` after every task regardless of complexity, causing up to 24+ reviewer model calls on an 8-task plan. Simple tasks (add test, update docs, rename) get the same overhead as security-sensitive changes.

**Approach:** Classify task risk inline in `/zie-implement` immediately after the GREEN phase using two signals: (1) task description keywords and (2) files changed. High-risk tasks invoke the reviewer as today. Low-risk tasks skip the reviewer but still run `make test-unit`. A `<!-- review: required -->` annotation forces review regardless of classification.

**Components:**
- Modify: `commands/zie-implement.md` — add risk classification block after GREEN phase; define HIGH (new function/class, changed behavior, external API call, auth/file-IO/subprocess, `review: required` annotation) and LOW (test-only, docs/config, rename/reformat, minor field addition) categories; gate reviewer invocation on classification result.

**Acceptance Criteria:**
- [ ] Tasks classified LOW skip impl-reviewer; `make test-unit` still runs
- [ ] Tasks classified HIGH invoke impl-reviewer as before
- [ ] `<!-- review: required -->` in task description forces HIGH regardless of other signals
- [ ] Classification is based on task description keywords + files changed post-GREEN
- [ ] Reviewer logic, checklist, and output format unchanged

**Out of Scope:**
- Changing the reviewer logic itself
- Model selection for the reviewer (see model-haiku-fast-skills)
- Risk classification for spec-reviewer or plan-reviewer
