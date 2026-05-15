import type { ProviderStatus } from "../types";

type ProviderReadinessProps = {
  providers: ProviderStatus[];
};

function providerLabel(provider: string) {
  return provider.replace("_", " ");
}

export function ProviderReadiness({ providers }: ProviderReadinessProps) {
  if (providers.length === 0) {
    return (
      <section className="panel">
        <h2>Live Readiness</h2>
        <p>Provider readiness is unavailable.</p>
      </section>
    );
  }

  const message = providers[0].message;
  const liveReady = providers[0].live_ready;

  return (
    <section className="panel">
      <h2>Live Readiness</h2>
      <p>{message}</p>
      <div className="providerGrid">
        {providers.map((provider) => (
          <div className="providerPill" key={provider.provider}>
            <strong>{provider.provider}</strong>
            <span>{providerLabel(provider.role)}</span>
            <span>{provider.configured ? "configured" : "missing"}</span>
          </div>
        ))}
      </div>
      {!liveReady && <p>Runs will use whatever live inputs are available and fall back where needed.</p>}
    </section>
  );
}
