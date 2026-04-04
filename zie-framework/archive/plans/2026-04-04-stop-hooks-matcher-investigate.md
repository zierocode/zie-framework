---
approved: true
approved_at: 2026-04-04
backlog: backlog/stop-hooks-matcher-investigate.md
spec: specs/2026-04-04-stop-hooks-matcher-investigate-design.md
---

# Stop Hook Matcher Support Investigation — Implementation Plan

**Goal:** Document the platform constraint (Stop events ignore matchers) in `hooks.json` so future maintainers do not re-investigate the same question.
**Architecture:** Single-file doc change — add a JSON comment key to the Stop section of `hooks.json`. No hook code changes, no tests required (doc-only).
**Tech Stack:** JSON (hooks.json)

---

## Investigation Outcome

| Branch | Description | Status |
| --- | --- | --- |
| A — matchers supported | Add `matcher` to stop-guard + compact-hint to gate to interactive sessions | **Closed** — not viable; matcher is silently ignored on Stop events |
| B — document constraint | Add comment key in hooks.json Stop section | **Active** — the only action needed |

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/hooks.json` | Add `_stop_matcher_note` comment key inside Stop entry |

---

## Task 1: Document constraint in hooks.json

**Acceptance Criteria:**
- `hooks.json` Stop section contains a `_stop_matcher_note` key with text explaining that Stop events do not support matchers and the `matcher` field is silently ignored by Claude Code
- `hooks.json` remains valid JSON
- `make lint` passes (no syntax error)

**Files:**
- Modify: `hooks/hooks.json`

---

- [ ] **Step 1: No failing tests needed**

  This is a documentation-only change. No behaviour changes, no new code paths. Verify JSON validity after edit:

  ```bash
  python3 -c "import json; json.load(open('hooks/hooks.json'))"
  ```

---

- [ ] **Step 2: Implement**

  In `hooks/hooks.json`, add a `_stop_matcher_note` key to the Stop entry (JSON "comment" convention used elsewhere in hooks.json via `_hook_output_protocol`):

  ```json
  "Stop": [
    {
      "_stop_matcher_note": "Stop events do not support matchers — the matcher field is silently ignored by Claude Code. All Stop hooks fire unconditionally on every session stop. Gate logic must live inside each hook (e.g. is_interrupt check, compact_hint_threshold). Investigated 2026-04-04.",
      "hooks": [
        ...
      ]
    }
  ]
  ```

  Run: `python3 -c "import json; json.load(open('hooks/hooks.json'))"` — must exit 0.

---

- [ ] **Step 3: Verify**

  ```bash
  make lint
  ```

  Must pass. No other changes needed.

---

## Future Watch

If a future Claude Code release adds matcher support for Stop events, the two hooks worth gating to interactive-only are:

1. `stop-guard.py` — spawns a git subprocess; skip on subagent/programmatic stops
2. `compact-hint.py` — reads context usage; only meaningful in interactive sessions

`session-learn.py` and `session-cleanup.py` run in background and are already low-overhead; gating them provides marginal benefit.

Matcher value to use when support arrives: `"interactive"` (exact token TBD — verify against Anthropic docs at that time).

---

**Commit:** `git add hooks/hooks.json && git commit -m "docs: stop-hooks-matcher-investigate — document Stop event matcher constraint in hooks.json"`
