# Data

**Status:** drafted

## Table of Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Decisions](#decisions)
- [Design](#design)
  - [Sources](#sources)
  - [detections table](#detections-table)
  - [receiver_locations table](#receiver_locations-table)
  - [visits derivation](#visits-derivation)

## Purpose

Defines the source data, how it's cleaned and loaded into DuckDB, and the derived `visits` table pane 1 reads from.

## Scope

Covers the two source CSVs, cleaning rules, DuckDB schema, and the visit-derivation query. Does not cover how this is exposed over HTTP (see [API.md](API.md)) or rendered (see [App.md](App.md)).

## Decisions

- Use `Signal` as the canonical fish identifier, not `TagCode` — confirmed 1:1 (70/70, no crossover) across all 358,040 detection rows; `Signal` is what's read off the receiver, so it's the id shown everywhere.
- Join detections to receiver metadata on zero-padded `ReceiverID` **and** `Array` together (not `ReceiverID` alone, and not `Array` alone). `Array`-only loses precision — `Marine` (46 receivers) and `Mouth` (8 receivers) each span multiple distinct receiver locations at the same `rkm`. But `ReceiverID`-only is a real bug: physical receivers get redeployed at different arrays across the season — e.g. receiver `005` shows up at both `BigEddy` (rkm 23.43) and `SkilakOutlet` (rkm 82.05) — so a `receiver_id`-only join fans out and mismatches those pings to the wrong location.
- Use each receiver's average lat/lon across its deployment rows, rather than time-matching a detection's timestamp against `deploy_time`/`retrieve_time` windows — deployment-to-deployment drift is ~100m, noise at river scale, and this avoids a brittle time-range join.
- Use `Timestamp_ak` as the canonical detection time; the naive `Timestamp` column is unused. Its values are local America/Anchorage clock time with a literal `AKDT` string suffix (e.g. `2026-06-14 19:24:45.299956 AKDT`) rather than an IANA zone name, so parsers won't handle it out of the box: strip the suffix and apply a fixed UTC-8 offset (safe — the whole dataset is AKDT, there are no AKST rows to disambiguate), then normalize to UTC for storage/sorting. Don't reach for `America/Anchorage` zoneinfo directly against the literal string — that's a different, ambiguous parse path. Note the stationary CSV's `deploy_time`/`retrieve_time` are already ISO-8601 UTC (`...Z`), a different format — don't assume the two files agree.
- A **visit** is a maximal run of a fish's consecutive detections at one `Array`, ending the moment the fish is next detected at a different `Array` — no time-gap threshold. Pane 1 shows the visit's first detection (arrival) as its representative point/time.
- Load both CSVs into DuckDB once at API startup rather than reading CSVs per request — 358k rows is small for DuckDB in-memory, and the source files don't change during a session.

## Design

### Sources

| File | Rows | Grain |
|---|---|---|
| `data/detection/Step5_Filtered_PRIscaled_perRx_6in_12cycles_kmax4_tolPerCycle0.20.csv` | 358,040 | one detection ping |
| `data/StationaryData_CLEAN_all.csv` | 97 | one receiver deployment/retrieval event |

Only 8 of the stationary file's 20 `Array` values (16 of its 97 receiver-deployment rows) appear in the detections CSV at all — e.g. `Marine`'s 46 receivers have zero detections. That's expected: not all receiver data has been downloaded from the field yet this season, not a sign the load is broken.

### `detections` table

Loaded from the detections CSV, renamed/typed:

| column | source column | type | notes |
|---|---|---|---|
| `signal` | `Signal` | varchar | fish id |
| `array` | `Array` | varchar | |
| `receiver_id` | `ReceiverID`, zero-padded to 3 digits | varchar | join key, paired with `array` (see below) |
| `detected_at` | `Timestamp_ak`, parsed to UTC | timestamp | |
| `sig_str`, `tilt`, `temp` | `SigStr`, `Tilt`, `Temp` | double | available for Claude filters; not used by panes 1/2 directly |

### `receiver_locations` table

Aggregated from the stationary CSV, one row per (`ReceiverID`, `Array`) pair — a physical receiver can be redeployed at a different array (and rkm) later in the season, e.g. `005` at both `BigEddy` and `SkilakOutlet`, so `receiver_id` alone isn't a unique key:

```sql
SELECT
  lpad(ReceiverID, 3, '0')  AS receiver_id,
  Array                      AS array,
  try_cast(rkm AS DOUBLE)    AS rkm,     -- NULL for tributary arrays (BeaverCreekTrib, FunnyRiver, Slikok)
  avg(Latitude)              AS lat,
  avg(Longitude)             AS lon
FROM stationary
GROUP BY 1, 2, 3
```

### `visits` derivation

Gaps-and-islands over each fish's chronological detections — a new visit starts whenever `array` differs from the previous detection for that `signal`. Arrival receiver (for pane 1's point) is the receiver of the first ping in the visit:

```sql
WITH ordered AS (
  SELECT *,
    lag(array) OVER (PARTITION BY signal ORDER BY detected_at) AS prev_array
  FROM detections
),
flagged AS (
  SELECT *,
    sum(CASE WHEN array IS DISTINCT FROM prev_array THEN 1 ELSE 0 END)
      OVER (PARTITION BY signal ORDER BY detected_at) AS visit_group
  FROM ordered
)
SELECT
  signal,
  array,
  visit_group,
  min(detected_at)                    AS arrived_at,
  max(detected_at)                    AS departed_at,
  count(*)                            AS ping_count,
  arg_min(receiver_id, detected_at)   AS arrival_receiver_id
FROM flagged
GROUP BY signal, array, visit_group
```

Joined to `receiver_locations` on `arrival_receiver_id = receiver_id AND array = array` to get `lat`/`lon`/`rkm` for the point — both columns are required on the join, not `receiver_id` alone (see the join-key decision above).
