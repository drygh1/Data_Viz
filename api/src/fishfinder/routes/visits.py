from __future__ import annotations

from fastapi import APIRouter, Query, Request

from fishfinder.data import queries

router = APIRouter()


@router.get("/api/visits")
def list_visits(request: Request, signals: str | None = Query(default=None)):
    signal_list = signals.split(",") if signals else None
    con = request.app.state.db.cursor()
    return queries.get_visits(con, signal_list)
