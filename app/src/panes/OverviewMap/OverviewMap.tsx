import { ScatterplotLayer } from "@deck.gl/layers";
import { DeckGL } from "@deck.gl/react";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useState } from "react";
import { Map as MapLibreMap } from "react-map-gl/maplibre";
import { type Visit, getVisits } from "../../client/api";
import { jitterPosition } from "../../lib/jitter";
import { useFishfinderStore } from "../../state/store";

const INITIAL_VIEW_STATE = {
  longitude: -151.15,
  latitude: 60.5,
  zoom: 9,
  pitch: 0,
  bearing: 0,
};

const MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

export function OverviewMap() {
  const { activeFilter, selectedFish, selectFish } = useFishfinderStore();
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getVisits(activeFilter ?? undefined)
      .then((data) => {
        if (!cancelled) setVisits(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load visits");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeFilter]);

  const points = visits.filter(
    (v): v is Visit & { lat: number; lon: number } => v.lat != null && v.lon != null,
  );

  const layer = new ScatterplotLayer<(typeof points)[number]>({
    id: "overview-points",
    data: points,
    getPosition: (v) => jitterPosition(v.lat, v.lon, v.signal, v.array),
    getRadius: 40,
    radiusMinPixels: 3,
    radiusMaxPixels: 8,
    getFillColor: (v) => (v.signal === selectedFish ? [255, 140, 0, 220] : [30, 100, 200, 160]),
    pickable: true,
    onClick: (info) => {
      if (info.object) selectFish(info.object.signal);
    },
  });

  return (
    <div className="pane pane-overview">
      <div className="pane-header">
        Overview map
        {loading && <span className="pane-status"> · loading…</span>}
        {error && <span className="pane-status pane-status-error"> · {error}</span>}
      </div>
      <DeckGL initialViewState={INITIAL_VIEW_STATE} controller layers={[layer]}>
        <MapLibreMap mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}
