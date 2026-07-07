export interface Visit {
  signal: string;
  array: string;
  arrived_at: string;
  departed_at: string;
  ping_count: number;
  lat: number | null;
  lon: number | null;
  rkm: number | null;
}

export interface TimelinePoint {
  detected_at: string;
  array: string;
  receiver_id: string;
  lat: number | null;
  lon: number | null;
}

export interface TimelinePointWithSignal extends TimelinePoint {
  signal: string;
}

export interface QueryResult {
  sql: string;
  signals: string[];
  row_count: number;
}

export class QueryError extends Error {
  sql: string;

  constructor(message: string, sql: string) {
    super(message);
    this.name = "QueryError";
    this.sql = sql;
  }
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    if (response.status === 422) {
      const body = (await response.json()) as { detail?: { sql?: string; error?: string } };
      throw new QueryError(body.detail?.error ?? "Query failed", body.detail?.sql ?? "");
    }
    throw new Error(`Request to ${url} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getVisits(signals?: string[]): Promise<Visit[]> {
  const params =
    signals && signals.length > 0 ? `?signals=${signals.map(encodeURIComponent).join(",")}` : "";
  return fetchJson<Visit[]>(`/api/visits${params}`);
}

export function getFishTimeline(signal: string): Promise<TimelinePoint[]> {
  return fetchJson<TimelinePoint[]>(`/api/fish/${encodeURIComponent(signal)}/timeline`);
}

export function getFishTimelines(signals: string[]): Promise<TimelinePointWithSignal[]> {
  const params = signals.map(encodeURIComponent).join(",");
  return fetchJson<TimelinePointWithSignal[]>(`/api/fish/timelines?signals=${params}`);
}

export function postQuery(text: string): Promise<QueryResult> {
  return fetchJson<QueryResult>("/api/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}
