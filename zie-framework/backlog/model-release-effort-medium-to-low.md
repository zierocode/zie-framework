# Backlog: Drop /release effort medium → low (haiku doesn't benefit from medium)

**Problem:**
/release uses `model: haiku` + `effort: medium`. haiku at medium effort gains little
from the extended token budget — the model's ceiling is the bottleneck, not effort.
The release flow is a checklist: run gates, bump version, write changelog, commit.
Two steps have "model: sonnet reasoning" comments inline (version suggestion,
changelog narrative) but the command-level effort setting applies to haiku, not sonnet.

**Motivation:**
medium effort on haiku wastes token budget on a model that can't use it effectively.
haiku+low runs the same checklist at lower cost. The judgment-heavy steps (semver
suggestion, changelog) are mechanical enough for haiku+low to handle correctly.

**Rough scope:**
- Change `effort: medium` → `effort: low` in commands/release.md frontmatter
- Tests: frontmatter lint; verify release still produces correct semver + changelog
