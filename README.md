# Subscriptions

## Setup

### Prerequisites

- [docker](https://docs.docker.com/engine/install/) or compatible env (e.g. [podman](https://podman.io/docs/installation), [colima](https://github.com/abiosoft/colima) etc)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Python3.13](https://www.python.org/downloads/)
- make

### Project installation

```bash
uv venv --python 3.13
uv sync
```

### Running formatters, linter and type checker

```bash
make qa
```

### Running tests

```bash
docker compose up
make test
```

or

```bash
uv run pytest tests/
```
