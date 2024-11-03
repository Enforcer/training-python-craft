.PHONY: fmt
fmt:
	uv run ruff format

.PHONY: lint
lint:
	uv run ruff check --fix
	mypy tests/ subscriptions/

.PHONY: qa
qa: fmt lint

.PHONY: test
test:
	uv run pytest tests/


.PHONY: all
all: fmt lint test

