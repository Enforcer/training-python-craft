.PHONY: fmt
fmt:
	uv run ruff format

.PHONY: lint
lint:
	uv run ruff check --fix
	uv run mypy tests/ subscriptions/
	uv run tach check

.PHONY: qa
qa: fmt lint

.PHONY: test
test:
	uv run pytest tests/


.PHONY: all
all: fmt lint test

