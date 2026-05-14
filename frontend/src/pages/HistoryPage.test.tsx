import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HistoryPage } from "./HistoryPage";

vi.mock("../api/client", () => ({
  fetchTickerHistory: async () => [
    {
      id: 1,
      ticker: "MSFT",
      final_decision: "Buy / Enter",
      confidence: "High",
      risk_reward: 2.0,
      created_at: "2026-05-14T18:00:00Z"
    }
  ]
}));

describe("HistoryPage", () => {
  it("renders prior snapshot rows", async () => {
    render(<HistoryPage ticker="MSFT" />);

    expect(await screen.findByText("MSFT History")).toBeInTheDocument();
    expect(screen.getByText("Buy / Enter")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
  });
});
