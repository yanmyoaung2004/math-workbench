import { describe, expect, it } from "vitest";
import { renderMathTex } from "./Math.tsx";

describe("renderMathTex", () => {
  it("typesets fractions and powers", () => {
    const html = renderMathTex("x = \\frac{1}{2}");
    expect(html).toContain("katex");
    expect(html).toContain("frac");
    expect(renderMathTex("2 x^{2} - 7 x + 3")).toContain("msup");
  });

  it("returns null for empty or broken input", () => {
    expect(renderMathTex("")).toBeNull();
    expect(renderMathTex("   ")).toBeNull();
    expect(renderMathTex("\\notacommand{")).toBeNull();
  });
});
