import { useEffect, useState } from "react";
import { fetchAnalysisRun, runMockAnalysis } from "../api/client";
import { JobStatusTable } from "../components/JobStatusTable";
import type { AnalysisRun } from "../types";

type RunProgressPageProps = {
  runId: number;
};

export function RunProgressPage({ runId }: RunProgressPageProps) {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState("");
  const [runningMock, setRunningMock] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadRun() {
      try {
        const loadedRun = await fetchAnalysisRun(runId);
        if (!cancelled) setRun(loadedRun);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load analysis run");
      }
    }
    loadRun();
    return () => {
      cancelled = true;
    };
  }, [runId]);

  async function onRunMockAnalysis() {
    setError("");
    setRunningMock(true);
    try {
      setRun(await runMockAnalysis(runId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run mock analysis");
    } finally {
      setRunningMock(false);
    }
  }

  function onOpenTicker(ticker: string) {
    window.location.hash = `#/ticker/${ticker}`;
  }

  if (error && !run) {
    return (
      <main className="page">
        <p role="alert">{error}</p>
      </main>
    );
  }

  if (!run) {
    return (
      <main className="page">
        <p>Loading analysis run...</p>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="pageHeader">
        <h1>Analysis Run #{run.id}</h1>
      </header>
      <div className="actions">
        <button type="button" onClick={onRunMockAnalysis} disabled={runningMock}>
          Run Mock Analysis
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
      <JobStatusTable jobs={run.jobs} onOpenTicker={onOpenTicker} />
    </main>
  );
}
