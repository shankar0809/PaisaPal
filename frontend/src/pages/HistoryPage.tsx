import { useEffect, useState } from "react";
import { fetchLatestAnalysisRunForTicker } from "../api/client";
import { RunStatusPanel } from "../components/RunStatusPanel";
import { ReportSection } from "../components/ReportSection";
import type { AnalysisRun } from "../types";

type HistoryPageProps = {
  ticker?: string;
};

const TERMINAL_STATUSES = new Set(["complete", "failed", "partial"]);

function formatStatus(status: string) {
  return status.replaceAll("_", " ");
}

export function HistoryPage({ ticker = "MSFT" }: HistoryPageProps) {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    let timer: number | undefined;

    const load = () => {
      fetchLatestAnalysisRunForTicker(ticker)
        .then((nextRun) => {
          if (!active) return;
          setRun(nextRun);
          setError("");
          if (!TERMINAL_STATUSES.has(nextRun.status)) {
            timer = window.setTimeout(load, 2000);
          }
        })
        .catch((err) => {
          if (!active) return;
          setRun(null);
          setError(err instanceof Error ? err.message : "Failed to load latest analysis run");
        });
    };

    load();
    return () => {
      active = false;
      if (timer !== undefined) {
        window.clearTimeout(timer);
      }
    };
  }, [ticker]);

  return (
    <main className="page">
      <header className="pageHeader">
        <h1>{ticker} Status</h1>
      </header>
      {error && <div className="panel" role="alert">{error}</div>}
      {!error && !run && <div className="panel emptyState">No analysis run found for this ticker.</div>}
      {run && (
        <ReportSection title="Current Analysis Run">
          <RunStatusPanel run={run} running={!TERMINAL_STATUSES.has(run.status)} />
          <div className="statusDetailGrid">
            <div>
              <span className="statusMetricLabel">Run ID</span>
              <div>{run.id}</div>
            </div>
            <div>
              <span className="statusMetricLabel">Created</span>
              <div>{new Date(run.created_at).toLocaleString()}</div>
            </div>
            <div>
              <span className="statusMetricLabel">Tickers</span>
              <div>{run.tickers.join(", ")}</div>
            </div>
          </div>
          <div className="tablePanel">
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Status</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {run.jobs.map((job) => (
                <tr key={job.id}>
                  <td>{job.ticker}</td>
                  <td>{formatStatus(job.status)}</td>
                  <td>{job.error_message ?? "None"}</td>
                </tr>
              ))}
              </tbody>
            </table>
          </div>
        </ReportSection>
      )}
    </main>
  );
}
