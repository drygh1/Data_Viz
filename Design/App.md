# App

**Status:** drafted

## Table of Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Decisions](#decisions)
- [Design](#design)
  - [Panes](#panes)
  - [State flow](#state-flow)
  - [Jitter](#jitter)

## Purpose

React 3-pane UI: browse all fish, animate one fish's movement, and filter fish by natural language.

## Scope

Covers pane layout, cross-pane state, and map rendering. Does not cover the endpoints it calls (see [API.md](API.md)) or how the underlying data is derived (see [Data.md](Data.md)).

## Decisions

- Jitter overview points client-side, deterministically seeded by `signal` (not random per render), so a fish's dot doesn't jump around on re-render/refetch.
- Lift "selected fish" and "active filter (signal list)" to a single top-level store rather than prop-drilling, because pane 3's filter output feeds pane 1, and pane 1's click feeds pane 2.
- Drive pane 2's playback with a time slider filtering the already-fetched timeline client-side, rather than re-fetching per frame — a single fish's timeline is small enough to hold in memory and scrubbing needs to be instant.

## Design

### Panes

| Pane | Component | Data source | Interaction |
|---|---|---|---|
| 1. Overview map | `OverviewMap` (deck.gl `ScatterplotLayer`) | `GET /api/visits` | click a point → sets selected fish |
| 2. Animated map | `FishTimelineMap` (deck.gl animated layer + time slider) | `GET /api/fish/{signal}/timeline` | play / pause / scrub |
| 3. Filter bar | `QueryBar` + `SqlPreview` | `POST /api/query` | submit text → sets active filter, shows SQL |

### State flow

```
QueryBar submits text
   → POST /api/query → { sql, signals }
   → SqlPreview shows sql
   → active filter = signals
   → OverviewMap refetches /api/visits?signals=...
   → user clicks a point
   → selected fish = signal
   → FishTimelineMap fetches /api/fish/{signal}/timeline
```

### Jitter

Each visit's raw lat/lon is its receiver's location; multiple fish at the same receiver would render on top of each other. Jitter offset = a small deterministic radius/angle derived by hashing `signal + array`, so it's stable across re-renders.
