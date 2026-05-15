import type { SourceSummaryItem } from "../types";

type SourceSummaryProps = {
  sources: SourceSummaryItem[];
};

function warningText(warnings: string[]) {
  return warnings.length === 0 ? "None" : warnings.join(", ");
}

export function SourceSummary({ sources }: SourceSummaryProps) {
  if (sources.length === 0) {
    return <p>No source summary was stored for this report.</p>;
  }

  return (
    <div className="tablePanel">
      <table>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Status</th>
            <th>Label</th>
            <th>Warnings</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((source) => (
            <tr key={`${source.provider}-${source.label}-${source.retrieved_at}`}>
              <td>{source.provider}</td>
              <td>{source.status}</td>
              <td>
                {source.url ? (
                  <a href={source.url} target="_blank" rel="noreferrer">
                    {source.label}
                  </a>
                ) : (
                  source.label
                )}
              </td>
              <td>{warningText(source.warnings)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
