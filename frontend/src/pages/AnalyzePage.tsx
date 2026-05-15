import { useEffect, useState } from "react";
import { createAnalysisRun, fetchProviderStatus, type CreateAnalysisRunPayload } from "../api/client";
import { ProviderReadiness } from "../components/ProviderReadiness";
import { TickerInputPanel } from "../components/TickerInputPanel";
import type { ProviderStatus } from "../types";

export function AnalyzePage() {
  const [providers, setProviders] = useState<ProviderStatus[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetchProviderStatus()
      .then((loaded) => {
        if (!cancelled) setProviders(loaded);
      })
      .catch(() => {
        if (!cancelled) setProviders([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(payload: CreateAnalysisRunPayload) {
    const run = await createAnalysisRun(payload);
    window.location.hash = `#/runs/${run.id}`;
  }

  return (
    <main className="page">
      <header className="pageHeader">
        <h1>Analyze</h1>
      </header>
      <ProviderReadiness providers={providers} />
      <TickerInputPanel onSubmit={onSubmit} />
    </main>
  );
}
