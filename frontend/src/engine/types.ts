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

export interface PracticeAttempt {
  topic: string;
  correct: boolean;
  hints_used: number;
  difficulty?: string;
  mistake?: string;
}

export interface Dashboard {
  mastery: Record<string, number>;
  recommendation: string;
  unlocked: Record<string, string[]>;
  by_mistake: Record<string, number>;
  attempts: number;
  bkt?: Record<string, number>;
  bkt_gates?: Record<string, string[]>;
  difficulty_rates?: Record<string, Record<string, number>>;
  at_risk?: { topic: string; flag: string; reason: string }[];
}

export interface MatrixStep {
  operation: string;
  explanation: string;
  math: string;
}

export interface MatrixResult {
  operation: string;
  input_display: string;
  result: string[][] | string[];
  result_latex: string;
  steps: MatrixStep[];
  verification: string;
}

export interface GeometryStep {
  operation: string;
  explanation: string;
  math: string;
  math_latex: string;
}

export interface GeometryResult {
  shape: string;
  find: string;
  inputs: [string, string][];
  result_exact: string;
  result_approx: number | null;
  steps: GeometryStep[];
  verification: string;
  result_latex: string;
}

export interface PracticeNext {
  topic: string;
  difficulty: string;
  prompt: string;
  expected: string[];
  prompt_latex: string;
  expected_latex: string[];
}

export interface ReviewItem {
  prompt: string;
  topic: string;
  next_due: string;
  interval_days: number;
  ease: number;
}

export interface Assignment {
  id: number;
  title: string;
  topic: string;
  difficulty: string;
  n: number;
  seed: number;
  created: string;
}

export interface Worksheet {
  title: string;
  topic: string;
  difficulty: string;
  seed: number;
  prompts: string[];
  answer_key: string[][];
}

export interface SpecPoint {
  code: string;
  topic: string;
  difficulty: string;
  label: string;
}

export interface WorkedExample {
  topic: string;
  prompt: string;
  exact: string[];
  prompt_latex: string;
  exact_latex: string[];
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
