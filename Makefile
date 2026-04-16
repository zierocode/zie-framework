VERSION    := $(shell cat VERSION 2>/dev/null || echo "0.1.0")
ENV        ?= dev
PROJECT_MD ?= zie-framework/PROJECT.md

# ── Help ──────────────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help
help:
	@grep -E '^[a-zA-Z][a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Tests ─────────────────────────────────────────────────────────────────────
test-fast: ## Fast TDD feedback — runs pytest on changed files only (+ --lf)
	bash scripts/test_fast.sh

# test-ci mirrors test-unit body for independent evolvability (CI alias)
test-ci: ## Full test suite with coverage gate — use before commit and in CI
	python3 -m coverage erase
	COVERAGE_PROCESS_START=$(CURDIR)/.coveragerc \
	    python3 -m pytest tests/ -x -q --tb=short --no-header -m "not integration"
	python3 -m coverage combine 2>/dev/null || true
	python3 -m coverage report --show-missing --fail-under=48
	@pytest --collect-only -q -m error_path tests/unit/ 2>/dev/null \
		| python3 tests/unit/scripts/check_error_path_coverage.py

test-unit: ## Fast unit tests with subprocess coverage measurement
	# REQUIRES: sitecustomize.py in venv for subprocess hook coverage.
	# Without it, subprocess-spawned hooks show 0%. Run 'make coverage-smoke' to verify.
	python3 -m coverage erase
	COVERAGE_PROCESS_START=$(CURDIR)/.coveragerc \
	    python3 -m pytest tests/ -x -q --tb=short --no-header -m "not integration"
	python3 -m coverage combine 2>/dev/null || true
	python3 -m coverage report --show-missing --fail-under=48
	@pytest --collect-only -q -m error_path tests/unit/ 2>/dev/null \
		| python3 tests/unit/scripts/check_error_path_coverage.py

coverage-smoke: ## Verify ≥1 hook has >0% line coverage (requires sitecustomize.py in venv)
	@python3 -m coverage report 2>/dev/null | grep -E 'hooks/[^ ]+.*[1-9][0-9]*%' > /dev/null || \
		(echo "ERROR: No hooks show >0% coverage. Ensure sitecustomize.py is in venv (see .coveragerc)" && exit 1)
	@echo "[zie-framework] Coverage smoke passed — at least one hook has measurable coverage"

test-int: ## Integration tests (hook event simulation)
	python3 -m pytest tests/ -v -m "integration" --tb=short

check-claudemd-lines: ## Assert CLAUDE.md ≤87 lines
	@python3 -c "import sys; lines=open('CLAUDE.md').readlines(); n=len(lines); sys.exit(1) if n > 87 else print(f'CLAUDE.md: {n} lines (OK)')"

lint: lint-bandit check-claudemd-lines ## Run all lint checks (ruff + bandit + claudemd line count)
	ruff check .

lint-fix: ## Auto-fix safe ruff violations
	ruff check . --fix

lint-md: ## Lint all Markdown files (markdownlint, no exceptions)
	npx markdownlint-cli "**/*.md" --ignore node_modules

test: test-unit test-int lint-md ## Full test suite (unit + integration + md lint)

# ── Environments ──────────────────────────────────────────────────────────────
start:  _start-$(ENV)  ## Start environment (usage: make start ENV=dev)
stop:   _stop-$(ENV)   ## Stop environment
deploy: _deploy-$(ENV) ## Deploy to environment (usage: make deploy ENV=prod)

_start-%:
	@echo "No _start-$* defined. Add it to Makefile.local"
_stop-%:
	@echo "No _stop-$* defined. Add it to Makefile.local"
_deploy-%:
	@echo "No _deploy-$* defined. Add it to Makefile.local"

# ── Git workflow ──────────────────────────────────────────────────────────────
push: ## Commit + push to dev branch (usage: make push m="commit message")
	@test -n "$(m)" || (echo "Usage: make push m='commit message'" && exit 1)
	git add -A && git commit -m "$(m)" && git push origin dev

ship: ## Run tests then prompt for /zie-release
	$(MAKE) test || (echo "Tests failed — fix before shipping" && exit 1)
	@echo "All tests passed. Run /zie-release for the full release gate."

# ── Implement / Release ───────────────────────────────────────────────────────
zie-implement: ## Run /implement in a fresh agent context — processes Now lane item (usage: make zie-implement)
	claude --agent zie-framework:builder

implement-local: ## Run /implement in current session (no --agent, works on non-Claude providers)
	@echo "[zie-framework] Running /implement in current session (no agent mode)"
	@echo "[zie-framework] On Claude Code, prefer: make zie-implement"

release-local: ## Run /release directly in current session (non-Claude fallback)
	@echo "[zie-framework] Use: /release"
	@echo "[zie-framework] Do NOT use 'make zie-release' on non-Claude providers."

zie-release: ## Run /release in a fresh agent context — avoids context overflow (usage: make zie-release)
	claude --agent zie-framework:shipper

bump: ## Bump VERSION + PROJECT.md + _bump-extra (usage: make bump NEW=1.2.3)
ifndef NEW
	$(error NEW is required — usage: make bump NEW=1.2.3)
endif
	@echo "$(NEW)" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$$' || \
		(echo "ERROR: NEW must be semver (e.g. 1.2.3), got: $(NEW)" && exit 1)
	@printf '%s\n' "$(NEW)" > VERSION
	@[ ! -f "$(PROJECT_MD)" ] || \
		sed -i '' 's/\*\*Version\*\*: [0-9.]*/\*\*Version\*\*: $(NEW)/' "$(PROJECT_MD)"
	$(MAKE) _bump-extra NEW=$(NEW)
	@echo "Bumped to v$(NEW)"

release: ## Publish release (usage: make release NEW=1.2.3) — DEPRECATED: use /release skill instead
	@echo "[WARN] make release is DEPRECATED — use /release skill instead to avoid git op duplication"
	@echo "[WARN] Continuing for backwards compatibility..."
ifndef NEW
	$(error NEW is required — usage: make release NEW=1.2.3)
endif
	@git diff --quiet && git diff --cached --quiet || \
		(echo "ERROR: Working tree is dirty. Commit or stash changes before releasing." && exit 1)
	@git rev-parse --abbrev-ref HEAD | grep -q "^dev$$" || \
		(echo "ERROR: Must release from 'dev' branch. Currently on: $$(git rev-parse --abbrev-ref HEAD)" && exit 1)
	$(MAKE) bump NEW=$(NEW)
	git add -A
	git commit -m "chore: bump to v$(NEW)" || true
	git checkout main
	git merge dev --no-ff -m "release: v$(NEW)"
	git tag -s v$(NEW) -m "release v$(NEW)"
	git push origin main --tags
	$(MAKE) _publish NEW=$(NEW)
	git checkout dev
	git merge main
	git push origin dev
	@echo "✓ released v$(NEW)"

_publish: ## Publish release artifacts (override in Makefile.local) — called by /release skill after git ops
	@echo "[zie-framework] No-op _publish — override in Makefile.local for custom publish logic"

# ── Setup ─────────────────────────────────────────────────────────────────────
setup: ## Install git hooks + project deps (run once after cloning)
	git config core.hooksPath .githooks
	pip install -r requirements-dev.txt
	$(MAKE) _setup-extra
	@echo "Setup complete"

sync-version: ## Sync all version files to match current VERSION (alias for bump)
	$(MAKE) bump NEW=$$(cat VERSION)

# ── Archive ───────────────────────────────────────────────────────────────────
archive: ## Archive shipped SDLC artifacts (move Done-lane items to archive/)
	@python3 -c "\
import re, shutil, sys; \
from pathlib import Path; \
zf = Path('zie-framework'); \
roadmap_path = zf / 'ROADMAP.md'; \
roadmap = roadmap_path.read_text() if roadmap_path.exists() else ''; \
done_match = re.search(r'## Done(.*?)(?=^## |\Z)', roadmap, re.DOTALL | re.MULTILINE); \
slugs = []; \
[slugs.append(m.group(1)) for line in (done_match.group(1).splitlines() if done_match else []) for m in [re.search(r'[-*]\s+.*?([a-z0-9][a-z0-9-]+)', line.lower())] if m]; \
moved = 0; \
[([shutil.move(str(src), str(zf / 'archive' / d / src.name)) or None for src in (zf / d).glob(f'*{slug}*') if not (zf / 'archive' / d / src.name).exists() and (moved := moved + 1)]) for slug in slugs for d in ('backlog', 'specs', 'plans')]; \
print(f'Archive complete. Moved {moved} file(s).')"

# ── Plans archive ─────────────────────────────────────────────────────────────
archive-plans: ## Move plans older than 60 days to zie-framework/plans/archive/
	@mkdir -p zie-framework/plans/archive
	@find zie-framework/plans -maxdepth 1 -name "*.md" \
	  -mtime +60 -exec mv {} zie-framework/plans/archive/ \;
	@echo "[zie-framework] Archived plans older than 60 days"

.PHONY: archive-prune
archive-prune: ## Prune archive/ files older than 90 days (guard: skips if < 20 total files)
	@python3 -c "\
import os, sys, time; \
from pathlib import Path; \
archive_root = Path('zie-framework/archive'); \
subdirs = ('backlog', 'specs', 'plans'); \
TTL = 90 * 86400; GUARD = 20; \
all_md = [f for d in subdirs for f in (archive_root / d).glob('*.md') if archive_root.exists() and (archive_root / d).exists()]; \
(not archive_root.exists()) and [print('[zie-framework] Archive prune: archive directory not found, skipping'), sys.exit(0)]; \
len(all_md) < GUARD and [print(f'[zie-framework] Archive prune: archive too young ({len(all_md)} files), skipping prune'), sys.exit(0)]; \
now = time.time(); removed = [0]; \
[[f.unlink() or removed.__setitem__(0, removed[0] + 1) for f in (archive_root / d).glob('*.md') if (now - f.stat().st_mtime) > TTL] for d in subdirs if (archive_root / d).exists()]; \
print(f'[zie-framework] Archive prune: removed {removed[0]} file(s)')"

.PHONY: adr-count
adr-count: ## Count ADR files in zie-framework/decisions/ (excludes ADR-000-summary.md)
	@count=$$(ls zie-framework/decisions/ADR-*.md 2>/dev/null | grep -v ADR-000-summary | wc -l | tr -d ' '); echo $$count

.PHONY: docs-sync
docs-sync: ## Run docs-sync-check manually (checks CLAUDE.md + README.md vs disk)
	@echo "[zie-framework] docs-sync-check is a Claude skill — run inside a Claude session:"
	@echo "  Skill(zie-framework:docs-sync-check)"
	@echo "Or run /zie-retro which invokes it automatically."

# ── Utilities ─────────────────────────────────────────────────────────────────
clean: ## Remove cache files and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; \
	find . -name ".coverage" -delete 2>/dev/null; \
	find . -name ".coverage.*" -delete 2>/dev/null; \
	find . -name "coverage.xml" -delete 2>/dev/null; \
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null; \
	$(MAKE) _clean-extra; true

# ── Hooks — override in Makefile.local ────────────────────────────────────────
# Pattern rule: any _*-extra / _publish target not defined in Makefile.local
# resolves here as a silent no-op. Explicit rules in Makefile.local always win
# over pattern rules — no duplicate-target warnings.
_%:
	@true

-include Makefile.local
