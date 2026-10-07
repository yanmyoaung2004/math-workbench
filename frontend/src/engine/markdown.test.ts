import { describe, expect, it } from "vitest";
import { solutionToMarkdown, substituteParams } from "./markdown.ts";
import { MockEngineService } from "./MockEngineService.ts";

describe("solutionToMarkdown", () => {
  it("renders answer plus stepped working", async () => {
    const service = new MockEngineService();
    const sol = await service.solveLinear("2x + 5 = 17");
    const md = solutionToMarkdown(sol);
    expect(md).toContain("# 2*x + 5 = 17");
    expect(md).toContain("**Answer:** 6");
    expect(md).toContain("2*x = 12");
    expect(md).toContain("_Verified: verified_");
  });
});

describe("substituteParams", () => {
  it("replaces standalone a/b/c only", () => {
    expect(substituteParams("a*x^2 + b*x + c", { a: 1, b: -4, c: 3 }))
      .toBe("1*x^2 + -4*x + 3");
    expect(substituteParams("y = abs(x)", { a: 2 })).toBe("y = abs(x)");
    expect(substituteParams("a + b", { a: 1 })).toBe("1 + b");
  });
});
