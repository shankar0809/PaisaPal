import { useEffect, useState } from "react";
import { fetchAnalysisRun, runAnalysis } from "../api/client";
import { JobStatusTable } from "../components/JobStatusTable";
import { RunStatusPanel } from "../components/RunStatusPanel";
import type { AnalysisRun } from "../types";

type RunProgressPageProps = {
  runId: number;
};

export function RunProgressPage({ runId }: RunProgressPageProps) {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

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

  useEffect(() => {
    if (!running) return undefined;
    let cancelled = false;
    async function pollRun() {
      try {
        const loadedRun = await fetchAnalysisRun(runId);
        if (!cancelled) setRun(loadedRun);
      } catch {
        // Keep the in-flight run request as the source of truth for terminal errors.
      }
    }
    pollRun();
    const intervalId = window.setInterval(async () => {
      await pollRun();
    }, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [runId, running]);

  async function onRunAnalysis() {
    setError("");
    setRunning(true);
    try {
      setRun(await runAnalysis(runId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run analysis");
    } finally {
      setRunning(false);
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
        <button type="button" onClick={onRunAnalysis} disabled={running}>
          {running ? "Running..." : "Run Analysis"}
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
      <RunStatusPanel run={run} running={running} />
      <JobStatusTable jobs={run.jobs} onOpenTicker={onOpenTicker} />
    </main>
  );
}
