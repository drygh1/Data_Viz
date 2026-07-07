import { type FormEvent, useState } from "react";
import { QueryError, postQuery } from "../../client/api";
import { useFishfinderStore } from "../../state/store";

export function QueryBar() {
  const { setFilter, lastSql } = useFishfinderStore();
  const [text, setText] = useState("");
  const [sql, setSql] = useState<string | null>(lastSql);
  const [rowCount, setRowCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await postQuery(text);
      setSql(result.sql);
      setRowCount(result.row_count);
      setFilter(result.signals, result.sql);
    } catch (err) {
      if (err instanceof QueryError) {
        setSql(err.sql || null);
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Query failed");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setText("");
    setSql(null);
    setRowCount(null);
    setError(null);
    setFilter(null, null);
  }

  return (
    <div className="pane pane-query">
      <form className="query-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. fish that visited BigEddy after June 20"
          className="query-input"
        />
        <button type="submit" disabled={loading || !text.trim()}>
          {loading ? "Running…" : "Filter"}
        </button>
        <button type="button" onClick={handleClear} disabled={loading}>
          Clear
        </button>
      </form>
      {rowCount !== null && !error && <div className="query-status">{rowCount} fish matched</div>}
      {error && <div className="query-status query-status-error">{error}</div>}
      {sql && (
        <pre className="sql-preview">
          <code>{sql}</code>
        </pre>
      )}
    </div>
  );
}
