import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { JobStatusTable } from "../components/JobStatusTable";

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
    expect(screen.getAllByRole("button", { name: "Open" })).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Open" }));

    expect(onOpenTicker).toHaveBeenCalledWith("MSFT");
  });
});
