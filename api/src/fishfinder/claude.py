"""Claude client, NL->SQL prompt, and SQL validation (API.md)."""

from __future__ import annotations

import os

import sqlglot
from anthropic import Anthropic
from sqlglot import exp
from sqlglot.errors import ParseError

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You translate a biologist's natural-language question into a single \
read-only DuckDB SQL query over the tables below. Respond with ONLY the SQL statement \
(a `WITH ... SELECT` CTE is fine) — no prose, no markdown code fences, no explanation. \
The result must include a `signal` column so the caller can identify the matching fish.

IMPORTANT: `array` collides with DuckDB's ARRAY type keyword. Always double-quote it as \
"array" wherever it's referenced as a column (SELECT, WHERE, GROUP BY, ORDER BY, etc.), \
e.g. `WHERE "array" = 'BigEddy'`.

detections — one row per detection ping
  signal       varchar    fish id
  array        varchar    receiver array name
  receiver_id  varchar    zero-padded receiver id
  detected_at  timestamp  detection time, UTC
  sig_str      double     signal strength
  tilt         double
  temp         double

receiver_locations — one row per (receiver_id, array)
  receiver_id  varchar
  array        varchar
  rkm          double     river km; NULL for tributary arrays
  lat          double
  lon          double

visits — one row per fish per visit (a maximal run of a fish's consecutive
detections at one array, ending when it's next detected at a different array)
  signal       varchar
  array        varchar
  arrived_at   timestamp  first detection of the visit
  departed_at  timestamp  last detection of the visit
  ping_count   bigint
  lat          double
  lon          double
  rkm          double
"""


class SqlValidationError(ValueError):
    """Raised when Claude's generated SQL fails validation."""

    def __init__(self, message: str, sql: str) -> None:
        super().__init__(message)
        self.sql = sql


def _extract_sql(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned[:4].lower().startswith("sql\n"):
            cleaned = cleaned[4:]
    return cleaned.strip().rstrip(";").strip()


def validate_sql(sql: str) -> None:
    """Confirm `sql` is a single, read-only `SELECT` statement (WITH-CTEs allowed)."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="duckdb") if s is not None]
    except ParseError as exc:
        raise SqlValidationError(f"Could not parse generated SQL: {exc}", sql) from exc

    if len(statements) != 1:
        raise SqlValidationError(f"Expected exactly one SQL statement, got {len(statements)}", sql)
    if not isinstance(statements[0], exp.Select):
        raise SqlValidationError("Only SELECT statements are allowed", sql)


def generate_sql(text: str) -> str:
    """Ask Claude to translate `text` into SQL, and validate the result."""
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = "".join(block.text for block in response.content if block.type == "text")
    sql = _extract_sql(raw)
    validate_sql(sql)
    return sql
