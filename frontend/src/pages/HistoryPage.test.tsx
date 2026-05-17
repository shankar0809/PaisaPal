import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HistoryPage } from "./HistoryPage";

vi.mock("../api/client", () => ({
  fetchAnalysisRuns: async () => ([
    {
      id: 7,
      status: "running_gpt_analysis",
      tickers: ["MSFT"],
      account_size: 100000,
      risk_percent: 0.5,
      max_dollar_risk: null,
      notes: "",
      created_at: "2026-05-14T18:00:00Z",
      jobs: [
        {
          id: 11,
          ticker: "MSFT",
          status: "running_gpt_analysis",
          error_message: null
        }
      ]
    }
  ])
}));

describe("HistoryPage", () => {
  it("renders recent analysis runs", async () => {
    render(<HistoryPage />);

    expect(await screen.findByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Recent Analysis Runs")).toBeInTheDocument();
    expect(screen.getAllByText("running gpt analysis").length).toBeGreaterThan(0);
    expect(screen.getByText("#7")).toBeInTheDocument();
    expect(screen.getByText("MSFT")).toBeInTheDocument();
  });
});
