import type { AnalysisJob, AnalysisRun } from "../types";

type RunStatusPanelProps = {
  run: AnalysisRun;
  running: boolean;
};

const ACTIVE_STATUSES = new Set([
  "fetching_market_data",
  "fetching_fundamentals",
  "fetching_earnings",
  "fetching_options",
  "running_web_research",
  "running_gpt_analysis"
]);

function formatStatus(status: string): string {
  return status.replaceAll("_", " ");
}

function activeJobs(jobs: AnalysisJob[]): AnalysisJob[] {
  return jobs.filter((job) => ACTIVE_STATUSES.has(job.status));
}

export function RunStatusPanel({ run, running }: RunStatusPanelProps) {
  const completeCount = run.jobs.filter((job) => job.status === "complete").length;
  const failedCount = run.jobs.filter((job) => job.status === "failed").length;
  const active = activeJobs(run.jobs);
  const activeLabel = active.length > 0
    ? `${active.length} of ${run.jobs.length} active`
    : `${completeCount} of ${run.jobs.length} complete`;
  const phase = active[0]?.status ?? run.status;

  return (
    <section className="panel runStatusPanel" aria-label="Run Status">
      <div>
        <h2>Run Status</h2>
        <p className="statusLine">{formatStatus(run.status)}</p>
      </div>
      <div>
        <span className="statusMetric">{activeLabel}</span>
        {failedCount > 0 && <span className="statusMetric errorMetric">{failedCount} failed</span>}
      </div>
      <div>
        <span className={running || active.length > 0 ? "statusDot active" : "statusDot"} aria-hidden="true" />
        <span>{formatStatus(phase)}</span>
      </div>
    </section>
  );
}
