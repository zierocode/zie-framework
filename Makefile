VERSION := $(shell cat VERSION 2>/dev/null || echo "0.1.0")

# ── Help ──────────────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Tests ─────────────────────────────────────────────────────────────────────
test-unit: ## Fast unit tests (run constantly during /zie-build)
	python3 -m pytest tests/ -x -q --tb=short --no-header -m "not integration"

test-int: ## Integration tests (hook event simulation)
	python3 -m pytest tests/ -v -m "integration" --tb=short

test: test-unit lint-md ## Full test suite (unit + integration + md lint)

# ── Git workflow ──────────────────────────────────────────────────────────────
push: ## Commit + push to dev branch (usage: make push m="commit message")
	@test -n "$(m)" || (echo "Usage: make push m='commit message'" && exit 1)
	git add -A && git commit -m "$(m)" && git push origin dev

ship: ## Full release gate — use /zie-ship instead
	$(MAKE) test || (echo "Tests failed — fix before shipping" && exit 1)
	@echo "All tests passed. Run /zie-ship for the full release gate."

# ── Release ───────────────────────────────────────────────────────────────────
release: ## Publish release (usage: make release NEW=1.2.3)
ifndef NEW
	$(error NEW is required — usage: make release NEW=1.2.3)
endif
	@git diff --quiet && git diff --cached --quiet || \
		(echo "ERROR: Working tree is dirty. Commit or stash changes before releasing." && exit 1)
	@git rev-parse --abbrev-ref HEAD | grep -q "^dev$$" || \
		(echo "ERROR: Must release from 'dev' branch. Currently on: $$(git rev-parse --abbrev-ref HEAD)" && exit 1)
	sed -i '' 's/"version": "[^"]*"/"version": "$(NEW)"/' .claude-plugin/plugin.json
	git add .claude-plugin/plugin.json
	git diff --cached --quiet || git commit --amend --no-edit
	git checkout main
	git merge dev --no-ff -m "release: v$(NEW)"
	git tag -s v$(NEW) -m "release v$(NEW)"
	git push origin main --tags
	git checkout dev

# ── Setup ─────────────────────────────────────────────────────────────────────
setup: ## Install git hooks (run once after cloning)
	git config core.hooksPath .githooks
	@echo "Git hooks installed from .githooks/"

sync-version: ## Sync plugin.json version to match VERSION
	jq --arg v "$$(cat VERSION)" '.version = $$v' .claude-plugin/plugin.json \
	  > .claude-plugin/plugin.json.tmp \
	  && mv .claude-plugin/plugin.json.tmp .claude-plugin/plugin.json
	sed -i '' 's/\*\*Version\*\*: [0-9.]*/\*\*Version\*\*: '"$$(cat VERSION)"'/' \
	  zie-framework/PROJECT.md
	@echo "plugin.json + PROJECT.md version synced to $$(cat VERSION)"

# ── Utilities ─────────────────────────────────────────────────────────────────
clean: ## Remove cache files and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; true

lint: lint-bandit ## Lint Python hooks (syntax + SAST)
	python3 -m py_compile hooks/*.py && echo "All hooks compile OK"

lint-bandit: ## Run Bandit SAST on hooks/ (medium severity + confidence)
	python3 -m bandit -r hooks/ -ll -q

lint-md: ## Lint all Markdown files (markdownlint, no exceptions)
	npx markdownlint-cli "**/*.md" --ignore node_modules
