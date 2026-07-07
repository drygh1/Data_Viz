import { PathLayer, ScatterplotLayer } from "@deck.gl/layers";
import { DeckGL } from "@deck.gl/react";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useMemo, useState } from "react";
import { Map as MapLibreMap } from "react-map-gl/maplibre";
import { type TimelinePoint, getFishTimeline } from "../../client/api";
import { useFishfinderStore } from "../../state/store";

const INITIAL_VIEW_STATE = {
  longitude: -151.15,
  latitude: 60.5,
  zoom: 9,
  pitch: 0,
  bearing: 0,
};

const MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
const PLAYBACK_INTERVAL_MS = 200;

type LocatedPoint = TimelinePoint & { lat: number; lon: number };

export function FishTimelineMap() {
  const { selectedFish } = useFishfinderStore();
  const [timeline, setTimeline] = useState<LocatedPoint[]>([]);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTimeline([]);
    setIndex(0);
    setPlaying(false);
    if (!selectedFish) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    getFishTimeline(selectedFish)
      .then((data) => {
        if (!cancelled) {
          setTimeline(data.filter((p): p is LocatedPoint => p.lat != null && p.lon != null));
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load timeline");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedFish]);

  useEffect(() => {
    if (!playing || timeline.length === 0) return;
    const interval = setInterval(() => {
      setIndex((i) => {
        if (i >= timeline.length - 1) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, PLAYBACK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [playing, timeline.length]);

  const visited = timeline.slice(0, index + 1);
  const current = visited.at(-1);

  const layers = useMemo(() => {
    if (visited.length === 0) return [];
    const path = visited.map((p): [number, number] => [p.lon, p.lat]);
    return [
      new PathLayer<{ path: [number, number][] }>({
        id: "fish-path",
        data: [{ path }],
        getPath: (d) => d.path,
        getWidth: 3,
        widthMinPixels: 2,
        getColor: [30, 100, 200, 180],
      }),
      new ScatterplotLayer<LocatedPoint>({
        id: "fish-path-points",
        data: visited,
        getPosition: (p) => [p.lon, p.lat],
        getRadius: 30,
        radiusMinPixels: 2,
        radiusMaxPixels: 5,
        getFillColor: [30, 100, 200, 120],
      }),
      new ScatterplotLayer<LocatedPoint>({
        id: "fish-current-position",
        data: current ? [current] : [],
        getPosition: (p) => [p.lon, p.lat],
        getRadius: 60,
        radiusMinPixels: 5,
        radiusMaxPixels: 10,
        getFillColor: [255, 140, 0, 230],
      }),
    ];
  }, [visited, current]);

  if (!selectedFish) {
    return (
      <div className="pane pane-timeline">
        <div className="pane-header">Animated fish map</div>
        <div className="pane-empty">Click a fish on the overview map to see its movement.</div>
      </div>
    );
  }

  return (
    <div className="pane pane-timeline">
      <div className="pane-header">
        Fish {selectedFish}
        {loading && <span className="pane-status"> · loading…</span>}
        {error && <span className="pane-status pane-status-error"> · {error}</span>}
      </div>
      <DeckGL initialViewState={INITIAL_VIEW_STATE} controller layers={layers}>
        <MapLibreMap mapStyle={MAP_STYLE} />
      </DeckGL>
      <div className="playback-controls">
        <button
          type="button"
          onClick={() => setPlaying((p) => !p)}
          disabled={timeline.length === 0}
        >
          {playing ? "Pause" : "Play"}
        </button>
        <input
          type="range"
          min={0}
          max={Math.max(timeline.length - 1, 0)}
          value={index}
          onChange={(e) => {
            setPlaying(false);
            setIndex(Number(e.target.value));
          }}
          disabled={timeline.length === 0}
        />
        <span className="playback-time">
          {current ? new Date(current.detected_at).toLocaleString() : "—"}
        </span>
      </div>
    </div>
  );
}
