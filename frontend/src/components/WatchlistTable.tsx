import type { WatchlistRow } from "../types";
import { DecisionBadge } from "./DecisionBadge";

type WatchlistTableProps = {
  rows: WatchlistRow[];
  onOpenTicker?: (ticker: string) => void;
};

export function WatchlistTable({ rows, onOpenTicker }: WatchlistTableProps) {
  if (rows.length === 0) {
    return <div className="panel emptyState">Import a CSV watchlist to start analyzing tickers.</div>;
  }

  return (
    <div className="panel tablePanel">
      <table>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Price</th>
            <th>Decision</th>
            <th>Confidence</th>
            <th>Technical</th>
            <th>Fundamentals</th>
            <th>Sentiment</th>
            <th>Options</th>
            <th>Risk/Reward</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} onClick={() => onOpenTicker?.(row.ticker)} className="clickableRow">
              <td>{row.ticker}</td>
              <td>{row.current_price.toFixed(2)}</td>
              <td>
                <DecisionBadge decision={row.final_decision} />
              </td>
              <td>{row.confidence}</td>
              <td>{row.technical_rating}</td>
              <td>{row.fundamental_rating}</td>
              <td>{row.sentiment_rating}</td>
              <td>{row.options_flow_rating}</td>
              <td>{row.risk_reward === null ? "N/A" : row.risk_reward.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
