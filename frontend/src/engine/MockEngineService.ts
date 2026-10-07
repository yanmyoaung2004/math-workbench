import { BaseEngineService } from "./EngineService.ts";
import { EngineError, type EngineResponse } from "./types.ts";

/** Canned verified DTOs for UI development and tests (no backend needed). */
const LINEAR = {
  interpretation: "2*x + 5 = 17",
  interpretation_latex: "2 x + 5 = 17",
  exact: ["6"],
  exact_latex: ["6"],
  approximate: ["6.0"],
  steps: [
    {
      operation: "subtract_both_sides",
      operand: "5",
      operand_latex: "5",
      before: "2*x + 5 = 17",
      before_latex: "2 x + 5 = 17",
      after: "2*x = 12",
      after_latex: "2 x = 12",
      rule: "subtraction_property_of_equality",
      explanation: "Subtract 5 from both sides to remove the constant term.",
      verification: "verified",
    },
    {
      operation: "divide_both_sides",
      operand: "2",
      operand_latex: "2",
      before: "2*x = 12",
      before_latex: "2 x = 12",
      after: "x = 6",
      after_latex: "x = 6",
      rule: "division_property_of_equality",
      explanation: "Divide both sides by 2 to isolate x.",
      verification: "verified",
    },
  ],
  verification: "verified",
  domain_info: { domain: "reals", excluded: [] },
  bindings: [{ variable: "x", exact: "6", approximate: "6.0", exact_latex: "6" }],
};

export class MockEngineService extends BaseEngineService {
  protected async send(payload: Record<string, unknown>): Promise<EngineResponse> {
    const op = String(payload["op"] ?? "");
    const input = String(payload["input"] ?? "");
    const needsInput = [
      "solve_linear", "solve_quadratic", "solve_inequality",
      "simplify", "expand", "factorise", "parse",
      "sample_graph", "analyze_graph", "table_values",
    ].includes(op);
    if (needsInput && input.trim() === "") {
      return { ok: false, op, error: { code: "VALIDATION_ERROR", message: "Please enter something." } };
    }
    if (op === "solve_linear" || op === "solve_quadratic" || op === "solve_inequality") {
      return { ok: true, op, interpretation: LINEAR.interpretation, result: LINEAR };
    }
    if (op === "simplify" || op === "expand" || op === "factorise") {
      return { ok: true, op, interpretation: input, result: { ...LINEAR, interpretation: input } };
    }
    if (op === "solve_system") {
      return {
        ok: true, op, interpretation: "2*x + y = 7; x - y = 2",
        result: {
          ...LINEAR, interpretation: "2*x + y = 7; x - y = 2",
          exact: ["3", "1"], exact_latex: ["3", "1"],
          bindings: [
            { variable: "x", exact: "3", approximate: "3.0", exact_latex: "3" },
            { variable: "y", exact: "1", approximate: "1.0", exact_latex: "1" },
          ],
        },
      };
    }
    if (op === "solve_intersection") {
      return {
        ok: true, op, interpretation: "y = 2*x + 4 ; y = 10",
        result: { points: [{ kind: "intersection", x: 3, y: 10, exact: "3", exact_latex: "3" }] },
      };
    }
    if (op === "parse") {
      return { ok: true, op, interpretation: input, result: { kind: "equation", interpretation: input } };
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
          interpretation: "x**2", roots: [{ kind: "root", x: 0, y: 0, exact: "0", exact_latex: "0" }],
          y_intercept: { kind: "y_intercept", x: 0, y: 0, exact: "0", exact_latex: "0" },
          turning_points: [{ kind: "turning_point", x: 0, y: 0, exact: "0", exact_latex: "0" }],
          axis_of_symmetry: "x = 0", axis_latex: "x = 0", vertical_asymptotes: [],
          horizontal_asymptote: "", gradient: "2*x", gradient_latex: "2 x",
        },
      };
    }
    if (op === "table_values") {
      return {
        ok: true, op, interpretation: "x**2",
        result: { interpretation: "x**2", xs: ["-1", "0", "1"], xs_latex: ["-1", "0", "1"], ys: ["1", "0", "1"], ys_latex: ["1", "0", "1"], ys_approx: [1, 0, 1] },
      };
    }
    if (op === "practice_generate") {
      return {
        ok: true, op, interpretation: "",
        result: {
          questions: [
            { topic: "linear", difficulty: "basic", prompt: "3x + 7 = 25", prompt_latex: "3 x + 7 = 25", expected: ["6"], expected_latex: ["6"], op: "solve_linear" },
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
    if (op === "ai_reflect") {
      return {
        ok: true, op, interpretation: LINEAR.interpretation,
        result: { accepted: true, correct: false, category: "sign", explanation: "Check the sign.", correction: "2*x = 12" },
      };
    }
    if (op === "practice_record") {
      return { ok: true, op, interpretation: "", result: { recorded: 1 } };
    }
    if (op === "practice_dashboard") {
      return {
        ok: true, op, interpretation: "",
        result: { mastery: { linear: 100 }, recommendation: "Balanced.", unlocked: { linear: ["beginner", "basic"] }, by_mistake: {}, attempts: 2 },
      };
    }
    if (op === "review_due") {
      return { ok: true, op, interpretation: "", result: { due: [] } };
    }
    if (op === "review_answer") {
      return { ok: true, op, interpretation: "", result: { next_due: "2026-10-08", interval_days: 1, ease: 2.5 } };
    }
    if (op === "progress_streak") {
      return { ok: true, op, interpretation: "", result: { streak_days: 3, active_today: true } };
    }
    if (op === "assignment_create") {
      return { ok: true, op, interpretation: "", result: { created: 1 } };
    }
    if (op === "assignment_list") {
      return { ok: true, op, interpretation: "", result: { assignments: [] } };
    }
    if (op === "worksheet_generate") {
      return {
        ok: true, op, interpretation: "",
        result: { title: "Mock sheet", topic: "linear", difficulty: "basic", seed: 1, prompts: ["3x + 7 = 25"], answer_key: [["6"]] },
      };
    }
    if (op === "spec_map") {
      return {
        ok: true, op, interpretation: "",
        result: { spec_points: [{ code: "ALG-LIN-2", topic: "linear", difficulty: "basic", label: "Two-step linear equations" }] },
      };
    }
    if (op === "concept_note") {
      return { ok: true, op, interpretation: "", result: { rule: "discriminant", note: "Mock concept note." } };
    }
    if (op === "practice_examples") {
      return {
        ok: true, op, interpretation: "",
        result: { examples: [{ topic: "linear", prompt: "2x + 5 = 17", exact: ["6"], prompt_latex: "2 x + 5 = 17", exact_latex: ["6"] }] },
      };
    }
    if (op === "glossary_list") {
      return { ok: true, op, interpretation: "", result: { terms: ["coefficient", "discriminant"] } };
    }
    if (op === "glossary_get") {
      return { ok: true, op, interpretation: "", result: { term: "discriminant", definition: "Mock definition." } };
    }
    if (op === "ocr_parse") {
      return { ok: false, op, error: { code: "VALIDATION_ERROR", message: "No OCR engine is configured." } };
    }
    throw new EngineError("VALIDATION_ERROR", `Mock has no fixture for op ${op}.`);
  }
}
