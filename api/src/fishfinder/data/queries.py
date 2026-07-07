"""visits / receiver_locations / timeline SQL (Data.md)."""

from __future__ import annotations

import duckdb

VISITS_COLUMNS = ["signal", "array", "arrived_at", "departed_at", "ping_count", "lat", "lon", "rkm"]


def _quote(column: str) -> str:
    # `array` collides with DuckDB's ARRAY type keyword when unquoted.
    return f'"{column}"' if column == "array" else column


def get_visits(
    con: duckdb.DuckDBPyConnection, signals: list[str] | None
) -> list[dict[str, object]]:
    columns_sql = ", ".join(_quote(c) for c in VISITS_COLUMNS)
    if signals:
        placeholders = ",".join("?" for _ in signals)
        sql = f"""
            SELECT {columns_sql} FROM visits
            WHERE signal IN ({placeholders})
            ORDER BY signal, arrived_at
        """
        rows = con.execute(sql, signals).fetchall()
    else:
        sql = f"SELECT {columns_sql} FROM visits ORDER BY signal, arrived_at"
        rows = con.execute(sql).fetchall()
    return [dict(zip(VISITS_COLUMNS, row, strict=True)) for row in rows]


def get_fish_timeline(
    con: duckdb.DuckDBPyConnection, signals: list[str], *, include_signal: bool
) -> list[dict[str, object]]:
    columns = ["detected_at", "array", "receiver_id", "lat", "lon"]
    if include_signal:
        columns.insert(0, "signal")
    columns_sql = ", ".join(
        f"r.{_quote(c)}" if c in ("lat", "lon") else f"d.{_quote(c)}" for c in columns
    )
    placeholders = ",".join("?" for _ in signals)
    sql = f"""
        SELECT {columns_sql}
        FROM detections d
        LEFT JOIN receiver_locations r
            ON d.receiver_id = r.receiver_id AND d."array" = r."array"
        WHERE d.signal IN ({placeholders})
        ORDER BY d.signal, d.detected_at
    """
    rows = con.execute(sql, signals).fetchall()
    return [dict(zip(columns, row, strict=True)) for row in rows]
