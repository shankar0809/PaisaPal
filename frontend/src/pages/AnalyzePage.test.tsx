import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AnalyzePage } from "./AnalyzePage";
import { TickerInputPanel } from "../components/TickerInputPanel";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("TickerInputPanel", () => {
  it("shows a validation error for empty tickers and does not submit", async () => {
    const onSubmit = vi.fn();
    render(<TickerInputPanel onSubmit={onSubmit} />);

    fireEvent.click(screen.getByRole("button", { name: /run analysis/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Enter at least one ticker.");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the ticker input string with the selected risk percent", async () => {
    const onSubmit = vi.fn();
    render(<TickerInputPanel onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Tickers"), { target: { value: "NVDA, TSLA" } });
    fireEvent.change(screen.getByLabelText("Risk percent"), { target: { value: "0.5" } });
    fireEvent.click(screen.getByRole("button", { name: /run analysis/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        tickers: "NVDA, TSLA",
        account_size: 100000,
        risk_percent: 0.5,
        max_dollar_risk: null,
        notes: ""
      })
    );
  });

  it("shows validation errors for invalid account size and max dollar risk", async () => {
    const onSubmit = vi.fn();
    render(<TickerInputPanel onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Tickers"), { target: { value: "NVDA" } });
    fireEvent.change(screen.getByLabelText("Account size"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: /run analysis/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Account size must be greater than 0."
    );
    expect(onSubmit).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Account size"), { target: { value: "100000" } });
    fireEvent.change(screen.getByLabelText("Max dollar risk"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: /run analysis/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Max dollar risk must be greater than 0."
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

describe("AnalyzePage", () => {
  it("renders live readiness and provider configuration", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [
          {
            provider: "openai",
            configured: true,
            role: "ai",
            required_for_live: true,
            live_ready: true,
            message: "Live AI analysis ready"
          },
          {
            provider: "polygon",
            configured: true,
            role: "market_data",
            required_for_live: false,
            live_ready: true,
            message: "Live AI analysis ready"
          },
          {
            provider: "fmp",
            configured: false,
            role: "fundamentals",
            required_for_live: false,
            live_ready: true,
            message: "Live AI analysis ready"
          }
        ]
      })
    );

    render(<AnalyzePage />);

    expect(await screen.findByText("Live AI analysis ready")).toBeInTheDocument();
    expect(screen.getByText("openai")).toBeInTheDocument();
    expect(screen.getByText("polygon")).toBeInTheDocument();
    expect(screen.getByText("fmp")).toBeInTheDocument();
    expect(screen.getAllByText("configured")).toHaveLength(2);
    expect(screen.getByText("missing")).toBeInTheDocument();
  });
});
