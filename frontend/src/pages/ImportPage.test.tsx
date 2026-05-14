import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ImportPage } from "./ImportPage";

describe("ImportPage", () => {
  it("renders CSV upload controls", () => {
    render(<ImportPage />);

    expect(screen.getByText("CSV Import")).toBeInTheDocument();
    expect(screen.getByLabelText("Watchlist CSV")).toBeInTheDocument();
  });
});
