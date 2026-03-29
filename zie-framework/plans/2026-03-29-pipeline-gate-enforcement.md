---
approved: true
approved_at: 2026-03-29
backlog: backlog/pipeline-gate-enforcement.md
spec: specs/2026-03-29-pipeline-gate-enforcement-design.md
---

# Pipeline Gate Enforcement — Implementation Plan

**Goal:** Make the SDLC pipeline an enforced gate, not a suggestion, by adding directive blocks to `intent-sdlc.py` for plan/implement intent and hardening `zie-plan.md` to always validate an approved spec exists.
**Architecture:** Two-layer enforcement. Layer 1 — `intent-sdlc.py` gains `_check_pipeline_preconditions(intent, roadmap_content, cwd)` which runs after intent detection and injects a `⛔ STOP.` directive block into `additionalContext` when preconditions fail. Layer 2 — `zie-plan.md` pre-flight removes the explicit-slug bypass and hard-stops whenever a spec is missing or unapproved. A positional-guidance path runs only when no gate was already triggered, injecting stage-aware nudges for known ROADMAP slugs.
**Tech Stack:** Python 3.x, pytest, stdlib only (`re`, `glob`, `pathlib`); Markdown command file edit

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/intent-sdlc.py` | Add `_check_pipeline_preconditions`, `_extract_roadmap_slugs`, `_positional_guidance`; wire into inner operations block |
| Modify | `commands/zie-plan.md` | Remove explicit-slug bypass; add spec-gate to all invocation paths |
| Modify | `tests/unit/test_hooks_intent_sdlc.py` | Add gate-specific test classes: plan-gate, implement-gate, positional-guidance, false-positive |

---

## Task 1: Add `_check_pipeline_preconditions` to `intent-sdlc.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `intent=plan` + slug in prompt matches a ROADMAP Next slug that has no `approved: true` spec → output contains `⛔ STOP.`
- `intent=plan` + slug matches a ROADMAP Next slug that has an approved spec → no `⛔ STOP.` injected
- `intent=plan` + no ROADMAP slug matched in prompt → no gate triggered (soft nudge only, existing behaviour)
- `intent=implement` + Now lane has at least one `[ ]` item → no gate triggered
- `intent=implement` + Now lane has zero `[ ]` items (empty or all `[x]`) → output contains `⛔ STOP.`
- `intent=implement` + Now lane missing entirely → output contains `⛔ STOP.`
- Gate logic returns `None` for any intent other than `plan`/`implement`
- `zie-framework/` directory missing → outer guard exits 0 (existing behaviour, unchanged)
- Multiple ROADMAP slugs in one prompt, any lacks approved spec → `⛔ STOP.` injected
- Feature name in prompt does not match any ROADMAP slug → no gate triggered

**Files:**
- Modify: `hooks/intent-sdlc.py`

### Step 1: Write failing tests (RED)

Add a new test class `TestPipelineGates` to the existing test file:

```python
# tests/unit/test_hooks_intent_sdlc.py — append class

class TestPipelineGates:
    """Gate enforcement: plan intent + no approved spec → ⛔; implement + no Now item → ⛔."""

    def _ctx(self, r):
        assert r.returncode == 0
        assert r.stdout.strip() != ""
        return json.loads(r.stdout)["additionalContext"]

    def _make_spec(self, specs_dir, slug, approved=True):
        specs_dir.mkdir(parents=True, exist_ok=True)
        content = f"---\napproved: {'true' if approved else 'false'}\n---\n# Spec\n"
        (specs_dir / f"2026-01-01-{slug}-design.md").write_text(content)

    # ── plan gate ──────────────────────────────────────────────────────────────

    def test_plan_intent_no_spec_blocks(self, tmp_path):
        """plan intent + ROADMAP slug + no spec → ⛔ STOP."""
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "let's plan my-feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx
        assert "my-feature" in ctx

    def test_plan_intent_approved_spec_passes(self, tmp_path):
        """plan intent + ROADMAP slug + approved spec → no gate."""
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        self._make_spec(cwd / "zie-framework" / "specs", "my-feature", approved=True)
        r = run_hook({"prompt": "let's plan my-feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" not in ctx

    def test_plan_intent_draft_spec_blocks(self, tmp_path):
        """plan intent + ROADMAP slug + approved: false spec → ⛔ STOP."""
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        self._make_spec(cwd / "zie-framework" / "specs", "my-feature", approved=False)
        r = run_hook({"prompt": "let's plan my-feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx

    def test_plan_intent_no_roadmap_slug_no_gate(self, tmp_path):
        """plan intent + no slug matched → no gate (ambiguous prompt)."""
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "ready to plan"}, tmp_cwd=cwd)
        # Should not emit ⛔
        ctx = self._ctx(r)
        assert "⛔" not in ctx

    def test_plan_intent_multiple_slugs_any_missing_blocks(self, tmp_path):
        """Multiple slugs: one approved, one missing → ⛔ for missing one."""
        roadmap = (
            "## Now\n\n"
            "## Next\n- [ ] feat-a — spec\n- [ ] feat-b — spec\n\n"
            "## Ready\n"
        )
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        # Only feat-a has an approved spec
        self._make_spec(cwd / "zie-framework" / "specs", "feat-a", approved=True)
        r = run_hook({"prompt": "plan feat-a and feat-b together"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx
        assert "feat-b" in ctx

    def test_plan_false_positive_generic_phrase(self, tmp_path):
        """'plan this design pattern' with no ROADMAP slug → no gate."""
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "plan this design pattern for our api"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" not in ctx

    # ── implement gate ─────────────────────────────────────────────────────────

    def test_implement_intent_no_now_item_blocks(self, tmp_path):
        """implement intent + empty Now lane → ⛔ STOP."""
        roadmap = "## Now\n\n## Next\n- [ ] my-feature — plan\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "let's start coding now"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx

    def test_implement_intent_all_done_now_blocks(self, tmp_path):
        """implement intent + Now lane has only [x] items → ⛔ STOP."""
        roadmap = "## Now\n- [x] my-feature — implement\n\n## Next\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "continue implementing"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" in ctx

    def test_implement_intent_active_now_passes(self, tmp_path):
        """implement intent + Now lane has [ ] item → no gate."""
        roadmap = "## Now\n- [ ] my-feature — implement\n\n## Next\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "let's implement the next task"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "⛔" not in ctx
```

Run: `make test-unit` — must FAIL (functions not yet implemented)

### Step 2: Implement (GREEN)

Add three helper functions to `hooks/intent-sdlc.py`, then wire them in.

**New helpers** — insert after the `STALE_THRESHOLD_SECS` constant and before `derive_stage`:

```python
def _extract_roadmap_slugs(roadmap_content: str) -> list[str]:
    """Return all kebab-case slugs from Next and Ready lane items in ROADMAP."""
    slugs = []
    in_target = False
    for line in roadmap_content.splitlines():
        if line.startswith("##") and any(
            s in line.lower() for s in ("next", "ready")
        ):
            in_target = True
            continue
        if line.startswith("##") and in_target:
            in_target = False
            continue
        if in_target and line.strip().startswith("- "):
            # Extract kebab-case tokens (min 3 chars, contain a hyphen)
            tokens = re.findall(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)+', line.lower())
            slugs.extend(tokens)
    return list(dict.fromkeys(slugs))  # deduplicate, preserve order


def _spec_approved(cwd: Path, slug: str) -> bool:
    """Return True if zie-framework/specs/*-<slug>-design.md has approved: true."""
    specs_dir = cwd / "zie-framework" / "specs"
    matches = list(specs_dir.glob(f"*-{slug}-design.md"))
    if not matches:
        return False
    try:
        content = matches[0].read_text()
        # frontmatter check: approved: true on its own line
        return bool(re.search(r'^approved:\s*true\s*$', content, re.MULTILINE))
    except Exception:
        return False


def _check_pipeline_preconditions(
    intent: str, roadmap_content: str, cwd: Path, message: str
) -> str | None:
    """Return a directive block string if preconditions fail, else None.

    plan intent: if a ROADMAP Next/Ready slug appears in the prompt and has no
    approved spec → block. If no slug matched → return None (ambiguous).
    implement intent: if Now lane has no [ ] item → block.
    All other intents: return None.
    """
    if intent == "plan":
        slugs = _extract_roadmap_slugs(roadmap_content)
        matched = [s for s in slugs if s in message]
        if not matched:
            return None  # ambiguous — no gate
        blocking = [s for s in matched if not _spec_approved(cwd, s)]
        if not blocking:
            return None
        slug_list = ", ".join(f"'{s}'" for s in blocking)
        return (
            f"⛔ STOP. No approved spec for {slug_list}. "
            f"You must run /zie-spec {blocking[0]} first. "
            f"Do not proceed with planning."
        )

    if intent == "implement":
        # Check Now lane for at least one [ ] item (raw lines, not cleaned)
        in_now = False
        has_open = False
        for line in roadmap_content.splitlines():
            if line.startswith("##") and "now" in line.lower():
                in_now = True
                continue
            if line.startswith("##") and in_now:
                break
            if in_now and re.search(r'-\s*\[\s*\]', line):
                has_open = True
                break
        if not has_open:
            return (
                "⛔ STOP. No active feature in Now lane. "
                "Complete /zie-backlog → /zie-spec → /zie-plan first, "
                "then start /zie-implement. Do not write code."
            )
        return None

    return None
```

**Positional guidance helper** — insert after `_check_pipeline_preconditions`:

```python
def _positional_guidance(roadmap_content: str, cwd: Path, message: str) -> str | None:
    """Return a stage-aware nudge for a known ROADMAP slug when no gate fired.

    Runs only when no dominant intent was detected or gate already fired — caller
    is responsible for not double-injecting.
    """
    slugs = _extract_roadmap_slugs(roadmap_content)
    matched = [s for s in slugs if s in message]
    if not matched:
        return None
    slug = matched[0]  # first match drives guidance
    has_approved_spec = _spec_approved(cwd, slug)
    # Check Ready lane
    in_ready = False
    in_now = False
    for line in roadmap_content.splitlines():
        if line.startswith("##") and "ready" in line.lower():
            in_ready = True
            continue
        if line.startswith("##") and "now" in line.lower():
            in_now = True
            continue
        if line.startswith("##") and (in_ready or in_now):
            in_ready = False
            in_now = False
    # Re-scan for slug presence in Ready / Now sections
    in_ready_section = False
    slug_in_ready = False
    for line in roadmap_content.splitlines():
        if line.startswith("##") and "ready" in line.lower():
            in_ready_section = True
            continue
        if line.startswith("##") and in_ready_section:
            break
        if in_ready_section and slug in line.lower():
            slug_in_ready = True
            break

    if not has_approved_spec:
        return f"Feature '{slug}' is in backlog. Start with /zie-spec {slug}"
    if has_approved_spec and not slug_in_ready:
        return f"Spec approved for '{slug}'. Run /zie-plan {slug}"
    if slug_in_ready:
        return f"Plan ready for '{slug}'. Run /zie-implement to start"
    return None
```

**Wire up in the inner operations block** — replace the `# ── Build combined context` block:

```python
    # ── Pipeline gate check ───────────────────────────────────────────────────
    gate_msg = None
    if best and best in ("plan", "implement"):
        gate_msg = _check_pipeline_preconditions(best, roadmap_content, cwd, message)

    # ── Positional guidance (only when no gate and no dominant intent) ────────
    guidance_msg = None
    if gate_msg is None and not intent_cmd:
        guidance_msg = _positional_guidance(roadmap_content, cwd, message)

    # ── Build combined context ────────────────────────────────────────────────
    parts = []
    if gate_msg:
        parts.append(gate_msg)
    elif intent_cmd:
        parts.append(f"intent:{best} → {intent_cmd}")
    if guidance_msg:
        parts.append(guidance_msg)
    parts.append(
        f"task:{active_task} | stage:{stage} | next:{suggested_cmd} | tests:{test_status}"
    )
    context = "[zie-framework] " + " | ".join(parts)

    print(json.dumps({"additionalContext": context}))
```

Run: `make test-unit` — must PASS

### Step 3: Refactor

- Verify `_extract_roadmap_slugs` deduplicates correctly; no state mutation.
- Verify `_spec_approved` catches `FileNotFoundError` via the outer `except Exception`.
- Ensure the wire-up block preserves the existing `scores`/`best` variable references — no regressions in `TestIntentSdlcHappyPath`.

Run: `make test-unit` — still PASS

---

## Task 2: Add `TestPositionalGuidance` test class

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Prompt contains a Next-lane slug with no spec → guidance nudge contains `/zie-spec`
- Prompt contains a slug with approved spec but not in Ready → nudge contains `/zie-plan`
- Prompt contains a slug already in Ready → nudge contains `/zie-implement`
- No ROADMAP slug in prompt → no guidance injected

**Files:**
- Modify: `tests/unit/test_hooks_intent_sdlc.py`

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_hooks_intent_sdlc.py — append class

class TestPositionalGuidance:
    """Positional guidance nudges when no dominant intent and slug matched."""

    def _ctx(self, r):
        assert r.returncode == 0
        assert r.stdout.strip() != ""
        return json.loads(r.stdout)["additionalContext"]

    def _make_spec(self, specs_dir, slug, approved=True):
        specs_dir.mkdir(parents=True, exist_ok=True)
        content = f"---\napproved: {'true' if approved else 'false'}\n---\n# Spec\n"
        (specs_dir / f"2026-01-01-{slug}-design.md").write_text(content)

    def test_no_spec_nudges_zie_spec(self, tmp_path):
        """Slug in Next with no spec → nudge to /zie-spec."""
        roadmap = "## Now\n\n## Next\n- [ ] cool-feature — backlog\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "what about cool-feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "/zie-spec" in ctx or "zie-spec" in ctx

    def test_approved_spec_no_ready_nudges_zie_plan(self, tmp_path):
        """Slug in Next with approved spec but not in Ready → nudge to /zie-plan."""
        roadmap = "## Now\n\n## Next\n- [ ] cool-feature — spec\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        self._make_spec(cwd / "zie-framework" / "specs", "cool-feature", approved=True)
        r = run_hook({"prompt": "what about cool-feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "/zie-plan" in ctx or "zie-plan" in ctx

    def test_slug_in_ready_nudges_zie_implement(self, tmp_path):
        """Slug in Ready → nudge to /zie-implement."""
        roadmap = (
            "## Now\n\n"
            "## Next\n\n"
            "## Ready\n- [ ] cool-feature — plan ✓\n"
        )
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        self._make_spec(cwd / "zie-framework" / "specs", "cool-feature", approved=True)
        r = run_hook({"prompt": "what about cool-feature"}, tmp_cwd=cwd)
        ctx = self._ctx(r)
        assert "/zie-implement" in ctx or "zie-implement" in ctx

    def test_no_slug_in_prompt_no_guidance(self, tmp_path):
        """Generic question with no ROADMAP slug → no guidance."""
        roadmap = "## Now\n\n## Next\n- [ ] cool-feature — backlog\n\n## Ready\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook({"prompt": "what should I do next"}, tmp_cwd=cwd)
        # May or may not produce output; if it does, no ⛔ and no feature-specific nudge
        if r.stdout.strip():
            ctx = json.loads(r.stdout)["additionalContext"]
            assert "cool-feature" not in ctx
```

Run: `make test-unit` — must FAIL

### Step 2: Implement (GREEN)

The `_positional_guidance` helper from Task 1 covers these cases. No additional implementation needed.

Run: `make test-unit` — must PASS

### Step 3: Refactor

- Confirm `_positional_guidance` is only called when `gate_msg is None and not intent_cmd` — no double-inject possible.

Run: `make test-unit` — still PASS

---

## Task 3: Harden `zie-plan.md` pre-flight gate

<!-- depends_on: none -->

**Acceptance Criteria:**
- `/zie-plan <slug>` with no spec file → prints `⛔ No spec found for '<slug>'. Run /zie-spec <slug> first.` and stops
- `/zie-plan <slug>` with spec file containing `approved: false` → prints `⛔ Spec exists but not approved. Complete /zie-spec <slug> review first.` and stops
- `/zie-plan <slug>` with approved spec → gate passes, proceeds to plan drafting
- `/zie-plan` (no args) path → existing no-args behaviour unchanged (shows list, already filters to approved-spec items)
- WIP check in Now lane → still runs before spec gate (order preserved)

**Files:**
- Modify: `commands/zie-plan.md`

### Step 1: Write failing tests (RED)

This task modifies a Markdown command file. There are no automated tests for command Markdown — the acceptance criteria are verified manually or via integration test. Document the manual verification steps:

```text
Manual verification checklist (run after Step 2):
1. Run /zie-plan my-feature (no spec file in zie-framework/specs/) →
   output must contain "⛔ No spec found for 'my-feature'"
2. Create zie-framework/specs/2026-01-01-my-feature-design.md with approved: false →
   run /zie-plan my-feature → output must contain "⛔ Spec exists but not approved"
3. Set approved: true in that spec file → run /zie-plan my-feature →
   proceeds to plan drafting normally
4. Run /zie-plan (no args) → still shows backlog list, filtered to approved specs
```

### Step 2: Implement (GREEN)

In `commands/zie-plan.md`, update the `## ร่าง plan สำหรับ slug ที่เลือก` section.

**Current behaviour (to remove):** the spec lookup is done only in the no-args flow; the explicit-slug path skips the spec gate.

**Change:** Add a spec-gate block at the top of the slug-handling flow (applies to both no-args selected slugs and explicit slug args). Insert the following block immediately before step 1 of `## ร่าง plan สำหรับ slug ที่เลือก`:

```markdown
## ตรวจสอบ spec ก่อน plan (ทุก slug)

For each resolved slug (whether from args or from no-args selection):

1. Glob `zie-framework/specs/*-<slug>-design.md`.
   - If no file found → print:
     `⛔ No spec found for '<slug>'. Run /zie-spec <slug> first.`
     STOP — do not proceed with this slug.
   - If file found → read frontmatter.
2. Check `approved: true` in frontmatter.
   - If `approved: false` or key absent → print:
     `⛔ Spec exists but not approved. Complete /zie-spec <slug> review first.`
     STOP — do not proceed with this slug.
   - If `approved: true` → gate passes, continue.
```

### Step 3: Refactor

- Confirm the no-args path still filters the display list to approved-spec items (existing behaviour) — the new gate is a redundant safety net for explicit-slug invocations where the user bypasses the list.
- Confirm the WIP check (Now lane warn) still runs before the spec gate.

---

## Task 4: Register `_extract_roadmap_slugs` and `_spec_approved` unit tests

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `_extract_roadmap_slugs` returns deduplicated kebab slugs from Next and Ready sections
- `_extract_roadmap_slugs` excludes single-word tokens and pure-number tokens
- `_extract_roadmap_slugs` ignores Now section slugs (Now lane is not a source)
- `_spec_approved` returns `True` when spec file has `approved: true` in frontmatter
- `_spec_approved` returns `False` when spec file missing
- `_spec_approved` returns `False` when spec file has `approved: false`
- `_spec_approved` returns `False` when frontmatter is malformed

**Files:**
- Modify: `tests/unit/test_hooks_intent_sdlc.py`

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_hooks_intent_sdlc.py — append class

import sys, os
REPO_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT_PATH, "hooks"))

# Import helpers directly for unit testing
# (import guarded — intent-sdlc.py top-level executes; use importlib trick)
import importlib.util, types

def _load_intent_sdlc_helpers():
    """Load only the helper functions from intent-sdlc.py without executing top-level."""
    path = os.path.join(REPO_ROOT_PATH, "hooks", "intent-sdlc.py")
    source = open(path).read()
    # Execute only function definitions (stop before outer guard block)
    stop_marker = "# ── Outer guard"
    idx = source.find(stop_marker)
    safe_src = source[:idx] if idx != -1 else source
    ns: dict = {}
    exec(compile(safe_src, path, "exec"), ns)  # noqa: S102
    return ns


class TestHelperFunctions:
    """Unit tests for _extract_roadmap_slugs and _spec_approved."""

    @classmethod
    def setup_class(cls):
        cls.helpers = _load_intent_sdlc_helpers()
        cls.extract = cls.helpers["_extract_roadmap_slugs"]
        cls.spec_approved = cls.helpers["_spec_approved"]

    def test_extract_slugs_from_next(self):
        content = "## Next\n- [ ] cool-feature — spec\n- [ ] auth-login — plan\n"
        slugs = self.extract(content)
        assert "cool-feature" in slugs
        assert "auth-login" in slugs

    def test_extract_slugs_from_ready(self):
        content = "## Ready\n- [ ] pipeline-gate — plan ✓\n"
        slugs = self.extract(content)
        assert "pipeline-gate" in slugs

    def test_extract_slugs_excludes_now(self):
        content = "## Now\n- [ ] now-feature — implement\n\n## Next\n- [ ] next-feature — spec\n"
        slugs = self.extract(content)
        assert "now-feature" not in slugs
        assert "next-feature" in slugs

    def test_extract_slugs_deduplicates(self):
        content = "## Next\n- [ ] cool-feature — spec\n- [ ] cool-feature — plan\n"
        slugs = self.extract(content)
        assert slugs.count("cool-feature") == 1

    def test_extract_slugs_ignores_single_words(self):
        content = "## Next\n- [ ] spec\n- [ ] plan\n"
        slugs = self.extract(content)
        # Single words without hyphens should not be returned
        assert "spec" not in slugs
        assert "plan" not in slugs

    def test_spec_approved_true(self, tmp_path):
        specs = tmp_path / "zie-framework" / "specs"
        specs.mkdir(parents=True)
        (specs / "2026-01-01-my-feat-design.md").write_text(
            "---\napproved: true\n---\n# Spec\n"
        )
        assert self.spec_approved(tmp_path, "my-feat") is True

    def test_spec_approved_false_flag(self, tmp_path):
        specs = tmp_path / "zie-framework" / "specs"
        specs.mkdir(parents=True)
        (specs / "2026-01-01-my-feat-design.md").write_text(
            "---\napproved: false\n---\n# Spec\n"
        )
        assert self.spec_approved(tmp_path, "my-feat") is False

    def test_spec_approved_missing_file(self, tmp_path):
        (tmp_path / "zie-framework" / "specs").mkdir(parents=True)
        assert self.spec_approved(tmp_path, "missing-feat") is False

    def test_spec_approved_no_specs_dir(self, tmp_path):
        (tmp_path / "zie-framework").mkdir(parents=True)
        assert self.spec_approved(tmp_path, "any-feat") is False
```

Run: `make test-unit` — must FAIL (helpers not importable yet at this path)

### Step 2: Implement (GREEN)

The helpers are added in Task 1. After Task 1 GREEN, these tests should pass automatically since the exec-based import loads from the same source file.

Run: `make test-unit` — must PASS

### Step 3: Refactor

- Confirm `_load_intent_sdlc_helpers` stops before the outer guard so no subprocess or stdin interaction is triggered during import.
- Verify `exec` call uses `compile()` for proper source attribution in tracebacks.

Run: `make test-unit` — still PASS

---

## Task 5: Final integration smoke-test and commit

<!-- depends_on: Task 1, Task 2, Task 3, Task 4 -->

**Acceptance Criteria:**
- `make test-unit` passes with zero failures
- `make test` passes (unit + md lint)
- No regression in `TestIntentSdlcHappyPath`, `TestIntentSdlcEarlyExit`, `TestIntentSdlcRoadmapCache`
- `commands/zie-plan.md` passes markdownlint

**Files:**
- No new files — verification only

### Step 1: Run full test suite

```bash
make test-unit
```

Expected: all tests pass, including new `TestPipelineGates`, `TestPositionalGuidance`, `TestHelperFunctions`.

```bash
make test
```

Expected: unit + md lint clean.

### Step 2: Commit

```bash
git add hooks/intent-sdlc.py \
  commands/zie-plan.md \
  tests/unit/test_hooks_intent_sdlc.py
git commit -m "feat: pipeline gate enforcement — spec-before-plan, plan-before-implement"
```

### Step 3: Verify no regressions

Re-run:

```bash
make test-unit
```

Expected: still all green.
