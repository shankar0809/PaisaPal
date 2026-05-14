type DecisionBadgeProps = {
  decision: string;
};

export function DecisionBadge({ decision }: DecisionBadgeProps) {
  const tone = decision.toLowerCase().includes("buy")
    ? "positive"
    : decision.toLowerCase().includes("avoid")
      ? "negative"
      : "neutral";

  return <span className={`badge ${tone}`}>{decision}</span>;
}
