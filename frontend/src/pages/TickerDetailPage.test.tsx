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
      vcp_summary: {
        ticker: "MSFT",
        vcp_score: 9,
        vcp_stage: "Stage 2",
        tech_output: "Strong VCP watchlist candidate",
        vcp_rating: "High-quality VCP",
      },
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
      analysis_steps: [
        {
          section: "Current Stock Context",
          status: "covered",
          summary: "Price $420.00, confidence High, final view Buy / Enter.",
          results: {
            current_price: "420.00",
            confidence: "High",
            final_classification: "Buy / Enter"
          },
          sources: [{ provider: "polygon", source_type: "market", status: "fresh", label: "Polygon market data" }],
          warnings: []
        }
      ],
      input: { ticker: "MSFT", current_price: 420 },
      analysis: { final_decision: "Buy / Enter" }
    },
    markdown_report: "# MSFT Investment Analysis\n\nAI-generated thesis.",
    created_at: "2026-05-14T18:00:00Z",
    source_coverage: [
      {
        section: "VCP / Technical Pattern View",
        status: "covered",
        matched_sources: [{ provider: "polygon", label: "Polygon daily bars", status: "fresh", url: null }],
        warnings: []
      },
      {
        section: "Options Flow / Implied Move",
        status: "partial",
        matched_sources: [{ provider: "polygon", label: "Polygon options chain", status: "fresh", url: null }],
        warnings: ["Options chain missing greeks"]
      }
    ]
  })
}));

describe("TickerDetailPage", () => {
  it("renders AI source freshness, step details, data warnings, and generated markdown", async () => {
    render(<TickerDetailPage ticker="MSFT" />);

    expect(await screen.findByRole("heading", { name: "MSFT" })).toBeInTheDocument();
    expect(screen.getByText("Source & Freshness")).toBeInTheDocument();
    expect(screen.getByText("Framework Source Coverage")).toBeInTheDocument();
    expect(screen.getByText("VCP Summary")).toBeInTheDocument();
    expect(screen.getByText("Analysis Step Results")).toBeInTheDocument();
    expect(screen.getByText("VCP / Technical Pattern View")).toBeInTheDocument();
    expect(screen.getByText("Current Stock Context")).toBeInTheDocument();
    expect(screen.getByText("9")).toBeInTheDocument();
    expect(screen.getByText("Stage 2")).toBeInTheDocument();
    expect(screen.getByText("Strong VCP watchlist candidate")).toBeInTheDocument();
    expect(screen.getByText("Polygon daily bars")).toBeInTheDocument();
    expect(screen.getByText("Options chain missing greeks")).toBeInTheDocument();
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
