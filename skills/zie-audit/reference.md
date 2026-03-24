# zie-audit — Reference Material

Supporting file for `skills/zie-audit/SKILL.md`. Read via
`${CLAUDE_SKILL_DIR}/reference.md` during the audit. Never auto-injected.

---

## Dimension Definitions

| Dimension | What it covers |
| --- | --- |
| Security | Secrets, injection, input validation, auth/authz, error leakage, CVE hints |
| Lean | Dead code, duplicated logic, over-engineering, unnecessary dependencies |
| Quality | Test coverage, fragile tests, weak assertions, edge-case gaps, TODO/FIXME debt |
| Docs | Stale references, missing docs, broken examples, README completeness, CHANGELOG sync |
| Architecture | Coupling, SRP violations, inconsistent patterns, silent failures |
| Performance | Hot-path I/O, caching gaps, blocking operations, N+1 query patterns |
| Dependencies | Outdated packages, license compatibility, abandoned libraries |
| Developer Exp | Output clarity, error messages, onboarding friction, local setup steps |
| Standards | semver, conventional commits, OpenSSF scorecard, SLSA supply chain levels |

---

## Scoring Rubric

Each dimension starts at **100**.

| Severity | Score deduction per finding |
| --- | --- |
| Critical | −15 |
| High | −8 |
| Medium | −3 |
| Low | −1 |

Floor: 0 (a dimension cannot go below 0).

**Overall score** = weighted average across all active dimensions (equal weight
unless `--focus` is used, in which case only the focused dimension is scored).

**Severity bump rule:** a finding present in both the internal scan (Phase 2)
and an external standard (Phase 3) is bumped one severity level upward
(Low → Medium → High → Critical). This reflects external validation confidence.

---

## Query Template Library

Build the Phase 3 query list dynamically from `research_profile`. Templates:

### Language / Runtime

```text
"{lang} best practices 2026"
"{lang} security vulnerabilities checklist"
```

### Framework-Specific

```text
"{fw} security guide"
"{fw} performance anti-patterns"
```

### Domain-Specific

| Domain / Context | Queries to add |
| --- | --- |
| `claude-code-plugin` | "claude code plugin development best practices", "claude code hooks security patterns" |
| `public-api` in special_ctx | "REST API design standards OpenAPI 2026" |
| `handles-payments` in special_ctx | "PCI DSS compliance checklist developer" |
| `processes-pii` in special_ctx | "GDPR technical implementation checklist" |

### OSS + Supply Chain (always included)

```text
"OpenSSF best practices scorecard criteria"
"SLSA supply chain security levels"
"{project_type} github stars:>100 architecture patterns"
```

**Cap:** 15 queries total. Prioritise language + framework + domain queries.
Drop OSS/supply-chain queries last if over cap.

---

## Finding Format

Each finding from Phase 2 agents:

```python
{
  "severity": "Critical|High|Medium|Low",
  "dimension": "<dimension name>",
  "description": "<specific issue — what and where>",
  "location": "<file:line or module>",
  "effort": "XS|S|M|L"
}
```

Each finding from Phase 3 external research:

```python
{
  "standard": "<standard name, e.g. OpenSSF>",
  "finding": "<gap description>",
  "severity": "Critical|High|Medium|Low"
}
```
