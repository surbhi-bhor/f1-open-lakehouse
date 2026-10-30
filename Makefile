.PHONY: lint test check

# The repo sits on the Windows drive; a Linux venv inside it breaks, so keep it in WSL's home.
export UV_PROJECT_ENVIRONMENT ?= $(HOME)/.venvs/f1lake

lint:
	uv run ruff check .

test:
	uv run pytest

check: lint test
