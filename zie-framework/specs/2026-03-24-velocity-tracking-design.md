---
approved: true
approved_at: 2026-03-24
backlog: backlog/velocity-tracking.md
---

# Velocity Tracking in /zie-status — Design Spec

**Problem:** `/zie-status` shows current state but gives no throughput signal. There is no way to know how fast features are shipping or whether workflow changes are having any effect.

**Approach:** Parse git tags (semver format) to derive release dates; compute days between consecutive releases for the last N releases (default 5); display as a single line in `/zie-status` output. No new files, commands, or external storage — data comes entirely from existing git history.

**Components:**
- Modify: `commands/zie-status.md` — add velocity section: run `git tag --sort=-version:refname` to get last N+1 semver tags, compute intervals, display as "Velocity (last N): Xd, Yd, Zd, ..." in the status output

**Acceptance Criteria:**
- [ ] `/zie-status` shows release intervals for the last 5 releases (configurable to N)
- [ ] Intervals computed from semver git tags only (ignores non-semver tags)
- [ ] Graceful output when <2 semver tags exist: "Velocity: not enough releases yet"
- [ ] No new files, commands, or external storage created
- [ ] One line added to `/zie-status` output — existing sections unchanged

**Out of Scope:**
- Per-stage timing breakdown
- External dashboards or metrics storage
- Velocity tracking in hooks or session-resume
