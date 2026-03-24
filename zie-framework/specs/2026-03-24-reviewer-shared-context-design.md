---
approved: true
approved_at: 2026-03-24
backlog: backlog/reviewer-shared-context.md
---

# Reviewer Shared Context Bundle — Design Spec

**Problem:** All three reviewers independently read `zie-framework/decisions/*.md` and `zie-framework/project/context.md` on every invocation. In a spec→plan→implement session, the same static files are read 3 times with no changes between reads.

**Approach:** Load ADRs + context.md once in `/zie-plan` and `/zie-implement` before the reviewer loop, then pass the pre-loaded content as part of the reviewer invocation context. Each reviewer uses the same data but skips the disk reads. Backward-compatible: if the caller does not pass a bundle, reviewer falls back to reading from disk.

**Components:**
- Modify: `commands/zie-plan.md` — add upfront context load step (read `decisions/*.md` + `project/context.md`); pass loaded content when invoking plan-reviewer
- Modify: `commands/zie-implement.md` — same; pass bundle to impl-reviewer invocation
- Modify: `skills/spec-reviewer/SKILL.md` — accept pre-loaded context bundle; skip disk reads if bundle present; read from disk if bundle absent (fallback)
- Modify: `skills/plan-reviewer/SKILL.md` — same fallback pattern
- Modify: `skills/impl-reviewer/SKILL.md` — same fallback pattern

**Acceptance Criteria:**
- [ ] Context files loaded once per command session, not per reviewer invocation
- [ ] Reviewer receives pre-loaded ADR + context content from caller
- [ ] Reviewer skips disk reads when bundle is present
- [ ] Reviewer reads from disk when bundle is absent (backward-compatible fallback)
- [ ] Review output and behavior identical to today — no functional change

**Out of Scope:**
- Caching context across different sessions or features
- Sharing context between spec-reviewer invocations from different commands
