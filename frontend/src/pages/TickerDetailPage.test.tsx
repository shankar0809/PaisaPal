import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TickerDetailPage } from "./TickerDetailPage";

vi.mock("../api/client", () => ({
  fetchTickerReport: async () => ({
    ticker: "MSFT",
    report: {
      input: { ticker: "MSFT", current_price: 420 },
      analysis: {
        context_rating: "Constructive consolidation",
        vcp_rating: "High-quality VCP",
        fundamental_rating: "Elite fundamentals",
        sentiment_rating: "Bullish and improving",
        options_flow_rating: "Bullish leaning",
        final_decision: "Buy / Enter"
      }
    },
    markdown_report: "# MSFT Investment Analysis",
    created_at: "2026-05-14T18:00:00Z"
  })
}));

describe("TickerDetailPage", () => {
  it("renders framework sections and final decision", async () => {
    render(<TickerDetailPage ticker="MSFT" />);

    expect(await screen.findByText("MSFT")).toBeInTheDocument();
    expect(screen.getByText("Current Stock Context")).toBeInTheDocument();
    expect(screen.getByText("Technical Setup")).toBeInTheDocument();
    expect(screen.getByText("Final Directional Recommendation")).toBeInTheDocument();
    expect(screen.getByText("Buy / Enter")).toBeInTheDocument();
  });
});
