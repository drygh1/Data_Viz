# Project

**Status:** drafted

## Table of Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Background](#background)
- [Decisions](#decisions)
- [Design](#design)
  - [Components](#components)
  - [Flow](#flow)
  - [Layout](#layout)
  - [Repository layout](#repository-layout)

## Purpose

Fishfinder lets a biologist explore JSATS-tagged fish detections on the Kenai River: see where every tagged fish currently sits, drill into one fish's movement over time, and filter the fish set with a natural-language query instead of hand-written SQL.

## Scope

Covers the overall architecture, the three components (Data, API, App), how they fit together, and the stack. Does not cover data schema/ETL details (see [Data.md](Data.md)), HTTP contracts (see [API.md](API.md)), or UI/interaction details (see [App.md](App.md)).

## Background

JSATS (Juvenile Salmon Acoustic Telemetry System) tags emit an acoustic ping picked up by fixed receivers ("arrays") along the river. A detection only tells you *which receiver* heard the tag *when* — not a continuous position — so "movement" is reconstructed from the sequence of receivers a fish passes.

## Decisions

- Chose FastAPI (Python) over Node/Django because the CSV cleaning, rkm/lat-lon handling, and "visit" derivation are pandas/numpy-shaped work, and it ships with the official Anthropic Python SDK for the `/api/query` endpoint.
- Chose DuckDB over SQLite/Postgres because the core feature — Claude writes SQL, the app runs it — is DuckDB's headline use case: fast in-process analytical SQL directly over the loaded tables, no server to run.
- Chose React + Vite over Svelte/Vue because deck.gl (below) has first-class React bindings.
- Chose deck.gl + MapLibre over Leaflet/Mapbox because pane 1 is a jittered scatterplot and pane 2 is animated movement — deck.gl's `ScatterplotLayer`/animated layers are built for exactly that, and MapLibre avoids Mapbox's token/licensing.
- Chose to keep Data and API in one Python package (`api/`) rather than separate top-level folders, because [Data.md](Data.md) already decided the CSVs load into DuckDB at API startup — they're one deployable service, and splitting them would be organizational, not architectural.
- Chose folder names `api/` and `app/` to match the component doc names (`API.md`, `App.md`) — shared vocabulary between the docs and the repo.

## Design

### Components

| Component | Doc | Responsibility |
|---|---|---|
| Data | [Data.md](Data.md) | Load the two source CSVs into DuckDB, clean/normalize them, derive `visits` |
| API | [API.md](API.md) | FastAPI service: timeline endpoints + Claude NL→SQL endpoint |
| App | [App.md](App.md) | React 3-pane UI |

### Flow

```
CSV files → [Data: DuckDB tables] → [API: FastAPI] → [App: React/deck.gl]
                                          ↑
                                   Claude (NL → SQL)
```

### Layout

```
┌───────────────────────┬───────────────────────┐
│ Pane 1                 │ Pane 2                 │
│ Overview map           │ Animated fish map      │
│ (one point per visit)  │ (all raw pings,        │
│ click → selects fish   │  played over time)     │
├───────────────────────┴───────────────────────┤
│ Pane 3 — natural-language filter + SQL preview  │
└───────────────────────────────────────────────┘
```

### Repository layout

```
Data_Viz/
├── Design/              # design docs
├── data/                # source CSVs
├── api/                 # Python: Data + API components (one deployable service)
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/fishfinder/
│   │   ├── main.py          # FastAPI app + startup CSV load
│   │   ├── data/
│   │   │   ├── load.py      # CSV → DuckDB ingestion (Data.md)
│   │   │   └── queries.py   # visits / receiver_locations SQL
│   │   ├── routes/
│   │   │   ├── visits.py
│   │   │   ├── fish.py
│   │   │   └── query.py     # Claude NL→SQL endpoint
│   │   └── claude.py        # Claude client, prompt, SQL validation
│   └── tests/
├── app/                  # React/Vite frontend
│   ├── package.json
│   └── src/
│       ├── panes/
│       │   ├── OverviewMap/
│       │   ├── FishTimelineMap/
│       │   └── QueryBar/
│       ├── state/            # lifted selected-fish + filter store
│       ├── client/           # typed fetch wrapper for the API endpoints
│       └── lib/               # jitter helper, etc.
├── Makefile
└── README.md
```

`api/src/fishfinder/routes/` maps 1:1 to the endpoint list in [API.md](API.md); `data/` underneath holds the ingestion and `visits` SQL from [Data.md](Data.md). `app/src/panes/` maps 1:1 to the pane table in [App.md](App.md). Python uses a `src/` layout as current packaging best practice, playing well with `uv`/`pyright` per [Code.md](standards/Code.md).
