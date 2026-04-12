---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-knowledge-hash-in-implement.md
---

# Remove knowledge-hash Bang Injection from /implement Banner — Design Spec

**Problem:** `implement.md` runs `!python3 .../knowledge-hash.py --now` on every `/implement` invocation, adding subprocess overhead (rglob + hash across all project files) and ~50–100 tokens of hash output to the banner context. The hash value is a fingerprint — it conveys no actionable information. Drift detection is already handled by `session-resume.py` at session start via a fire-and-forget background subprocess.

**Approach:** Remove the single bang-injection line (line 15 of `implement.md`) that calls `knowledge-hash.py --now`. No replacement is needed — `session-resume.py` already runs `knowledge-hash.py --check` in the background at session start and surfaces drift warnings there. Add a structural test asserting the line is absent.

**Components:**
- `commands/implement.md` — remove line 15 (`!python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now ...`)
- `tests/unit/test_implement_md.py` — new structural test asserting `knowledge-hash` invocation is absent from `implement.md`

**Data Flow:**
1. Developer runs `/implement`
2. `implement.md` banner renders — no longer spawns `knowledge-hash.py --now`
3. Drift detection path unchanged: at session start, `session-resume.py` spawns `knowledge-hash.py --check` fire-and-forget in background (lines 142–154 of `session-resume.py`)
4. Drift warnings surface via `/status` or session-resume output, not in the `/implement` banner

**Edge Cases:**
- `knowledge-hash.py` script itself is not removed — session-resume still uses it
- If `knowledge-hash.py` is unavailable, the existing `|| echo "knowledge-hash: unavailable"` fallback becomes moot (line removed); session-resume already has its own exception guard for the drift check subprocess
- No config key change — this is a pure line removal

**Out of Scope:**
- Modifying or removing `knowledge-hash.py` itself
- Changing how `session-resume.py` runs drift detection
- Adding any replacement banner content for the hash line
- Changing `/status` drift visibility output
