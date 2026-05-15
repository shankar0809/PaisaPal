import type { SourceCoverageItem } from "../types";

type FrameworkSourceCoverageProps = {
  coverage: SourceCoverageItem[];
};

function sourceText(item: SourceCoverageItem) {
  if (item.matched_sources.length === 0) return "No matched sources";
  return item.matched_sources.map((source) => source.label).join(", ");
}

function warningText(warnings: string[]) {
  return warnings.length === 0 ? "None" : warnings.join(", ");
}

export function FrameworkSourceCoverage({ coverage }: FrameworkSourceCoverageProps) {
  if (coverage.length === 0) {
    return <p>No framework source coverage was stored for this report.</p>;
  }

  return (
    <div className="tablePanel">
      <table>
        <thead>
          <tr>
            <th>Framework Section</th>
            <th>Status</th>
            <th>Matched Sources</th>
            <th>Warnings</th>
          </tr>
        </thead>
        <tbody>
          {coverage.map((item) => (
            <tr key={item.section}>
              <td>{item.section}</td>
              <td>{item.status}</td>
              <td>{sourceText(item)}</td>
              <td>{warningText(item.warnings)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
