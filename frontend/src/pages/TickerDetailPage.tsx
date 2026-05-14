import { useEffect, useState } from "react";
import { fetchTickerReport } from "../api/client";
import { ReportSection } from "../components/ReportSection";
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

  const input = report.report.input;
  const analysis = report.report.analysis;

  return (
    <main className="page">
      <header className="pageHeader detailHeader">
        <h1>{report.ticker}</h1>
        <a className="buttonLink" href={`/api/tickers/${encodeURIComponent(report.ticker)}/report.md`} target="_blank">
          Export Markdown
        </a>
      </header>
      <ReportSection title="Current Stock Context">
        <dl>
          <dt>Current Price</dt>
          <dd>{valueText(input.current_price)}</dd>
          <dt>Context Rating</dt>
          <dd>{valueText(analysis.context_rating)}</dd>
        </dl>
      </ReportSection>
      <ReportSection title="Technical Setup">
        <dl>
          <dt>VCP Rating</dt>
          <dd>{valueText(analysis.vcp_rating)}</dd>
          <dt>VCP Score</dt>
          <dd>{valueText(analysis.vcp_score)}</dd>
        </dl>
      </ReportSection>
      <ReportSection title="Trade Plan">
        <dl>
          <dt>Risk/Reward</dt>
          <dd>{valueText(analysis.risk_reward)}</dd>
          <dt>Position Size</dt>
          <dd>{valueText(analysis.position_size)}</dd>
        </dl>
      </ReportSection>
      <ReportSection title="Fundamentals">
        <p>{valueText(analysis.fundamental_rating)}</p>
      </ReportSection>
      <ReportSection title="Market Sentiment">
        <p>{valueText(analysis.sentiment_rating)}</p>
      </ReportSection>
      <ReportSection title="Options Flow">
        <p>{valueText(analysis.options_flow_rating)}</p>
      </ReportSection>
      <ReportSection title="LEAP Analysis">
        <p>LEAP import is not enabled in v1</p>
      </ReportSection>
      <ReportSection title="Earnings Implied Move">
        <p>Earnings import is not enabled in v1</p>
      </ReportSection>
      <ReportSection title="Final Directional Recommendation">
        <p>{valueText(analysis.final_decision)}</p>
      </ReportSection>
    </main>
  );
}
