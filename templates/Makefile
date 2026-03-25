VERSION := $(shell cat VERSION 2>/dev/null || echo "0.1.0")
ENV     ?= dev

# Path to PROJECT.md for version badge sync (override in Makefile.local if different)
PROJECT_MD ?= zie-framework/PROJECT.md

# ── Help ──────────────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help
help:
	@grep -E '^[a-zA-Z][a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Tests ─────────────────────────────────────────────────────────────────────
test-unit: ## Run unit tests (override in Makefile.local)
	@echo "Override test-unit in Makefile.local"

test-int: ## Run integration tests (override in Makefile.local)
	@echo "Override test-int in Makefile.local"

lint-md: ## Lint all Markdown files (markdownlint)
	npx markdownlint-cli "**/*.md" --ignore node_modules

test: test-unit test-int lint-md ## Full test suite

# ── Environments ──────────────────────────────────────────────────────────────
start:  _start-$(ENV)  ## Start environment (usage: make start ENV=dev|staging|prod)
stop:   _stop-$(ENV)   ## Stop environment  (usage: make stop ENV=dev)
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

# ── Release ───────────────────────────────────────────────────────────────────
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

release: ## Publish release (usage: make release NEW=1.2.3)
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
	git tag -a v$(NEW) -m "release v$(NEW)"
	git push origin main --tags
	$(MAKE) _publish NEW=$(NEW)
	git checkout dev
	git merge main
	git push origin dev
	@echo "✓ released v$(NEW)"

# ── Setup ─────────────────────────────────────────────────────────────────────
setup: ## Install git hooks + project deps (run once after cloning)
	git config core.hooksPath .githooks
	$(MAKE) _setup-extra
	@echo "Setup complete"

sync-version: ## Sync all version files to match current VERSION (alias for bump)
	$(MAKE) bump NEW=$$(cat VERSION)

# ── Utilities ─────────────────────────────────────────────────────────────────
clean: ## Remove cache files and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; \
	$(MAKE) _clean-extra; true

# ── Hooks — override in Makefile.local ────────────────────────────────────────
# _bump-extra  NEW=x.y.z  runs inside bump, before commit
#                         → update plugin.json, package.json, pyproject.toml, etc.
# _publish     NEW=x.y.z  runs inside release, after git push origin main --tags
#                         → gh release create, npm publish, docker push, etc.
# _setup-extra            runs inside setup → install project-specific deps
# _clean-extra            runs inside clean → remove project-specific artifacts
#
# Pattern rule: any _* hook not defined in Makefile.local resolves here as
# a silent no-op. Explicit rules in Makefile.local always win over pattern
# rules — no duplicate-target warnings.
_%:
	@true

-include Makefile.local
