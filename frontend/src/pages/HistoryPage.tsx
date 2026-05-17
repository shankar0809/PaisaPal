import { useEffect, useMemo, useState } from "react";
import { fetchAnalysisRuns } from "../api/client";
import { ReportSection } from "../components/ReportSection";
import type { AnalysisRun } from "../types";

const TERMINAL_STATUSES = new Set(["complete", "failed", "partial"]);

function formatStatus(status: string) {
  return status.replaceAll("_", " ");
}

function countJobs(run: AnalysisRun) {
  const complete = run.jobs.filter((job) => job.status === "complete").length;
  const failed = run.jobs.filter((job) => job.status === "failed").length;
  const active = run.jobs.length - complete - failed;
  return { complete, failed, active };
}

export function HistoryPage() {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    let timer: number | undefined;

    const load = () => {
      fetchAnalysisRuns()
        .then((nextRuns) => {
          if (!active) return;
          setRuns(nextRuns);
          setError("");
          if (nextRuns.some((run) => !TERMINAL_STATUSES.has(run.status))) {
            timer = window.setTimeout(load, 2000);
          }
        })
        .catch((err) => {
          if (!active) return;
          setRuns([]);
          setError(err instanceof Error ? err.message : "Failed to load analysis runs");
        });
    };

    load();
    return () => {
      active = false;
      if (timer !== undefined) {
        window.clearTimeout(timer);
      }
    };
  }, []);

  const rows = useMemo(
    () =>
      runs.map((run) => {
        const counts = countJobs(run);
        return { run, counts };
      }),
    [runs]
  );

  return (
    <main className="page">
      <header className="pageHeader">
        <h1>Status</h1>
      </header>
      {error && <div className="panel" role="alert">{error}</div>}
      {!error && runs.length === 0 && <div className="panel emptyState">No analysis runs yet.</div>}
      {runs.length > 0 && (
        <ReportSection title="Recent Analysis Runs">
          <div className="tablePanel">
            <table>
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Tickers</th>
                  <th>Status</th>
                  <th>Jobs</th>
                  <th>Created</th>
                  <th>Open</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ run, counts }) => (
                  <tr key={run.id}>
                    <td>#{run.id}</td>
                    <td>{run.tickers.join(", ")}</td>
                    <td>{formatStatus(run.status)}</td>
                    <td>
                      {counts.complete} complete, {counts.active} active, {counts.failed} failed
                    </td>
                    <td>{new Date(run.created_at).toLocaleString()}</td>
                    <td>
                      <button
                        type="button"
                        onClick={() => {
                          window.location.hash = `#/runs/${run.id}`;
                        }}
                      >
                        Open
                      </button>
                    </td>
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
