/** DTO mirrors of the Python sidecar protocol (docs/math-engine.md).
 *  Components render these directly — no math logic lives in the UI. */

export interface EngineStep {
  operation: string;
  operand: string;
  before: string;
  after: string;
  rule: string;
  explanation: string;
  verification: string;
  before_latex: string;
  after_latex: string;
  operand_latex: string;
}

export interface Binding {
  variable: string;
  exact: string;
  approximate: string;
  exact_latex: string;
}

export interface SolutionResult {
  interpretation: string;
  exact: string[];
  approximate: string[];
  steps: EngineStep[];
  verification: string;
  domain_info: { domain: string; excluded: string[] };
  bindings: Binding[];
  interpretation_latex: string;
  exact_latex: string[];
}

export interface GraphSegment {
  xs: number[];
  ys: number[];
}

export interface SampleResult {
  interpretation: string;
  segments: GraphSegment[];
  excluded: number[];
}

export interface FeaturePoint {
  kind: string;
  x: number;
  y: number;
  exact: string;
  exact_latex: string;
}

export interface AnalysisResult {
  interpretation: string;
  roots: FeaturePoint[];
  y_intercept: FeaturePoint | null;
  turning_points: FeaturePoint[];
  axis_of_symmetry: string;
  vertical_asymptotes: number[];
  horizontal_asymptote: string;
  gradient: string;
  axis_latex: string;
  gradient_latex: string;
}

export interface TableResult {
  interpretation: string;
  xs: string[];
  ys: string[];
  ys_approx: Array<number | null>;
  xs_latex: string[];
  ys_latex: string[];
}

export interface Question {
  topic: string;
  difficulty: string;
  prompt: string;
  expected: string[];
  op: string;
  prompt_latex: string;
  expected_latex: string[];
}

export interface HistoryEntry {
  id: number;
  timestamp: string;
  op: string;
  input: string;
  interpretation: string;
  exact: string[];
  verification: string;
  interpretation_latex: string;
  exact_latex: string[];
}

export type EngineOk = {
  ok: true;
  op: string;
  interpretation: string;
  result: unknown;
};

export type EngineErr = {
  ok: false;
  op: string;
  error: { code: string; message: string };
};

export type EngineResponse = EngineOk | EngineErr;

export class EngineError extends Error {
  readonly code: string;
  constructor(code: string, message: string) {
    super(message);
    this.name = "EngineError";
    this.code = code;
  }
}
