# Backlog: Add /chore, /hotfix, /spike intent patterns to intent-sdlc.py

**Problem:**
PATTERNS dict in intent-sdlc.py covers init/backlog/spec/plan/implement/fix/release/
retro/audit. The three off-pipeline tracks (/chore, /hotfix, /spike) appear only in
the suggestion string and are never detected from natural language. If a user says
"emergency fix for prod", the hook suggests /fix not /hotfix. If they say "let's
explore this idea", nothing matches spike.

**Motivation:**
Ambient intent guidance is partially blind to 3 valid workflow paths. Users relying
on the hook for guidance will be routed to the wrong commands in urgent situations
(hotfix vs fix distinction matters for release gating).

**Rough scope:**
- Add PATTERNS entries for:
  - `hotfix`: ["emergency", "prod down", "critical", "cannot wait", "urgent fix"]
  - `chore`: ["bump version", "update docs", "housekeeping", "maintenance"]
  - `spike`: ["explore", "investigate", "research", "prototype", "proof of concept"]
- Add corresponding next-command suggestions in the output
- Tests: "emergency fix" → hotfix intent detected; "let's explore" → spike detected
