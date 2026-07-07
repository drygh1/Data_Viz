from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from fishfinder.data import queries

router = APIRouter()


@router.get("/api/fish/{signal}/timeline")
def fish_timeline(signal: str, request: Request):
    con = request.app.state.db.cursor()
    rows = queries.get_fish_timeline(con, [signal], include_signal=False)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No detections found for signal {signal!r}")
    return rows


@router.get("/api/fish/timelines")
def fish_timelines(request: Request, signals: str = Query(...)):
    signal_list = signals.split(",")
    con = request.app.state.db.cursor()
    return queries.get_fish_timeline(con, signal_list, include_signal=True)
