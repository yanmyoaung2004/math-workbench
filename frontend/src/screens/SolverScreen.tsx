import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { getEngine } from "../engine/index.ts";
import { EngineError, type SolutionResult } from "../engine/types.ts";
import { Button, Card, EngineInput, ErrorBanner, GhostButton } from "../ui/primitives.tsx";
import Math from "../ui/Math.tsx";

type Op = "solve_linear" | "solve_quadratic" | "solve_inequality" | "solve_system" | "simplify" | "expand" | "factorise";

const OPS: { id: Op; label: string; placeholder: string }[] = [
  { id: "solve_linear", label: "Linear", placeholder: "2x + 5 = 17" },
  { id: "solve_quadratic", label: "Quadratic", placeholder: "x^2 - 5x + 6 = 0" },
  { id: "solve_inequality", label: "Inequality", placeholder: "2x + 3 > 9" },
  { id: "solve_system", label: "System", placeholder: "2x + y = 7  |  x - y = 2" },
  { id: "simplify", label: "Simplify", placeholder: "2x + 3x" },
  { id: "expand", label: "Expand", placeholder: "(x + 1)^2" },
  { id: "factorise", label: "Factorise", placeholder: "x^2 + 2x + 1" },
];

async function runSolve(op: Op, input: string): Promise<SolutionResult> {
  const engine = await getEngine();
  if (op === "solve_linear") return engine.solveLinear(input);
  if (op === "solve_quadratic") return engine.solveQuadratic(input);
  if (op === "solve_inequality") return engine.solveInequality(input);
  if (op === "solve_system") {
    const parts = input.split(/[|;]/).map((s) => s.trim()).filter(Boolean);
    if (parts.length !== 2) throw new EngineError("VALIDATION_ERROR", "Enter two equations separated by |.");
    return engine.solveSystem([parts[0], parts[1]]);
  }
  if (op === "expand" || op === "factorise") return engine.transform(op, input);
  return engine.transform("simplify", input);
}

export default function SolverScreen() {
  const [op, setOp] = useState<Op>("solve_linear");
  const [input, setInput] = useState("2x + 5 = 17");
  const [hintLevel, setHintLevel] = useState(0);
  const solve = useMutation({ mutationFn: () => runSolve(op, input) });
  const hint = useMutation({
    mutationFn: async (level: number) => {
      if (!solve.data) throw new Error("Solve something first.");
      const engine = await getEngine();
      return engine.aiHint(solve.data, level);
    },
  });

  const active = OPS.find((o) => o.id === op)!;
  const result = solve.data;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2" role="group" aria-label="Solver mode">
        {OPS.map((o) => (
          <GhostButton
            key={o.id}
            aria-pressed={op === o.id}
            onClick={() => {
              setOp(o.id);
              solve.reset();
              setHintLevel(0);
            }}
            className={op === o.id ? "bg-accent-600/10 font-semibold text-accent-600" : ""}
          >
            {o.label}
          </GhostButton>
        ))}
      </div>

      <form
        className="flex flex-col gap-2 sm:flex-row"
        onSubmit={(e) => {
          e.preventDefault();
          setHintLevel(0);
          solve.mutate();
        }}
      >
        <EngineInput
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={active.placeholder}
          aria-label="Mathematical input"
          className="min-w-0"
        />
        <Button type="submit" disabled={solve.isPending} className="w-full shrink-0 sm:w-auto">
          {solve.isPending ? "Solving…" : "Solve"}
        </Button>
      </form>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Tip: press Enter to solve. The engine echoes what it understood before answering.
      </p>

      {solve.isError && (
        <ErrorBanner
          message={solve.error instanceof EngineError ? solve.error.message : "Something went wrong."}
        />
      )}

      {result && (
        <Card className="p-5">
          <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Understood as
          </p>
          <p className="text-lg"><Math tex={result.interpretation_latex} fallback={result.interpretation} /></p>
          <p className="mt-3 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Answer
          </p>
          <p className="text-2xl font-semibold">
            {result.exact_latex.length > 0
              ? result.exact_latex.map((tex, i) => (
                  <span key={i} className="mr-4">
                    <Math tex={tex} fallback={result.exact[i]} />
                  </span>
                ))
              : <Math tex={result.interpretation_latex} fallback={result.interpretation} />}
          </p>
          {result.verification !== "verified" && (
            <p className="mt-1 text-sm text-amber-600 dark:text-amber-400">
              Unverifiable — treat with care.
            </p>
          )}
        </Card>
      )}

      {result && result.steps.length > 0 && (
        <Card className="p-5">
          <h2 className="mb-3 font-semibold">Why — step by step</h2>
          <ol className="flex flex-col gap-3">
            {result.steps.map((step, i) => (
              <li key={i} className="step-card rounded-r-lg bg-slate-50 py-2 pl-4 pr-3 dark:bg-white/5">
                <p className="text-sm font-medium">Step {i + 1}: {step.explanation}</p>
                <p className="mt-1 overflow-x-auto text-sm text-slate-600 dark:text-slate-300">
                  <Math tex={step.before_latex} fallback={step.before} />
                  <span className="mx-2">→</span>
                  <Math tex={step.after_latex} fallback={step.after} />
                </p>
              </li>
            ))}
          </ol>
        </Card>
      )}

      {result && (
        <Card className="p-5">
          <h2 className="mb-1 font-semibold">Need a nudge?</h2>
          <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">
            Hints reveal gradually — the answer stays hidden until level 5.
          </p>
          <div className="flex flex-wrap gap-2">
            {[1, 2, 3, 4, 5].map((level) => (
              <GhostButton
                key={level}
                onClick={() => {
                  setHintLevel(level);
                  hint.mutate(level);
                }}
                className={hintLevel === level ? "bg-accent-600/10 font-semibold" : ""}
              >
                Hint {level}
              </GhostButton>
            ))}
          </div>
          {hint.data && (
            <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm dark:bg-white/5">{hint.data.hint}</p>
          )}
        </Card>
      )}
    </div>
  );
}
