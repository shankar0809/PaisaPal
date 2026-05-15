import type { AnalysisJob } from "../types";

type JobStatusTableProps = {
  jobs: AnalysisJob[];
  onOpenTicker: (ticker: string) => void;
};

function formatStatus(status: string): string {
  return status.replaceAll("_", " ");
}

export function JobStatusTable({ jobs, onOpenTicker }: JobStatusTableProps) {
  if (jobs.length === 0) return <p className="emptyState">No jobs yet.</p>;

  return (
    <section className="panel tablePanel">
      <table>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Status</th>
            <th>Error</th>
            <th>Report</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>{job.ticker}</td>
              <td>{formatStatus(job.status)}</td>
              <td>{job.error_message ?? ""}</td>
              <td>
                {job.status === "complete" && (
                  <button
                    type="button"
                    aria-label={`Open ${job.ticker} report`}
                    onClick={() => onOpenTicker(job.ticker)}
                  >
                    Open
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
