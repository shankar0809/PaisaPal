import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TickerDetailPage } from "./TickerDetailPage";

vi.mock("../api/client", () => ({
  fetchTickerReport: async () => ({
    ticker: "MSFT",
    report: {
      ticker: "MSFT",
      company_name: "Microsoft Corp.",
      current_price: 420,
      final_classification: "Buy / Enter",
      confidence: "High",
      technical_rating: "High-quality VCP",
      vcp_rating: "Constructive",
      fundamental_rating: "Elite fundamentals",
      earnings_rating: "Clean setup",
      sentiment_rating: "Bullish and improving",
      options_flow_rating: "Bullish leaning",
      data_warnings: ["Options flow provider returned stale data"],
      source_summary: [
        {
          provider: "polygon",
          retrieved_at: "2026-05-14T18:00:00Z",
          status: "ok",
          label: "Polygon market data",
          url: "https://example.test/polygon",
          warnings: []
        }
      ],
      input: { ticker: "MSFT", current_price: 420 },
      analysis: { final_decision: "Buy / Enter" }
    },
    markdown_report: "# MSFT Investment Analysis\n\nAI-generated thesis.",
    created_at: "2026-05-14T18:00:00Z"
  })
}));

describe("TickerDetailPage", () => {
  it("renders AI source freshness, data warnings, and generated markdown", async () => {
    render(<TickerDetailPage ticker="MSFT" />);

    expect(await screen.findByText("MSFT")).toBeInTheDocument();
    expect(screen.getByText("Source & Freshness")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Polygon market data" })).toHaveAttribute(
      "href",
      "https://example.test/polygon"
    );
    expect(screen.getByText("Data Warnings")).toBeInTheDocument();
    expect(screen.getByText("Options flow provider returned stale data")).toBeInTheDocument();
    expect(screen.getByText("Generated Report")).toBeInTheDocument();
    expect(screen.getByText(/AI-generated thesis/)).toBeInTheDocument();
  });
});
