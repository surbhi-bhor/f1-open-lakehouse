.PHONY: guard lint test check

guard:
	@bash scripts/guard_location.sh "$(CURDIR)"

lint:
	uv run ruff check .

test:
	uv run pytest

check: guard lint test
