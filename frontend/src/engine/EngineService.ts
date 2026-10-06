import { unwrap, type JsonLinesSession } from "./protocol.ts";
import type {
  AnalysisResult,
  EngineResponse,
  HistoryEntry,
  Question,
  SampleResult,
  SolutionResult,
  TableResult,
} from "./types.ts";

/** Shared request/response mapping. Transports implement `send`. */
export abstract class BaseEngineService {
  protected abstract send(payload: Record<string, unknown>): Promise<EngineResponse>;

  protected async result<T>(payload: Record<string, unknown>): Promise<T> {
    return unwrap(await this.send(payload)) as T;
  }

  solveLinear(input: string, domain = "reals"): Promise<SolutionResult> {
    return this.result({ op: "solve_linear", input, domain });
  }

  solveQuadratic(input: string, method = "auto", domain = "reals"): Promise<SolutionResult> {
    return this.result({ op: "solve_quadratic", input, domain, method });
  }

  solveSystem(equations: [string, string], domain = "reals"): Promise<SolutionResult> {
    return this.result({ op: "solve_system", equations, domain });
  }

  solveInequality(input: string, domain = "reals"): Promise<SolutionResult> {
    return this.result({ op: "solve_inequality", input, domain });
  }

  transform(kind: "simplify" | "expand" | "factorise", input: string): Promise<SolutionResult> {
    return this.result({ op: kind, input });
  }

  parse(input: string): Promise<{ kind: string }> {
    return this.result({ op: "parse", input });
  }

  sampleGraph(input: string, xMin = -10, xMax = 10, n = 400): Promise<SampleResult> {
    return this.result({ op: "sample_graph", input, x_min: xMin, x_max: xMax, n });
  }

  analyzeGraph(input: string): Promise<AnalysisResult> {
    return this.result({ op: "analyze_graph", input });
  }

  tableValues(input: string, start: string, end: string, step: string): Promise<TableResult> {
    return this.result({ op: "table_values", input, start, end, step });
  }

  intersect(a: string, b: string): Promise<{ points: { x: number; y: number; exact: string }[] }> {
    return this.result({ op: "solve_intersection", inputs: [a, b] });
  }

  practiceGenerate(topic: string, difficulty: string, n: number, seed: number): Promise<{ questions: Question[] }> {
    return this.result({ op: "practice_generate", topic, difficulty, n, seed });
  }

  practiceScore(attempts: { topic: string; correct: boolean; hints_used: number }[]): Promise<{
    mastery: Record<string, number>;
    recommendation: string;
  }> {
    return this.result({ op: "practice_score", attempts });
  }

  historyList(limit = 50): Promise<{ entries: HistoryEntry[] }> {
    return this.result({ op: "history_list", limit });
  }

  historyClear(): Promise<{ cleared: number }> {
    return this.result({ op: "history_clear" });
  }

  aiHint(solution: unknown, level: number, stepIndex = 0): Promise<{ hint: string; level: number }> {
    return this.result({ op: "ai_hint", solution, level, step_index: stepIndex });
  }

  aiExplain(solution: unknown, question: string): Promise<{ explanation: string; provider: string }> {
    return this.result({ op: "ai_explain", solution, question });
  }

  aiMistake(expectedStep: unknown, studentAfter: string): Promise<{
    correct: boolean; category?: string; explanation?: string; correction?: string;
  }> {
    return this.result({ op: "ai_mistake", expected_step: expectedStep, student_after: studentAfter });
  }
}

export class SessionEngineService extends BaseEngineService {
  constructor(private readonly session: JsonLinesSession) {
    super();
  }

  protected send(payload: Record<string, unknown>): Promise<EngineResponse> {
    return this.session.request(payload);
  }
}
