import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { getEngine } from "../engine/index.ts";
import { EngineError, type GeometryResult, type MatrixResult, type SolutionResult } from "../engine/types.ts";
import { Button, Card, EngineInput, ErrorBanner, GhostButton } from "../ui/primitives.tsx";
import MathNotation from "../ui/Math.tsx";

type Tab = "calculus" | "matrix" | "geometry";

function parseMatrix(text: string): number[][] {
  const value: unknown = JSON.parse(text);
  if (!Array.isArray(value) || !value.every((row) => Array.isArray(row) && row.every((v) => typeof v === "number"))) {
    throw new EngineError("VALIDATION_ERROR", "Enter a matrix like [[1, 2], [3, 4]].");
  }
  return value as number[][];
}

function CircleDiagram({ r }: { r: number }) {
  const size = 160;
  const radius = Math.min(70, Math.max(12, (r / 10) * 70));
  const c = size / 2;
  return (
    <svg width={size} height={size} role="img" aria-label={`Circle of radius ${r}`}>
      <circle cx={c} cy={c} r={radius} fill="none" stroke="currentColor" strokeWidth={2} className="text-accent-600" />
      <line x1={c} y1={c} x2={c + radius} y2={c} stroke="currentColor" strokeWidth={1.5} strokeDasharray="4 3" />
      <text x={c + radius / 2} y={c - 6} textAnchor="middle" fontSize={12} fill="currentColor">r</text>
    </svg>
  );
}

function RightTriangleDiagram({ angleDeg }: { angleDeg: number }) {
  const w = 180;
  const h = 120;
  const rad = (angleDeg * Math.PI) / 180;
  const x2 = w - 20;
  const y2 = h - 20;
  const x1 = x2 - (h - 40) / Math.tan(rad);
  return (
    <svg width={w} height={h} role="img" aria-label={`Right triangle, angle ${angleDeg} degrees`}>
      <polygon points={`${x1},${y2} ${x2},${y2} ${x2},20`} fill="none" stroke="currentColor" strokeWidth={2} className="text-accent-600" />
      <rect x={x2 - 10} y={y2 - 10} width={10} height={10} fill="none" stroke="currentColor" strokeWidth={1} />
      <text x={(x1 + x2) / 2} y={y2 - 26} textAnchor="middle" fontSize={12} fill="currentColor">Î¸={angleDeg}Â°</text>
    </svg>
  );
}

export default function AdvancedScreen() {
  const [tab, setTab] = useState<Tab>("calculus");
  const [calcInput, setCalcInput] = useState("3x^2 + 2x + 5");
  const [calcKind, setCalcKind] = useState<"differentiate" | "integrate" | "definite">("differentiate");
  const [boundA, setBoundA] = useState("0");
  const [boundB, setBoundB] = useState("3");
  const [matrixText, setMatrixText] = useState("[[1, 2], [3, 4]]");
  const [matrixB, setMatrixB] = useState("[[5, 6], [7, 8]]");
  const [matrixOp, setMatrixOp] = useState<"multiply" | "determinant" | "inverse">("multiply");
  const [shape, setShape] = useState("circle");
  const [find, setFind] = useState("area");
  const [fields, setFields] = useState<Record<string, string>>({ r: "7" });

  const calc = useMutation({
    mutationFn: async (): Promise<SolutionResult> => {
      const engine = await getEngine();
      if (calcKind === "differentiate") return engine.differentiate(calcInput);
      if (calcKind === "integrate") return engine.integrate(calcInput);
      return engine.definiteIntegrate(calcInput, boundA, boundB);
    },
  });
  const matrix = useMutation({
    mutationFn: async (): Promise<MatrixResult> => {
      const engine = await getEngine();
      const a = parseMatrix(matrixText);
      if (matrixOp === "multiply") return engine.matrixMultiply(a, parseMatrix(matrixB));
      if (matrixOp === "determinant") return engine.matrixDeterminant(a);
      return engine.matrixInverse(a);
    },
  });
  const geometry = useMutation({
    mutationFn: async (): Promise<GeometryResult> => {
      const engine = await getEngine();
      return engine.geometrySolve(shape, find, fields);
    },
  });

  const error = calc.isError ? calc.error : matrix.isError ? matrix.error : geometry.isError ? geometry.error : null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2" role="group" aria-label="Advanced mode">
        {(["calculus", "matrix", "geometry"] as const).map((t) => (
          <GhostButton key={t} aria-pressed={tab === t} onClick={() => setTab(t)} className={tab === t ? "bg-accent-600/10 font-semibold capitalize" : "capitalize"}>
            {t}
          </GhostButton>
        ))}
      </div>

      {tab === "calculus" && (
        <Card className="p-5">
          <div className="mb-3 flex flex-wrap gap-2" role="group" aria-label="Calculus operation">
            {(["differentiate", "integrate", "definite"] as const).map((k) => (
              <GhostButton key={k} aria-pressed={calcKind === k} onClick={() => setCalcKind(k)} className={calcKind === k ? "bg-accent-600/10 font-semibold capitalize" : "capitalize"}>
                {k}
              </GhostButton>
            ))}
          </div>
          <form className="flex flex-col gap-2 sm:flex-row" onSubmit={(e) => { e.preventDefault(); calc.mutate(); }}>
            <EngineInput value={calcInput} onChange={(e) => setCalcInput(e.target.value)} aria-label="Expression in x" className="min-w-0" />
            {calcKind === "definite" && (
              <>
                <EngineInput value={boundA} onChange={(e) => setBoundA(e.target.value)} aria-label="Lower bound" className="w-24 py-2 text-base" />
                <EngineInput value={boundB} onChange={(e) => setBoundB(e.target.value)} aria-label="Upper bound" className="w-24 py-2 text-base" />
              </>
            )}
            <Button type="submit" disabled={calc.isPending} className="w-full shrink-0 sm:w-auto">Go</Button>
          </form>
          {calc.data && (
            <div className="mt-3">
              <p className="text-2xl font-semibold"><MathNotation tex={calc.data.exact_latex[0]} fallback={calc.data.exact[0]} /></p>
              <ol className="mt-2 flex flex-col gap-2">
                {calc.data.steps.map((s, i) => (
                  <li key={i} className="step-card rounded-r-lg bg-slate-50 py-2 pl-4 pr-3 text-sm dark:bg-white/5">
                    <span className="font-medium">{s.explanation}</span>
                    <span className="mt-1 block overflow-x-auto"><MathNotation tex={s.after_latex} fallback={s.after} /></span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </Card>
      )}

      {tab === "matrix" && (
        <Card className="p-5">
          <div className="mb-3 flex flex-wrap gap-2" role="group" aria-label="Matrix operation">
            {(["multiply", "determinant", "inverse"] as const).map((k) => (
              <GhostButton key={k} aria-pressed={matrixOp === k} onClick={() => setMatrixOp(k)} className={matrixOp === k ? "bg-accent-600/10 font-semibold capitalize" : "capitalize"}>
                {k}
              </GhostButton>
            ))}
          </div>
          <form className="flex flex-col gap-2" onSubmit={(e) => { e.preventDefault(); matrix.mutate(); }}>
            <EngineInput value={matrixText} onChange={(e) => setMatrixText(e.target.value)} aria-label="Matrix A as JSON" className="py-2 font-mono text-base" />
            {matrixOp === "multiply" && (
              <EngineInput value={matrixB} onChange={(e) => setMatrixB(e.target.value)} aria-label="Matrix B as JSON" className="py-2 font-mono text-base" />
            )}
            <Button type="submit" disabled={matrix.isPending} className="w-full sm:w-auto">Compute</Button>
          </form>
          {matrix.data && (
            <div className="mt-3">
              <p className="text-xl font-semibold"><MathNotation tex={matrix.data.result_latex} fallback={JSON.stringify(matrix.data.result)} /></p>
              <ol className="mt-2 flex flex-col gap-2">
                {matrix.data.steps.map((s, i) => (
                  <li key={i} className="step-card rounded-r-lg bg-slate-50 py-2 pl-4 pr-3 text-sm dark:bg-white/5">
                    <span className="font-medium">{s.explanation}</span>
                    <span className="math mt-1 block overflow-x-auto">{s.math}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </Card>
      )}

      {tab === "geometry" && (
        <Card className="p-5">
          <div className="mb-3 flex flex-wrap gap-2">
            <select value={shape} onChange={(e) => setShape(e.target.value)} aria-label="Shape" className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-white/15 dark:bg-ink-800">
              <option value="circle">Circle</option>
              <option value="rectangle">Rectangle</option>
              <option value="triangle">Triangle</option>
              <option value="right_triangle">Right triangle</option>
            </select>
            <select value={find} onChange={(e) => setFind(e.target.value)} aria-label="Find" className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-white/15 dark:bg-ink-800">
              {["area", "circumference", "perimeter", "hypotenuse", "leg", "opposite", "adjacent", "hypotenuse_from_angle", "angle"].map((f) => (
                <option key={f} value={f}>{f.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <form className="flex flex-col gap-2 sm:flex-row" onSubmit={(e) => { e.preventDefault(); geometry.mutate(); }}>
            {(["r", "w", "h", "b", "a", "c", "angle_deg", "hypotenuse", "opposite"] as const).map((name) => (
              <label key={name} className="text-sm">
                <span className="mb-1 block text-xs uppercase tracking-wide text-slate-500">{name}</span>
                <EngineInput
                  value={fields[name] ?? ""}
                  onChange={(e) => setFields((f) => ({ ...f, [name]: e.target.value }))}
                  placeholder="â€”"
                  aria-label={`Input ${name}`}
                  className="w-full py-2 text-base sm:w-24"
                />
              </label>
            ))}
            <Button type="submit" disabled={geometry.isPending} className="w-full shrink-0 self-end sm:w-auto">Solve</Button>
          </form>
          {geometry.data && (
            <div className="mt-3 flex flex-col gap-3 sm:flex-row">
              {shape === "circle" && <CircleDiagram r={Number(fields.r) || 0} />}
              {shape === "right_triangle" && <RightTriangleDiagram angleDeg={Number(fields.angle_deg) || 30} />}
              <div>
                <p className="text-2xl font-semibold"><MathNotation tex={geometry.data.result_latex} fallback={geometry.data.result_exact} /></p>
                {geometry.data.result_approx !== null && (
                  <p className="math text-slate-500">â‰ˆ {geometry.data.result_approx}</p>
                )}
                <ol className="mt-2 flex flex-col gap-2">
                  {geometry.data.steps.map((s, i) => (
                    <li key={i} className="step-card rounded-r-lg bg-slate-50 py-2 pl-4 pr-3 text-sm dark:bg-white/5">
                      <span className="font-medium">{s.explanation}</span>
                      <span className="mt-1 block overflow-x-auto"><MathNotation tex={s.math_latex} fallback={s.math} /></span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          )}
        </Card>
      )}

      {error && <ErrorBanner message={error instanceof EngineError ? error.message : "Something went wrong."} />}
    </div>
  );
}
