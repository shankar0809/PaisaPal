import type { SourceSummaryItem } from "../types";

type SourceSummaryProps = {
  sources: SourceSummaryItem[];
};

function warningText(warnings: string[]) {
  return warnings.length === 0 ? "None" : warnings.join(", ");
}

function safeSourceUrl(url: string | null) {
  if (!url) return null;

  try {
    const parsedUrl = new URL(url);
    return parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:" ? url : null;
  } catch {
    return null;
  }
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
          {sources.map((source) => {
            const sourceUrl = safeSourceUrl(source.url);

            return (
              <tr key={`${source.provider}-${source.label}-${source.retrieved_at}`}>
                <td>{source.provider}</td>
                <td>{source.status}</td>
                <td>
                  {sourceUrl ? (
                    <a href={sourceUrl} target="_blank" rel="noreferrer">
                      {source.label}
                    </a>
                  ) : (
                    source.label
                  )}
                </td>
                <td>{warningText(source.warnings)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
