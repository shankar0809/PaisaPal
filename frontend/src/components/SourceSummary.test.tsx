import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SourceSummary } from "./SourceSummary";

describe("SourceSummary", () => {
  it("renders non-http source URLs as plain text", () => {
    render(
      <SourceSummary
        sources={[
          {
            provider: "provider",
            retrieved_at: "2026-05-14T18:00:00Z",
            status: "ok",
            label: "Unsafe source",
            url: "javascript:alert(1)",
            warnings: []
          }
        ]}
      />
    );

    expect(screen.getByText("Unsafe source")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Unsafe source" })).not.toBeInTheDocument();
  });
});
