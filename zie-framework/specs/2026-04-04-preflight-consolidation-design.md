# Preflight Consolidation — Design Spec

**Problem:** 13 commands each independently repeat the same 3–5 guard steps verbatim (~150 words each), totalling ~1,500+ words of duplicated boilerplate with no variation — creating a maintenance burden where every guard protocol change requires editing 10+ files.

**Approach:** Create a canonical `zie-framework/project/command-conventions.md` file that documents the standard pre-flight protocol. Replace the duplicated guard steps in 10 commands with a single reference line. Commands with genuinely custom pre-flight logic (init, implement, retro, release, sprint, chore, hotfix, spike) retain only their unique steps inline; the canonical 3-step guard (check `zie-framework/` exists, read `.config`, check ROADMAP Now lane) moves to the conventions doc. Update tests that assert specific guard text to match the new reference format.

**Components:**
- `zie-framework/project/command-conventions.md` — new file: canonical pre-flight protocol
- `commands/spec.md` — replace standard guard steps with reference line
- `commands/plan.md` — replace standard guard steps with reference line
- `commands/fix.md` — replace standard guard steps with reference line
- `commands/backlog.md` — replace standard guard steps with reference line
- `commands/resync.md` — replace standard guard steps with reference line
- `commands/chore.md` — retain custom slug-derive step; drop standard guard if duplicated
- `commands/hotfix.md` — retain custom slug-derive step; drop standard guard if duplicated
- `commands/spike.md` — retain custom slug-derive step; drop standard guard if duplicated
- `commands/implement.md` — has standard steps 1–2 (check zie-framework/ exists, check ROADMAP.md); replace those with reference line; retain unique live-context injection, agent-mode advisory, Ready-lane guard inline
- `commands/retro.md` — retain unique git-log injections
- `commands/release.md` — retain unique VERSION/branch/playwright config reads
- `commands/sprint.md` — retain unique lane-scan and branch check
- `commands/init.md` — retain unique git-repo check (no zie-framework/ dependency)
- `tests/unit/test_e2e_optimization.py` — update assertions referencing inline guard text
- `tests/unit/test_branding.py` — update if it asserts guard section presence by text
- `tests/unit/test_implement_preflight.py` — update if impacted
- `tests/unit/test_skills_bash_injection.py` — likely unaffected (tests injection position, not guard text)

**Data Flow:**
1. Author writes canonical 3-step guard to `command-conventions.md`
2. Each applicable command's `## ตรวจสอบก่อนเริ่ม` section is replaced with:
   `See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight).`
3. Commands with custom-only guards keep only their unique steps inline (no reference needed if no standard steps exist). Examples:
   - `spec.md`: `## ตรวจสอบก่อนเริ่ม` becomes just the reference line (its only pre-flight is the standard 3-step guard)
   - `chore.md`: keeps its unique slug-derive step inline; replaces only the duplicate standard steps with the reference line
   - `implement.md`: reference line for steps 1–2 (zie-framework/ check + ROADMAP check), then inline: agent-mode advisory, Ready-lane guard, WIP check, uncommitted work warn
4. Tests that assert inline guard text (e.g. `grep("zie-framework/", content)` for guard presence) are updated to assert the reference line instead: `assert "command-conventions.md" in content` or `assert "Pre-flight standard" in content`
5. No runtime behavior change — commands still instruct Claude to perform the same guard steps via the referenced doc

**Edge Cases:**
- `init.md` — must NOT reference the conventions doc (its guard runs before `zie-framework/` exists); keep its git-repo check fully inline
- `implement.md` — has standard steps 1–2; replace with reference line, keep custom live-context + agent-mode advisory + Ready-lane guard inline
- `retro.md` — has no standard 3-step guard; only git-log injections; no change needed
- `release.md` — has extended guard (VERSION, branch, playwright); only the `zie-framework/` exists step is standard; de-duplicate that one step, keep rest inline
- `sprint.md` — has extended guard with branch/WIP checks beyond the standard 3; de-duplicate only the standard steps
- `backlog.md` — only has 2 standard steps (no ROADMAP WIP check); reference doc covers both; memory recall step stays inline
- Tests asserting `≤ 3 items` in backlog pre-flight (`test_e2e_optimization.py`) — reference line counts as 1 item, so constraint is still met

**Out of Scope:**
- Changing the actual guard logic or adding new guard steps
- Modifying hook behavior
- Touching non-command files (skills, templates, hooks)
- Runtime enforcement (guards remain advisory prose, not executed code)
- Changing the Thai section heading `## ตรวจสอบก่อนเริ่ม` — keep it in every command for structural consistency
