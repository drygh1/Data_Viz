from collections.abc import Iterator
from pathlib import Path
from typing import Any

import duckdb
import pytest

from fishfinder.data.load import load_database

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"


def one(cursor: duckdb.DuckDBPyConnection) -> tuple[Any, ...]:
    row = cursor.fetchone()
    assert row is not None
    return row


@pytest.fixture(scope="module")
def con(tmp_path_factory: pytest.TempPathFactory) -> Iterator[duckdb.DuckDBPyConnection]:
    db_path = str(tmp_path_factory.mktemp("db") / "fishfinder.duckdb")
    load_database(db_path, DATA_DIR)
    connection = duckdb.connect(db_path, read_only=True)
    yield connection
    connection.close()


def test_detections_loaded(con: duckdb.DuckDBPyConnection) -> None:
    (count,) = one(con.execute("SELECT count(*) FROM detections"))
    assert count == 358_040


def test_receiver_id_is_zero_padded(con: duckdb.DuckDBPyConnection) -> None:
    (receiver_id,) = one(
        con.execute("SELECT receiver_id FROM detections WHERE signal = '2AB5' LIMIT 1")
    )
    assert receiver_id == "065"


def test_detected_at_converted_from_akdt_to_utc(con: duckdb.DuckDBPyConnection) -> None:
    # First row of the source CSV: Timestamp_ak = 2026-06-14 19:24:45.299956 AKDT
    # (UTC-8) -> 2026-06-15 03:24:45.299956 UTC.
    (count,) = one(
        con.execute(
            "SELECT count(*) FROM detections WHERE signal = '2AB5' AND receiver_id = '065' "
            "AND detected_at = TIMESTAMP '2026-06-15 03:24:45.299956'"
        )
    )
    assert count == 1


def test_receiver_redeployed_at_two_arrays(con: duckdb.DuckDBPyConnection) -> None:
    rows = con.execute(
        'SELECT "array" FROM receiver_locations WHERE receiver_id = \'005\' ORDER BY "array"'
    ).fetchall()
    arrays = {row[0] for row in rows}
    assert {"BigEddy", "SkilakOutlet"} <= arrays


def test_visits_are_maximal_runs_per_array(con: duckdb.DuckDBPyConnection) -> None:
    rows = con.execute(
        "SELECT \"array\" FROM visits WHERE signal = '2AB5' ORDER BY arrived_at"
    ).fetchall()
    arrays = [row[0] for row in rows]
    # no two consecutive visits share the same array
    assert all(a != b for a, b in zip(arrays, arrays[1:], strict=False))


def test_visits_have_locations_for_detected_arrays(con: duckdb.DuckDBPyConnection) -> None:
    (missing,) = one(con.execute("SELECT count(*) FROM visits WHERE lat IS NULL"))
    (total,) = one(con.execute("SELECT count(*) FROM visits"))
    assert missing < total
