from __future__ import annotations

import duckdb
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from fishfinder.claude import SqlValidationError, generate_sql

router = APIRouter()


class QueryRequest(BaseModel):
    text: str


class QueryResponse(BaseModel):
    sql: str
    signals: list[str]
    row_count: int


@router.post("/api/query", response_model=QueryResponse)
def run_query(body: QueryRequest, request: Request) -> QueryResponse:
    try:
        sql = generate_sql(body.text)
    except SqlValidationError as exc:
        raise HTTPException(status_code=422, detail={"sql": exc.sql, "error": str(exc)}) from exc

    con = request.app.state.db.cursor()
    try:
        rows = con.execute(sql).fetchall()
        columns = [d[0] for d in con.description]
    except duckdb.Error as exc:
        raise HTTPException(status_code=422, detail={"sql": sql, "error": str(exc)}) from exc

    if "signal" not in columns:
        raise HTTPException(
            status_code=422,
            detail={"sql": sql, "error": "Query result must include a 'signal' column"},
        )
    signal_idx = columns.index("signal")
    signals = sorted({row[signal_idx] for row in rows})
    return QueryResponse(sql=sql, signals=signals, row_count=len(rows))
