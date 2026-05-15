import { createAnalysisRun, type CreateAnalysisRunPayload } from "../api/client";
import { TickerInputPanel } from "../components/TickerInputPanel";

export function AnalyzePage() {
  async function onSubmit(payload: CreateAnalysisRunPayload) {
    const run = await createAnalysisRun(payload);
    window.location.hash = `#/runs/${run.id}`;
  }

  return (
    <main className="page">
      <header className="pageHeader">
        <h1>Analyze</h1>
      </header>
      <TickerInputPanel onSubmit={onSubmit} />
    </main>
  );
}
