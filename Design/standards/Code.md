# Code

**Status:** drafted

## Table of Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Decisions](#decisions)
- [Design](#design)
  - [Python (Data + API)](#python-data--api)
  - [TypeScript (App)](#typescript-app)
  - [Makefile](#makefile)
  - [Enforcement](#enforcement)

## Purpose

Defines the tooling used to install dependencies, lint, and format code across Fishfinder's Python and TypeScript codebases, so every contributor's environment behaves the same way.

## Scope

Covers package management, linting, formatting, and type-checking tool choices and how they're invoked. Does not cover test conventions (see `standards/Tests.md`) or design-doc structure (see [Design-docs.md](Design-docs.md)).

## Decisions

- Chose **uv** over pip/venv/Poetry for Python because it's a single fast tool for venv + install + lockfile.
- Chose **Ruff** over flake8+isort+black because it replaces all three with one fast binary, including import sorting.
- Chose **pyright** over mypy for type checking because it's faster and integrates well with editors.
- Chose **pnpm** over npm/yarn because it's faster, disk-efficient, and catches phantom dependencies via strict `node_modules` resolution.
- Chose **Biome** over ESLint+Prettier because it's a single fast tool for both lint and format, mirroring Ruff's role on the Python side; fall back to ESLint+Prettier only if a specific plugin (e.g. `jsx-a11y`) is needed that Biome doesn't cover.
- Chose a top-level **Makefile** as the single entry point over remembering separate `uv`/`pnpm` invocations per codebase, because a contributor should be able to install and run the whole app without knowing it's two different toolchains underneath.

## Design

### Python (Data + API)

| Tool | Purpose | Config |
|---|---|---|
| uv | venv + dependency install + lockfile | `pyproject.toml` + `uv.lock` |
| Ruff | lint + format + import sort | `pyproject.toml [tool.ruff]` |
| pyright | type checking | `pyproject.toml [tool.pyright]` |

```bash
uv sync               # install deps into .venv
uv run ruff check .   # lint
uv run ruff format .  # format
uv run pyright        # type check
```

### TypeScript (App)

| Tool | Purpose | Config |
|---|---|---|
| pnpm | install + workspace management | `pnpm-lock.yaml` |
| Biome | lint + format | `biome.json` |

```bash
pnpm install
pnpm biome check .           # lint
pnpm biome format --write .  # format
```

### Makefile

A top-level `Makefile` wraps both toolchains so `make <target>` is the only thing a contributor needs to remember:

| Target | Runs |
|---|---|
| `make install` | `uv sync` + `pnpm install` |
| `make dev` | API (`uvicorn`, reload on) + App (`vite`) concurrently |
| `make lint` | `uv run ruff check .` + `pnpm biome check .` |
| `make format` | `uv run ruff format .` + `pnpm biome format --write .` |
| `make typecheck` | `uv run pyright` |

Not yet implemented — added here as the documented interface once the Data/API/App projects exist to run.

### Enforcement

Both the Python checks (`ruff check`, `pyright`) and the TypeScript check (`biome check`) run as pre-commit hooks and in CI; a PR with lint or type errors doesn't merge.
