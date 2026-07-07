from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import duckdb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fishfinder.data.load import load_database
from fishfinder.routes import fish, query, visits

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("FISHFINDER_DATA_DIR", REPO_ROOT / "data"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db_path = os.path.join(tempfile.gettempdir(), "fishfinder.duckdb")
    load_database(db_path, DATA_DIR)
    app.state.db = duckdb.connect(db_path, read_only=True)
    try:
        yield
    finally:
        app.state.db.close()


app = FastAPI(title="Fishfinder API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FISHFINDER_APP_ORIGIN", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(visits.router)
app.include_router(fish.router)
app.include_router(query.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
