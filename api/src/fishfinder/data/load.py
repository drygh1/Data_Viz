"""CSV -> DuckDB ingestion (Data.md)."""

from __future__ import annotations

from pathlib import Path

import duckdb

DETECTIONS_CSV = "Step5_Filtered_PRIscaled_perRx_6in_12cycles_kmax4_tolPerCycle0.20.csv"
STATIONARY_CSV = "StationaryData_CLEAN_all.csv"

# `array` collides with DuckDB's ARRAY type keyword, so it's quoted everywhere
# it's referenced as a column, including in downstream CTEs.
CREATE_DETECTIONS_SQL = """
CREATE TABLE detections AS
SELECT
    Signal                                    AS signal,
    "Array"                                   AS "array",
    lpad(CAST(ReceiverID AS VARCHAR), 3, '0') AS receiver_id,
    strptime(
        replace(Timestamp_ak, ' AKDT', ''),
        '%Y-%m-%d %H:%M:%S.%f'
    ) + INTERVAL 8 HOUR                       AS detected_at,
    SigStr                                    AS sig_str,
    Tilt                                      AS tilt,
    Temp                                      AS temp
FROM read_csv_auto(?, header = true)
"""

CREATE_STATIONARY_SQL = """
CREATE TABLE stationary AS
SELECT * FROM read_csv_auto(?, header = true)
"""

CREATE_RECEIVER_LOCATIONS_SQL = """
CREATE TABLE receiver_locations AS
SELECT
    lpad(CAST(ReceiverID AS VARCHAR), 3, '0') AS receiver_id,
    "Array"                                   AS "array",
    try_cast(rkm AS DOUBLE)                   AS rkm,
    avg(Latitude)                             AS lat,
    avg(Longitude)                            AS lon
FROM stationary
GROUP BY 1, 2, 3
"""

# Gaps-and-islands: a new visit starts whenever `array` differs from the
# previous detection for that `signal`, joined to receiver_locations for the
# arrival point (Data.md).
CREATE_VISITS_SQL = """
CREATE TABLE visits AS
WITH ordered AS (
    SELECT *,
        lag("array") OVER (PARTITION BY signal ORDER BY detected_at) AS prev_array
    FROM detections
),
flagged AS (
    SELECT *,
        sum(CASE WHEN "array" IS DISTINCT FROM prev_array THEN 1 ELSE 0 END)
            OVER (PARTITION BY signal ORDER BY detected_at) AS visit_group
    FROM ordered
),
grouped AS (
    SELECT
        signal,
        "array",
        visit_group,
        min(detected_at)                  AS arrived_at,
        max(detected_at)                  AS departed_at,
        count(*)                          AS ping_count,
        arg_min(receiver_id, detected_at) AS arrival_receiver_id
    FROM flagged
    GROUP BY signal, "array", visit_group
)
SELECT
    g.signal,
    g."array",
    g.arrived_at,
    g.departed_at,
    g.ping_count,
    r.lat,
    r.lon,
    r.rkm
FROM grouped g
LEFT JOIN receiver_locations r
    ON g.arrival_receiver_id = r.receiver_id AND g."array" = r."array"
"""


def load_database(db_path: str, data_dir: Path) -> None:
    """Build a fresh DuckDB database file at `db_path` from the source CSVs."""
    Path(db_path).unlink(missing_ok=True)
    con = duckdb.connect(db_path)
    try:
        con.execute(CREATE_DETECTIONS_SQL, [str(data_dir / "detection" / DETECTIONS_CSV)])
        con.execute(CREATE_STATIONARY_SQL, [str(data_dir / STATIONARY_CSV)])
        con.execute(CREATE_RECEIVER_LOCATIONS_SQL)
        con.execute(CREATE_VISITS_SQL)
    finally:
        con.close()
