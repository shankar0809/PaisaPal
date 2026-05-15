import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DashboardPage } from "./DashboardPage";

vi.mock("../api/client", () => ({
  fetchWatchlist: async () => [
    {
      id: 1,
      ticker: "MSFT",
      current_price: 420,
      final_decision: "Buy / Enter",
      confidence: "High",
      technical_rating: "High-quality VCP",
      fundamental_rating: "Elite fundamentals",
      earnings_rating: "Clean setup",
      sentiment_rating: "Bullish and improving",
      options_flow_rating: "Bullish leaning",
      risk_reward: 2,
      created_at: "2026-05-14T18:00:00Z"
    }
  ]
}));

describe("DashboardPage", () => {
  it("renders watchlist rows and filters", async () => {
    render(<DashboardPage />);

    expect(await screen.findByText("MSFT")).toBeInTheDocument();
    expect(screen.getByText("Classification")).toBeInTheDocument();
    expect(screen.getByText("Earnings")).toBeInTheDocument();
    expect(screen.getByText("Updated")).toBeInTheDocument();
    expect(screen.getAllByText("Buy / Enter").length).toBeGreaterThan(0);
    expect(screen.getByText("Clean setup")).toBeInTheDocument();
    expect(screen.getByText("2.00")).toBeInTheDocument();
    expect(screen.getByLabelText("Decision")).toBeInTheDocument();
    expect(screen.getByLabelText("Sort")).toBeInTheDocument();
  });
});
