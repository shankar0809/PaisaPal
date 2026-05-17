import { useEffect, useState } from "react";
import { fetchTickerReport } from "../api/client";
import { AnalysisSteps } from "../components/AnalysisSteps";
import { FrameworkSourceCoverage } from "../components/FrameworkSourceCoverage";
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
  const analysisSteps = report.report.analysis_steps ?? [];
  const vcpSummary = report.report.vcp_summary;
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

      <ReportSection title="VCP Summary">
        {vcpSummary ? (
          <dl className="summaryGrid">
            <div>
              <dt>Ticker</dt>
              <dd>{valueText(vcpSummary.ticker)}</dd>
            </div>
            <div>
              <dt>VCP Score</dt>
              <dd>{valueText(vcpSummary.vcp_score)}</dd>
            </div>
            <div>
              <dt>Stage</dt>
              <dd>{valueText(vcpSummary.vcp_stage)}</dd>
            </div>
            <div>
              <dt>Tech Output</dt>
              <dd>{valueText(vcpSummary.tech_output)}</dd>
            </div>
            <div>
              <dt>VCP Rating</dt>
              <dd>{valueText(vcpSummary.vcp_rating)}</dd>
            </div>
          </dl>
        ) : (
          <p>No VCP summary was stored for this report.</p>
        )}
      </ReportSection>

      <ReportSection title="Framework Source Coverage">
        <FrameworkSourceCoverage coverage={report.source_coverage ?? []} />
      </ReportSection>

      <ReportSection title="Analysis Step Results">
        <AnalysisSteps steps={analysisSteps} />
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
