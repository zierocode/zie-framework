---
approved: true
approved_at: 2026-04-04
backlog: backlog/fix-release-config-triple-read.md
---

# Fix Release Config Triple Read — Implementation Plan

**Goal:** Remove two redundant `.config` reads from `commands/release.md` by referencing the pre-bound `has_frontend`/`playwright_enabled` variables from pre-flight Step 2.
**Architecture:** Single-file markdown edit — no Python, no hooks, no tests required.

---

## Tasks

### Task 1 — Clarify pre-flight Step 2 binding

**Description:** Update Step 2 in `commands/release.md` to make the variable binding explicit.

**File:** `commands/release.md`

**Change:** Line ~13
- Before: `"อ่าน \`zie-framework/.config\` — ใช้ has_frontend, playwright_enabled เป็น context"`
- After: `"Read \`zie-framework/.config\` → bind \`has_frontend\`, \`playwright_enabled\` (reused by Gates 3–4)."`

**AC:**
- Pre-flight Step 2 reads config once and binds both fields explicitly.
- No second config read is issued before Gates 3–4.

---

### Task 2 — Remove inline read from Gate 3/5

**Description:** Gate 3/5 (E2E tests) reads `playwright_enabled` inline. Remove the read instruction and reference the pre-bound variable.

**File:** `commands/release.md`

**Change:** Line ~60
- Before: `"Read \`playwright_enabled\` from \`zie-framework/.config\` inline."`
- After: `"Check pre-bound \`playwright_enabled\` (from pre-flight Step 2)."`

**AC:**
- Gate 3/5 references the variable; no Read call to `.config`.

---

### Task 3 — Remove inline read from Gate 4/5

**Description:** Gate 4/5 (Visual check) reads both config fields inline. Remove the read instruction and reference the pre-bound variables.

**File:** `commands/release.md`

**Change:** Line ~73
- Before: `"Read \`has_frontend\` and \`playwright_enabled\` from \`zie-framework/.config\` inline."`
- After: `"Check pre-bound \`has_frontend\` and \`playwright_enabled\` (from pre-flight Step 2)."`

**AC:**
- Gate 4/5 references the variables; no Read call to `.config`.

---

### Task 4 — Run tests

**Description:** Verify no existing tests break.

```bash
make test-fast
```

**AC:** Exit 0. All existing release tests pass.
