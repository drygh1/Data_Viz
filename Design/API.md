# API

**Status:** drafted

## Table of Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Decisions](#decisions)
- [Design](#design)
  - [GET /api/visits](#get-apivisits)
  - [GET /api/fish/{signal}/timeline](#get-apifishsignaltimeline)
  - [GET /api/fish/timelines](#get-apifishtimelines)
  - [POST /api/query](#post-apiquery)

## Purpose

FastAPI service that exposes the DuckDB tables from [Data.md](Data.md) to the frontend, and turns a natural-language filter into SQL via Claude.

## Scope

Covers HTTP endpoints, request/response shapes, and how the Claude-generated SQL is sandboxed. Does not cover table schemas (see [Data.md](Data.md)) or how responses are rendered (see [App.md](App.md)).

## Decisions

- Claude-generated SQL runs against a read-only DuckDB connection, and is validated by parsing it — not a naive string-prefix check — to confirm it's a single statement rooted in `SELECT`. `WITH ... SELECT` CTEs are explicitly allowed (the `visits` table in [Data.md](Data.md) is itself defined as one); multiple statements or any non-`SELECT` statement type (`INSERT`/`UPDATE`/`DELETE`/DDL/`PRAGMA`/`ATTACH`/etc.) is rejected, because arbitrary LLM output must never be able to mutate or drop the loaded tables.
- Claude's system prompt includes the `detections`/`receiver_locations`/`visits` table and column definitions from [Data.md](Data.md) verbatim rather than restated here, because the model can only generate correct SQL if it knows the real schema, and duplicating it in two docs would drift.
- `/api/query` returns the SQL text alongside the matching fish ids, because the user wants to see — and verify — exactly what Claude ran before it drives pane 1.
- All endpoints are stateless reads with no auth/persistence, because this is a local single-user analytical tool, not a multi-tenant service.

## Design

### `GET /api/visits`

Pane 1 data — one row per fish per visit.

Query params: `signals` (optional, comma-separated — restricts to a fish-id set, e.g. from `/api/query`)

```json
[
  { "signal": "2AB5", "array": "BeaverCreek", "arrived_at": "2026-06-14T19:24:45Z",
    "departed_at": "2026-06-14T19:41:02Z", "ping_count": 34,
    "lat": 60.5381, "lon": -151.1476, "rkm": 16.36 }
]
```

### `GET /api/fish/{signal}/timeline`

Pane 2 data — every raw detection for one fish, joined to receiver location.

```json
[
  { "detected_at": "2026-06-14T19:24:45.299956Z", "array": "BeaverCreek",
    "receiver_id": "065", "lat": 60.5381, "lon": -151.1476 }
]
```

### `GET /api/fish/timelines`

Same shape as above, batched for multiple fish via `?signals=2AB5,04AD` — for comparing a few fish's movement together.

### `POST /api/query`

Body:

```json
{ "text": "fish that visited BigEddy after June 20" }
```

The text is sent to Claude alongside a system prompt containing the schema from [Data.md](Data.md) (table/column names and types) and an instruction to return a single read-only SQL statement.

Response:

```json
{
  "sql": "SELECT DISTINCT signal FROM visits WHERE array = 'BigEddy' AND arrived_at > '2026-06-20'",
  "signals": ["0559", "0565"],
  "row_count": 2
}
```

If the generated SQL fails validation (not a single `SELECT`, references a nonexistent table/column, or errors in DuckDB), respond `422` with the offending SQL and the error message so the frontend can show it in the SQL preview.
