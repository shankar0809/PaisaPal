import type { TickerReport } from "../types";

type AnalysisStep = NonNullable<TickerReport["report"]["analysis_steps"]>[number];

type AnalysisStepsProps = {
  steps: AnalysisStep[];
};

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "N/A";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function AnalysisSteps({ steps }: AnalysisStepsProps) {
  if (steps.length === 0) {
    return <p>No step details were stored for this report.</p>;
  }

  return (
    <div className="analysisSteps">
      {steps.map((step) => (
        <details key={step.section} className="analysisStep">
          <summary>
            <span>{step.section}</span>
            <span className={`stepStatus ${step.status}`}>{step.status}</span>
          </summary>
          <div className="analysisStepBody">
            <p>{step.summary}</p>
            <div className="analysisStepGrid">
              <div>
                <span className="statusMetricLabel">Results</span>
                <ul>
                  {Object.entries(step.results).map(([key, value]) => (
                    <li key={key}>
                      <strong>{key}</strong>: {formatValue(value)}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <span className="statusMetricLabel">Sources</span>
                <ul>
                  {step.sources.length === 0 ? (
                    <li>None</li>
                  ) : (
                    step.sources.map((source) => (
                      <li key={`${source.provider}-${source.label}`}>
                        {source.provider}: {source.label} ({source.status})
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>
            {step.warnings.length > 0 && (
              <div>
                <span className="statusMetricLabel">Warnings</span>
                <ul>
                  {step.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </details>
      ))}
    </div>
  );
}
