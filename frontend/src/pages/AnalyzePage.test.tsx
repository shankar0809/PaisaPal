import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TickerInputPanel } from "../components/TickerInputPanel";

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
});
