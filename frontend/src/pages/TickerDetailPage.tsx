import { useEffect, useState } from "react";
import { fetchTickerReport } from "../api/client";
import { ReportSection } from "../components/ReportSection";
import { SourceSummary } from "../components/SourceSummary";
import type { TickerReport } from "../types";

type TickerDetailPageProps = {
  ticker: string;
};

function valueText(value: unknown) {
  if (value === null || value === undefined || value === "") return "N/A";
  return String(value);
}

export function TickerDetailPage({ ticker }: TickerDetailPageProps) {
  const [report, setReport] = useState<TickerReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchTickerReport(ticker)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load ticker report"));
  }, [ticker]);

  if (error) {
    return (
      <main className="page">
        <div className="panel" role="alert">
          No analysis found for this ticker.
        </div>
      </main>
    );
  }
  if (!report) return <main className="page"><div className="panel emptyState">Loading report...</div></main>;

  const dataWarnings = report.report.data_warnings ?? [];
  const markdownReport = report.markdown_report || "No generated report was stored for this ticker.";

  return (
    <main className="page">
      <header className="pageHeader detailHeader">
        <h1>{report.ticker}</h1>
        <a className="buttonLink" href={`/api/tickers/${encodeURIComponent(report.ticker)}/report.md`} target="_blank">
          Export Markdown
        </a>
      </header>

      <ReportSection title="Source & Freshness">
        <SourceSummary sources={report.report.source_summary ?? []} />
      </ReportSection>

      {dataWarnings.length > 0 && (
        <ReportSection title="Data Warnings">
          <ul>
            {dataWarnings.map((warning) => (
              <li key={warning}>{valueText(warning)}</li>
            ))}
          </ul>
        </ReportSection>
      )}

      <ReportSection title="Generated Report">
        <pre className="markdownReport">{markdownReport}</pre>
      </ReportSection>
    </main>
  );
}
