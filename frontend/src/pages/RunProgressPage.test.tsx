import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { JobStatusTable } from "../components/JobStatusTable";
import { RunProgressPage } from "./RunProgressPage";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("JobStatusTable", () => {
  it("renders complete jobs with an open report button", () => {
    const onOpenTicker = vi.fn();
    render(
      <JobStatusTable
        jobs={[
          { id: 1, ticker: "MSFT", status: "complete", error_message: null },
          { id: 2, ticker: "AAPL", status: "in_progress", error_message: "Waiting" }
        ]}
        onOpenTicker={onOpenTicker}
      />
    );

    expect(screen.getByText("in progress")).toBeInTheDocument();
    expect(screen.getByText("Waiting")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /open .* report/i })).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Open MSFT report" }));

    expect(onOpenTicker).toHaveBeenCalledWith("MSFT");
  });
});

describe("RunProgressPage", () => {
  it("starts the configured live analysis run", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 7,
          status: "queued",
          tickers: ["NVDA"],
          account_size: 100000,
          risk_percent: 0.5,
          max_dollar_risk: null,
          notes: "",
          created_at: "2026-05-15T12:00:00",
          jobs: [{ id: 1, ticker: "NVDA", status: "queued", error_message: null }]
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 7,
          status: "complete",
          tickers: ["NVDA"],
          account_size: 100000,
          risk_percent: 0.5,
          max_dollar_risk: null,
          notes: "",
          created_at: "2026-05-15T12:00:00",
          jobs: [{ id: 1, ticker: "NVDA", status: "complete", error_message: null }]
        })
      });
    vi.stubGlobal("fetch", fetchMock);

    render(<RunProgressPage runId={7} />);

    fireEvent.click(await screen.findByRole("button", { name: "Run Analysis" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenLastCalledWith("/api/analysis-runs/7/run", { method: "POST" });
    });
    expect(await screen.findByText("complete")).toBeInTheDocument();
  });
});
