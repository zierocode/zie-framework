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

# ── Setup ─────────────────────────────────────────────────────────────────────
setup: ## Install git hooks (run once after cloning)
	git config core.hooksPath .githooks
	@echo "Git hooks installed from .githooks/"

# ── Utilities ─────────────────────────────────────────────────────────────────
clean: ## Remove cache files and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; true

lint: ## Lint Python hooks
	python3 -m py_compile hooks/*.py && echo "All hooks compile OK"

lint-md: ## Lint all Markdown files (markdownlint, no exceptions)
	npx markdownlint-cli "**/*.md" --ignore node_modules
