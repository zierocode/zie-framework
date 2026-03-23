---
approved: true
approved_at: 2026-03-23
backlog: backlog/audit-docs-standards.md
spec: specs/2026-03-23-audit-docs-standards-design.md
---

# Plan: Docs + Standards Sprint

**Spec:** specs/2026-03-23-audit-docs-standards-design.md
**Effort:** S
**Test runner:** pytest

## Tasks

### Task 1 — Fix plugin.json version + add Makefile sync-version target

**RED:** Write a test that asserts `.claude-plugin/plugin.json` version equals
the content of `VERSION`. Use `json.load` + `open("VERSION").read().strip()`.
Confirm it fails against current state (`plugin.json` = 1.3.0, `VERSION` =
1.4.0).

Also write a test that asserts the Makefile contains a `sync-version:` target
definition.

**GREEN:**
- Edit `.claude-plugin/plugin.json`: set `"version": "1.4.0"`.
- Add `sync-version` target to `Makefile`:

```makefile
sync-version: ## Sync plugin.json version to match VERSION
	jq --arg v "$$(cat VERSION)" '.version = $$v' .claude-plugin/plugin.json \
	  > .claude-plugin/plugin.json.tmp \
	  && mv .claude-plugin/plugin.json.tmp .claude-plugin/plugin.json
	@echo "plugin.json version synced to $$(cat VERSION)"
```

- Update the existing `release` target comment to reference `sync-version`
  so future maintainers know the relationship.

**REFACTOR:** Run `jq -r .version .claude-plugin/plugin.json` — confirm
output is `1.4.0`. Run `make sync-version` — confirm idempotent (no change).
Run tests — both assertions pass.

---

### Task 2 — Add pre-commit version drift check

**RED:** Write a test that asserts `.githooks/pre-commit` exists and its
content contains the string `make sync-version` and exits non-zero on version
mismatch. Also assert `make setup` wires `core.hooksPath` (already present in
Makefile — confirm test reads Makefile for `core.hooksPath .githooks`).

**GREEN:** Create `.githooks/pre-commit`:

```sh
#!/bin/sh
plugin_ver=$(jq -r .version .claude-plugin/plugin.json 2>/dev/null)
version_ver=$(cat VERSION 2>/dev/null)
if [ "$plugin_ver" != "$version_ver" ]; then
  echo "Version drift: plugin.json=$plugin_ver vs VERSION=$version_ver"
  echo "Run: make sync-version"
  exit 1
fi
```

Set executable: `chmod +x .githooks/pre-commit`.

**REFACTOR:** Manually test: temporarily set `plugin.json` version to `0.0.0`,
run `.githooks/pre-commit` — confirm non-zero exit and error message. Restore.
Run tests — pass. Confirm `make setup` still works (already sets
`core.hooksPath .githooks`).

---

### Task 3 — Fix README.md decisions.md → context.md

**RED:** Write a test that opens `README.md`, reads all lines, and asserts:
1. No line contains the string `decisions.md`.
2. At least one line contains `project/context.md`.

Confirm the test currently fails (line 87 still reads `decisions.md`).

**GREEN:** Edit `README.md` line 87: replace `decisions.md` with `context.md`.

**REFACTOR:** Run `grep -n "decisions.md" README.md` — must return no matches.
Run `grep -n "context.md" README.md` — must find the corrected line. Run
tests — pass.

---

### Task 4 — Update architecture.md timestamp + version summary

**RED:** Write a test that opens `zie-framework/project/architecture.md` and
asserts:
1. The "Last updated" line contains `2026-03-23`.
2. The file body contains the string `v1.3.0`.
3. The file body contains the string `v1.4.0`.

Confirm the test currently fails (timestamp is `2026-03-22`, no version
summary present).

**GREEN:** Edit `zie-framework/project/architecture.md`:
- Change `**Last updated:** 2026-03-22` to `**Last updated:** 2026-03-23`.
- Add a "Version History Summary" section after the Overview block:

```markdown
## Version History Summary

- **v1.3.0** (2026-03-23) — 6-stage SDLC pipeline; `project/context.md`
  renamed from `decisions.md`; reviewer context bundles; quick spec mode;
  hybrid release via `make release`.
- **v1.4.0** (2026-03-23) — `/zie-audit` 9-dimension audit command with
  external research; `research_profile` dynamic intelligence layer; intent-detect
  skip command content.
```

**REFACTOR:** Read the file back — confirm timestamp and both version strings
are present. Run tests — pass.

---

### Task 5 — Canonicalize ADR numbering in context.md

**RED:** Write a test that opens `zie-framework/project/context.md` and asserts
no line matches the pattern `^## D-\d+` (i.e., no `D-` prefixed section
headers remain). Also assert that the headers `ADR-001` through `ADR-010` (or
whatever range covers all entries) are all present using `ADR-` prefix.

Confirm the test currently fails — `context.md` has `D-001` through `D-010`
prefixed headers.

**GREEN:** Edit `zie-framework/project/context.md`: replace all `## D-NNN`
section headers with `## ADR-NNN`, preserving the number. Specifically:
`D-001` → `ADR-001`, `D-002` → `ADR-002`, `D-003` → `ADR-003`, `D-004` →
`ADR-004`, `D-005` → `ADR-005`, `D-006` → `ADR-006`, `D-007` → `ADR-007`,
`D-008` → `ADR-008`, `D-009` → `ADR-009`, `D-010` → `ADR-010`.

**REFACTOR:** Run `grep "^## D-" zie-framework/project/context.md` — must
return no matches. Run `grep "^## ADR-" zie-framework/project/context.md` —
must list all entries. Run tests — pass.

---

### Task 6 — Translate CHANGELOG v1.1.0 section to English

**RED:** Write a test that parses `CHANGELOG.md`, extracts the `v1.1.0`
section (lines between `## v1.1.0` and the next `## v`), and asserts no Thai
Unicode characters are present in that block. Use a regex or `ord(c) > 0x0E00
and ord(c) < 0x0E80` to detect Thai script.

Confirm the test currently fails — the v1.1.0 section contains Thai text.

**GREEN:** Edit `CHANGELOG.md` — replace the entire `v1.1.0` section body with
an English translation:

```markdown
## v1.1.0 — 2026-03-22

### Features

- **Knowledge Architecture** — Every project using zie-framework gets
  `PROJECT.md` (hub) and `project/architecture.md`, `project/components.md`,
  `project/decisions.md` (spokes), auto-generated by `/zie-init` from
  templates — no manual setup required.
- **Project Decisions log** — Records architectural decisions as an
  append-only log with status (Accepted / Superseded). `/zie-retro` syncs
  entries to brain automatically.

### Changed

- **Commands redesigned** — All `/zie-*` commands and skills use
  intent-driven language; phases renamed (e.g., "Write the failing test first
  (RED)").
- **Batch release support** — `[x]` items in the Now lane accumulate pending
  release. `/zie-ship` moves them to Done with a version tag — no need to
  ship features individually.
- **Intent-driven steps** — RED/GREEN/REFACTOR in `/zie-build` are short
  paragraphs instead of bullet micro-steps; config reads collapsed to one
  line.
- **Version bump suggestion** — `/zie-ship` analyzes the Now lane and git log
  then suggests major/minor/patch with reasoning before confirmation.
- **Human-readable CHANGELOG** — `/zie-ship` drafts the CHANGELOG entry for
  approval before committing.

### Tests

- 165 unit tests covering commands, skills, hooks, and templates (pytest).
```

**REFACTOR:** Run the Thai-detection test — zero Thai characters in the
v1.1.0 block. Eyeball the section for translation accuracy. Run full tests —
pass.

---

### Task 7 — Add SECURITY.md

**RED:** Write a test that asserts `SECURITY.md` exists at the repo root and
its content contains all three required elements: a vulnerability reporting
method (assert string `report` or `Report`), a maintainer contact (assert
string `contact` or `Contact` or `maintainer`), and a disclosure policy
(assert string `90` or `embargo` or `responsible disclosure`).

Confirm the test currently fails — `SECURITY.md` does not exist.

**GREEN:** Create `SECURITY.md` at the repo root:

```markdown
# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 1.4.x   | Yes       |
| < 1.4   | No        |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

To report a vulnerability, contact the maintainer directly:

- **Contact:** Open a private GitHub Security Advisory at
  `https://github.com/zierocode/zie-framework/security/advisories/new`
- **Email fallback:** Include "SECURITY" in the subject line.

Please include: a description of the issue, reproduction steps, affected
versions, and potential impact.

## Disclosure Policy

This project follows **responsible disclosure**:

1. Report the vulnerability privately.
2. The maintainer will acknowledge receipt within 7 days.
3. A fix will be developed and released within **90 days** of the report.
4. After the fix is released (or the 90-day embargo expires), the reporter
   may disclose the vulnerability publicly.

Coordinated disclosure is appreciated. Credit will be given in the release
notes unless the reporter prefers to remain anonymous.
```

**REFACTOR:** Confirm `SECURITY.md` exists at repo root. Run the test — all
three assertions pass. Check that `lint-md` passes on the new file (`make
lint-md`).

---

### Task 8 — Add .cz.toml commitizen config

**RED:** Write a test that asserts `.cz.toml` exists at the repo root and its
content contains `[tool.commitizen]`, the string `conventional_commits`, and
at least the commit types `feat`, `fix`, and `chore`.

Confirm the test currently fails — `.cz.toml` does not exist.

**GREEN:** Create `.cz.toml` at the repo root:

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "1.4.0"
version_files = [
    "VERSION",
    ".claude-plugin/plugin.json:\"version\""
]
tag_format = "v$version"
update_changelog_on_bump = true
changelog_file = "CHANGELOG.md"
changelog_incremental = true

[tool.commitizen.customize]
schema_pattern = "(feat|fix|chore|docs|refactor|test|ci|perf|revert)(\\(.+\\))?(!)?: .+"
commit_parser = "cz_conventional_commits"

[[tool.commitizen.customize.questions]]
type = "list"
name = "prefix"
message = "Select the type of change"
choices = [
    {value = "feat",     name = "feat:     A new feature"},
    {value = "fix",      name = "fix:      A bug fix"},
    {value = "chore",    name = "chore:    Maintenance, no production code change"},
    {value = "docs",     name = "docs:     Documentation changes only"},
    {value = "refactor", name = "refactor: Code restructure, no feature/bug change"},
    {value = "test",     name = "test:     Add or update tests"},
    {value = "ci",       name = "ci:       CI/CD pipeline changes"},
    {value = "perf",     name = "perf:     Performance improvement"},
    {value = "revert",   name = "revert:   Revert a previous commit"}
]
```

**REFACTOR:** Run the test — all assertions pass. Optionally run `cz info` if
commitizen is installed to confirm config loads without error. Verify `.cz.toml`
passes `lint-md` (N/A — not a markdown file).
