import { Play } from "lucide-react";
import { FormEvent, useState } from "react";
import type { CreateAnalysisRunPayload } from "../api/client";

type TickerInputPanelProps = {
  onSubmit: (payload: CreateAnalysisRunPayload) => Promise<void> | void;
};

function parseTickers(value: string): string[] {
  return value
    .split(/[\s,]+/)
    .map((ticker) => ticker.trim().toUpperCase())
    .filter(Boolean);
}

export function TickerInputPanel({ onSubmit }: TickerInputPanelProps) {
  const [tickers, setTickers] = useState("");
  const [accountSize, setAccountSize] = useState(100000);
  const [riskPercent, setRiskPercent] = useState(0.5);
  const [maxDollarRisk, setMaxDollarRisk] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsedTickers = parseTickers(tickers);
    if (parsedTickers.length === 0) {
      setError("Enter at least one ticker.");
      return;
    }

    setError("");
    setSubmitting(true);
    try {
      await onSubmit({
        tickers: parsedTickers,
        account_size: accountSize,
        risk_percent: riskPercent,
        max_dollar_risk: maxDollarRisk === "" ? null : Number(maxDollarRisk),
        notes
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis run failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="panel formPanel" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="analysis-tickers">Tickers</label>
        <textarea
          id="analysis-tickers"
          rows={5}
          value={tickers}
          onChange={(event) => setTickers(event.target.value)}
        />
      </div>
      <div className="field">
        <label htmlFor="account-size">Account size</label>
        <input
          id="account-size"
          min="0"
          type="number"
          value={accountSize}
          onChange={(event) => setAccountSize(Number(event.target.value))}
        />
      </div>
      <div className="field">
        <label htmlFor="risk-percent">Risk percent</label>
        <select
          id="risk-percent"
          value={riskPercent}
          onChange={(event) => setRiskPercent(Number(event.target.value))}
        >
          <option value="0.25">0.25%</option>
          <option value="0.5">0.5%</option>
          <option value="1">1%</option>
        </select>
      </div>
      <div className="field">
        <label htmlFor="max-dollar-risk">Max dollar risk</label>
        <input
          id="max-dollar-risk"
          min="0"
          type="number"
          value={maxDollarRisk}
          onChange={(event) => setMaxDollarRisk(event.target.value)}
        />
      </div>
      <div className="field">
        <label htmlFor="analysis-notes">Notes</label>
        <textarea
          id="analysis-notes"
          rows={4}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
        />
      </div>
      <div className="actions">
        <button type="submit" disabled={submitting}>
          <Play size={16} />
          Run Analysis
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
