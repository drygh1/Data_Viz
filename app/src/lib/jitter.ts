// Deterministic small offset so multiple fish at the same receiver don't
// render on top of each other, without jumping around on re-render/refetch
// (App.md).

const JITTER_RADIUS_DEG = 0.0015; // ~150m at Kenai River latitudes

function hashString(input: string): number {
  let hash = 2166136261;
  for (let i = 0; i < input.length; i++) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

export function jitterPosition(
  lat: number,
  lon: number,
  signal: string,
  array: string,
): [number, number] {
  const hash = hashString(`${signal}:${array}`);
  const angle = ((hash % 3600) / 3600) * 2 * Math.PI;
  const radiusFraction = ((hash >>> 12) % 1000) / 1000;
  const radius = JITTER_RADIUS_DEG * (0.3 + 0.7 * radiusFraction);
  return [lon + radius * Math.cos(angle), lat + radius * Math.sin(angle)];
}
