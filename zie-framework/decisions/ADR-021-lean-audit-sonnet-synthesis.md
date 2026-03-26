# ADR-021: zie-audit Downgraded from Opus/5-agents to Sonnet/3-agents + Synthesis Pass

Date: 2026-03-27
Status: Accepted
Supersedes: ADR-012 (Tiered Model Routing — Opus reservation for zie-audit)

## Context

ADR-012 reserved `model: opus, effort: high` exclusively for zie-audit on the basis that
9-dimension codebase analysis + 15+ WebSearch queries + parallel agent cross-referencing
was the most cognitively demanding task in the framework, and that audit quality directly
determines backlog priorities.

Since ADR-012 (2026-03-24), two things changed:

1. **Sonnet 4.6 capability:** Claude Sonnet 4.6 is substantially stronger than the Sonnet
   version available when ADR-012 was written. Pattern-match auditing (detecting dead code,
   shell injection patterns, stale docs, coupling violations) is within Sonnet 4.6's
   reliable capability range.

2. **Architecture redesign:** The audit architecture changes from 5 Opus agents doing
   independent full-codebase scans to 3 Sonnet agents with consolidated dimensions + 1
   explicit Sonnet synthesis pass. The synthesis pass assumes the cross-referencing and
   deduplication role that ADR-012 relied on Opus's reasoning depth to handle implicitly.

The combined cost of `5 × Opus × ~40K tokens + 25 WebSearch` was 50K–200K tokens per
audit run — potentially 50% of monthly credit budget for a single invocation. This made
zie-audit economically impractical to run with any frequency.

## Decision

Change zie-audit to `model: sonnet, effort: medium` for all agents (3 dimension agents +
1 synthesis agent). Consolidate 5 audit dimensions into 3:

- **Security** (unchanged — scope preserved)
- **Code Health** (Lean/Efficiency + Quality/Testing merged)
- **Structural** (Documentation + Architecture merged)
- **Synthesis** (new — aggregates, deduplicates, scores, and flags coverage gaps)

Reduce WebSearch cap from 25 to 15 targeted queries (5 per dimension agent, 0 for synthesis).

Update `test_model_effort_frontmatter.py` EXPECTED map: move zie-audit from opus tier to
sonnet tier.

## Consequences

**Positive:**
- Cost reduction: ~200K tokens → ~55K tokens per audit run (↓72%)
- zie-audit becomes economically viable to run weekly rather than quarterly
- Synthesis pass makes cross-referencing explicit rather than implicit in model reasoning
- 3-agent architecture is easier to maintain and tune than 5-agent

**Negative:**
- Opus's deeper reasoning may catch edge-case findings that Sonnet misses
- First run after this change should be validated against a prior Opus audit for finding
  quality regression

**Neutral:**
- The synthesis pass adds one additional agent invocation, partially offsetting 5→3 savings
- Security dimension is unchanged in scope — highest-priority findings not affected
- ADR-012's tier philosophy (haiku/sonnet/opus) remains valid for all other commands
