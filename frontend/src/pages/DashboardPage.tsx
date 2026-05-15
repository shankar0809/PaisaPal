import { useEffect, useMemo, useState } from "react";
import { fetchWatchlist } from "../api/client";
import { WatchlistTable } from "../components/WatchlistTable";
import type { WatchlistRow } from "../types";

export function DashboardPage() {
  const [rows, setRows] = useState<WatchlistRow[]>([]);
  const [decision, setDecision] = useState("");
  const [technical, setTechnical] = useState("");
  const [fundamentals, setFundamentals] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [sort, setSort] = useState("updated_desc");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (decision) params.set("decision", decision);
    if (technical) params.set("technical", technical);
    if (fundamentals) params.set("fundamentals", fundamentals);
    if (sentiment) params.set("sentiment", sentiment);
    if (sort) params.set("sort", sort);

    fetchWatchlist(params)
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load watchlist"));
  }, [decision, fundamentals, sentiment, sort, technical]);

  const decisions = useMemo(() => [...new Set(rows.map((row) => row.final_decision))], [rows]);
  const technicals = useMemo(() => [...new Set(rows.map((row) => row.technical_rating))], [rows]);
  const fundamentalRatings = useMemo(
    () => [...new Set(rows.map((row) => row.fundamental_rating))],
    [rows]
  );
  const sentimentRatings = useMemo(() => [...new Set(rows.map((row) => row.sentiment_rating))], [rows]);

  return (
    <main className="page">
      <header className="pageHeader">
        <h1>Dashboard</h1>
      </header>
      <section className="panel filters">
        <label>
          Decision
          <select value={decision} onChange={(event) => setDecision(event.target.value)}>
            <option value="">All</option>
            {decisions.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Technical
          <select value={technical} onChange={(event) => setTechnical(event.target.value)}>
            <option value="">All</option>
            {technicals.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Fundamentals
          <select value={fundamentals} onChange={(event) => setFundamentals(event.target.value)}>
            <option value="">All</option>
            {fundamentalRatings.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Sentiment
          <select value={sentiment} onChange={(event) => setSentiment(event.target.value)}>
            <option value="">All</option>
            {sentimentRatings.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Sort
          <select value={sort} onChange={(event) => setSort(event.target.value)}>
            <option value="updated_desc">Updated time</option>
            <option value="ticker">Ticker</option>
            <option value="risk_reward">Risk/reward</option>
            <option value="confidence">Confidence</option>
          </select>
        </label>
      </section>
      {error && <div className="panel" role="alert">{error}</div>}
      <WatchlistTable rows={rows} onOpenTicker={(ticker) => (window.location.hash = `#/ticker/${ticker}`)} />
    </main>
  );
}
