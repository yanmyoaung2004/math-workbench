import { BaseEngineService } from "./EngineService.ts";
import { EngineError, type EngineResponse } from "./types.ts";

/** Canned verified DTOs for UI development and tests (no backend needed). */
const LINEAR = {
  interpretation: "2*x + 5 = 17",
  exact: ["6"],
  approximate: ["6.0"],
  steps: [
    {
      operation: "subtract_both_sides",
      operand: "5",
      before: "2*x + 5 = 17",
      after: "2*x = 12",
      rule: "subtraction_property_of_equality",
      explanation: "Subtract 5 from both sides to remove the constant term.",
      verification: "verified",
    },
    {
      operation: "divide_both_sides",
      operand: "2",
      before: "2*x = 12",
      after: "x = 6",
      rule: "division_property_of_equality",
      explanation: "Divide both sides by 2 to isolate x.",
      verification: "verified",
    },
  ],
  verification: "verified",
  domain_info: { domain: "reals", excluded: [] },
  bindings: [{ variable: "x", exact: "6", approximate: "6.0" }],
};

export class MockEngineService extends BaseEngineService {
  protected async send(payload: Record<string, unknown>): Promise<EngineResponse> {
    const op = String(payload["op"] ?? "");
    const input = String(payload["input"] ?? "");
    if (input.trim() === "" && !["solve_system", "history_list", "history_clear"].includes(op)) {
      return { ok: false, op, error: { code: "VALIDATION_ERROR", message: "Please enter something." } };
    }
    if (op === "solve_linear" || op === "solve_quadratic" || op === "solve_inequality") {
      return { ok: true, op, interpretation: LINEAR.interpretation, result: LINEAR };
    }
    if (op === "sample_graph") {
      const xs: number[] = [];
      const ys: number[] = [];
      for (let i = 0; i <= 40; i++) {
        const x = -5 + (i * 10) / 40;
        xs.push(x);
        ys.push(x * x);
      }
      return {
        ok: true, op, interpretation: "x**2",
        result: { interpretation: "x**2", segments: [{ xs, ys }], excluded: [] },
      };
    }
    if (op === "analyze_graph") {
      return {
        ok: true, op, interpretation: "x**2",
        result: {
          interpretation: "x**2", roots: [{ kind: "root", x: 0, y: 0, exact: "0" }],
          y_intercept: { kind: "y_intercept", x: 0, y: 0, exact: "0" },
          turning_points: [{ kind: "turning_point", x: 0, y: 0, exact: "0" }],
          axis_of_symmetry: "x = 0", vertical_asymptotes: [],
          horizontal_asymptote: "", gradient: "2*x",
        },
      };
    }
    if (op === "table_values") {
      return {
        ok: true, op, interpretation: "x**2",
        result: { interpretation: "x**2", xs: ["-1", "0", "1"], ys: ["1", "0", "1"], ys_approx: [1, 0, 1] },
      };
    }
    if (op === "practice_generate") {
      return {
        ok: true, op, interpretation: "",
        result: {
          questions: [
            { topic: "linear", difficulty: "basic", prompt: "3x + 7 = 25", expected: ["6"], op: "solve_linear" },
          ],
        },
      };
    }
    if (op === "practice_score") {
      return {
        ok: true, op, interpretation: "",
        result: { mastery: { linear: 100 }, recommendation: "Balanced across topics." },
      };
    }
    if (op === "history_list") {
      return { ok: true, op, interpretation: "", result: { entries: [] } };
    }
    if (op === "history_clear") {
      return { ok: true, op, interpretation: "", result: { cleared: 0 } };
    }
    if (op === "ai_hint") {
      const level = Number(payload["level"] ?? 1);
      return { ok: true, op, interpretation: LINEAR.interpretation, result: { hint: `Mock hint L${level}.`, level } };
    }
    if (op === "ai_explain") {
      return {
        ok: true, op, interpretation: LINEAR.interpretation,
        result: { explanation: "[mock tutor] Subtract 5, then divide by 2.", provider: "mock" },
      };
    }
    if (op === "ai_mistake") {
      return { ok: true, op, interpretation: LINEAR.interpretation, result: { correct: true } };
    }
    throw new EngineError("VALIDATION_ERROR", `Mock has no fixture for op ${op}.`);
  }
}
