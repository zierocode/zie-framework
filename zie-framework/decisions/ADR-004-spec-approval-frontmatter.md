# ADR-004: Spec Approval State Tracked via Frontmatter

Date: 2026-03-23
Status: Accepted

## Context

/zie-plan needs to distinguish between specs that have passed the spec-reviewer
quality gate and specs that are just draft files. Before this decision, /zie-plan
checked only whether a matching spec file existed — it had no way to know if the
spec had been reviewed and approved.

This meant a partially-written or failing spec could slip through to the plan
stage without reviewer approval, defeating the purpose of the quality gate.

## Decision

After the spec-reviewer returns "APPROVED", `spec-design` prepends YAML
frontmatter to the spec file:

```yaml
---
approved: true
approved_at: YYYY-MM-DD
backlog: backlog/<slug>.md
---
```

/zie-plan filters the spec list by checking for `approved: true` in frontmatter.
Specs without this frontmatter are treated as drafts and excluded from the
plan-drafting flow.

## Consequences

**Positive:**

- The spec file itself carries its approval state — no external tracking needed.
- /zie-plan can reliably detect which specs are ready for planning.
- `approved_at` provides an audit trail with date.
- `backlog` link connects spec back to its origin backlog item.

**Negative:**

- Spec files now have mixed content (frontmatter + markdown body).
  Tools that render them must handle the YAML header.
- If a spec is edited after approval, the `approved: true` flag remains —
  users must manually update if a post-approval edit invalidates the review.
  Mitigation: /zie-spec Notes section warns about this.
