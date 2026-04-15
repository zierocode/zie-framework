---
tags: [feature]
---

# Lean Intent-SDLC Hook

## Problem

`intent-sdlc.py` has three token/IO waste issues:

1. **Short-message noise**: Messages under 15 chars that match no SDLC keyword still emit "unclear intent" additionalContext (~20-30 tokens each). Over a 50-message session, ~300-750 tokens wasted on "ok", "yes", "go" acknowledgments.

2. **Pattern-aggregate re-read**: Reads `/tmp/zie-{project}-pattern-aggregate` from disk on every UserPromptSubmit, even though this file only changes at session stop. Should use session-scoped caching or mtime check.

3. **Intent-dedup file write**: Writes the full context string to a temp file on every non-duplicate message. A simple in-memory hash comparison would eliminate the file I/O.

## Motivation

intent-sdlc.py fires on EVERY user message — it's the hottest path in the framework. Each unnecessary token or disk operation is multiplied by message count per session.

## Rough Scope

**In:**
- Short messages (<15 chars) with no SDLC keyword → exit silently, no additionalContext output
- Cache pattern-aggregate read with session-scoped mtime check (read once, skip if mtime unchanged)
- Replace file-write dedup with in-memory hash comparison (dedup dict stored in /tmp session file, read once per session)

**Out:**
- Changing intent detection regexes
- Changing SDLC command suggestions