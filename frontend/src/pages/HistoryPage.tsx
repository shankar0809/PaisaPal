import { useEffect, useState } from "react";
import { fetchTickerHistory } from "../api/client";
import type { HistoryRow } from "../types";

type HistoryPageProps = {
  ticker?: string;
};

export function HistoryPage({ ticker = "MSFT" }: HistoryPageProps) {
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchTickerHistory(ticker)
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load ticker history"));
  }, [ticker]);

  return (
    <main className="page">
      <header className="pageHeader">
        <h1>{ticker} History</h1>
      </header>
      {error && <div className="panel" role="alert">{error}</div>}
      <div className="panel tablePanel">
        <table>
          <thead>
            <tr>
              <th>Snapshot</th>
              <th>Decision</th>
              <th>Confidence</th>
              <th>Risk/Reward</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{new Date(row.created_at).toLocaleString()}</td>
                <td>{row.final_decision}</td>
                <td>{row.confidence}</td>
                <td>{row.risk_reward === null ? "N/A" : row.risk_reward.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
