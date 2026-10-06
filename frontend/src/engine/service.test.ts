import { describe, expect, it } from "vitest";
import { MockEngineService } from "./MockEngineService.ts";
import { EngineError } from "./types.ts";

describe("MockEngineService", () => {
  it("solves through the shared mapping", async () => {
    const service = new MockEngineService();
    const sol = await service.solveLinear("2x + 5 = 17");
    expect(sol.exact).toEqual(["6"]);
    expect(sol.verification).toBe("verified");
    expect(sol.steps).toHaveLength(2);
  });

  it("samples a graph", async () => {
    const service = new MockEngineService();
    const res = await service.sampleGraph("y = x^2", -5, 5, 41);
    expect(res.segments).toHaveLength(1);
    expect(res.segments[0].xs).toHaveLength(41);
  });

  it("rejects empty input with the engine code", async () => {
    const service = new MockEngineService();
    await expect(service.solveLinear("   ")).rejects.toMatchObject(
      expect.objectContaining({ code: "VALIDATION_ERROR" }),
    );
    await expect(service.solveLinear("   ")).rejects.toBeInstanceOf(EngineError);
  });
});
