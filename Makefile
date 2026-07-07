.PHONY: install dev lint format typecheck

install:
	cd api && uv sync
	cd app && pnpm install

dev:
	( cd api && uv run uvicorn fishfinder.main:app --reload --port 8000 ) & \
	( cd app && pnpm dev ) & \
	wait

lint:
	cd api && uv run ruff check .
	cd app && pnpm biome check .

format:
	cd api && uv run ruff format .
	cd app && pnpm biome format --write .

typecheck:
	cd api && uv run pyright
	cd app && pnpm typecheck
