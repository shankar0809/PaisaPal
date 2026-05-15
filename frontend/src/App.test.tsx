import { describe, expect, it } from "vitest";
import { routeFromHash } from "./App";

describe("routeFromHash", () => {
  it("parses valid analysis run routes", () => {
    expect(routeFromHash("#/runs/12")).toEqual({ name: "run", runId: 12 });
  });

  it("rejects malformed analysis run routes", () => {
    expect(routeFromHash("#/runs/foo")).not.toEqual(expect.objectContaining({ name: "run" }));
    expect(routeFromHash("#/runs/")).not.toEqual(expect.objectContaining({ name: "run" }));
    expect(routeFromHash("#/runs/1/extra")).not.toEqual(expect.objectContaining({ name: "run" }));
  });
});
