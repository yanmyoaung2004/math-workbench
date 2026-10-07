import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import Plotly from "plotly.js-dist-min";
import { getEngine } from "../engine/index.ts";
import { substituteParams } from "../engine/markdown.ts";
import { EngineError, type AnalysisResult, type SampleResult } from "../engine/types.ts";
import { effectiveTheme, useAppStore } from "../state/store.ts";
import { Button, Card, EngineInput, ErrorBanner, GhostButton } from "../ui/primitives.tsx";
import Math from "../ui/Math.tsx";
import { cn } from "../ui/cn.ts";

function PlotView({ data, dark }: { data: SampleResult; dark: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const grid = dark ? "#26314d" : "#e2e8f0";
    const traces = data.segments.map((seg) => ({
      x: seg.xs,
      y: seg.ys,
      mode: "lines" as const,
      type: "scatter" as const,
      line: { width: 2.5 },
    }));
    void Plotly.newPlot(
      ref.current,
      traces,
      {
        margin: { l: 44, r: 12, t: 12, b: 40 },
        xaxis: { zeroline: true, gridcolor: grid },
        yaxis: { zeroline: true, gridcolor: grid },
        showlegend: false,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
      },
      { responsive: true, displayModeBar: false },
    );
    return () => {
      if (ref.current) Plotly.purge(ref.current);
    };
  }, [data, dark]);
  return <div ref={ref} className="h-64 w-full min-w-0 sm:h-80" role="img" aria-label={`Graph of ${data.interpretation}`} />;
}

export default function GraphScreen() {
  const [input, setInput] = useState("y = x^2 - 4x + 3");
  const [xMin, setXMin] = useState("-5");
  const [xMax, setXMax] = useState("5");
  const [tStart, setTStart] = useState("-3");
  const [tEnd, setTEnd] = useState("3");
  const [tStep, setTStep] = useState("1");
  const [slidersOn, setSlidersOn] = useState(false);
  const [template, setTemplate] = useState("y = a*x^2 + b*x + c");
  const [params, setParams] = useState({ a: 1, b: -4, c: 3 });
  const theme = useAppStore((s) => s.theme);
  const dark = effectiveTheme(theme) === "dark";

  const effective = slidersOn ? substituteParams(template, params) : input;

  const plot = useMutation({
    mutationFn: async () => {
      const engine = await getEngine();
      const [sampled, analysis] = await Promise.all([
        engine.sampleGraph(effective, Number(xMin), Number(xMax), 400),
        engine.analyzeGraph(effective),
      ]);
      return { sampled, analysis } as { sampled: SampleResult; analysis: AnalysisResult };
    },
  });
  const table = useMutation({
    mutationFn: async () => (await getEngine()).tableValues(effective, tStart, tEnd, tStep),
  });

  return (
    <div className="flex flex-col gap-4">
      <Card className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="font-semibold">Explore parameters</h2>
          <GhostButton aria-pressed={slidersOn} onClick={() => setSlidersOn((v) => !v)} className={slidersOn ? "bg-accent-600/10 font-semibold" : ""}>
            {slidersOn ? "Using sliders" : "Use sliders"}
          </GhostButton>
        </div>
        {slidersOn && (
          <>
            <EngineInput
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              aria-label="Parametric template (a, b, c)"
              placeholder="y = a*x^2 + b*x + c"
              className="py-2 text-base"
            />
            <p className="math mt-1 text-sm text-slate-500">{effective}</p>
            <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-3">
              {(["a", "b", "c"] as const).map((name) => (
                <label key={name} className="text-sm">
                  <span className="mb-1 flex justify-between text-xs uppercase tracking-wide text-slate-500">
                    <span>{name}</span>
                    <span className="math font-semibold text-slate-700 dark:text-slate-200">{params[name]}</span>
                  </span>
                  <input
                    type="range"
                    min={-5}
                    max={5}
                    step={0.5}
                    value={params[name]}
                    onChange={(e) => setParams((p) => ({ ...p, [name]: Number(e.target.value) }))}
                    className="w-full accent-[#3b63e0]"
                    aria-label={`Parameter ${name}`}
                  />
                </label>
              ))}
            </div>
          </>
        )}
      </Card>
      <form
        className="flex flex-wrap items-end gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          plot.mutate();
        }}
      >
        <label className="min-w-0 flex-1 basis-56 text-sm">
          <span className="mb-1 block text-xs uppercase tracking-wide text-slate-500">Function</span>
          <EngineInput value={input} onChange={(e) => setInput(e.target.value)} placeholder="y = x^2 - 4x + 3" />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs uppercase tracking-wide text-slate-500">x min</span>
          <EngineInput value={xMin} onChange={(e) => setXMin(e.target.value)} className="w-24 py-2 text-base" />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs uppercase tracking-wide text-slate-500">x max</span>
          <EngineInput value={xMax} onChange={(e) => setXMax(e.target.value)} className="w-24 py-2 text-base" />
        </label>
        <Button type="submit" disabled={plot.isPending} className="w-full sm:w-auto">
          {plot.isPending ? "Plotting…" : "Plot"}
        </Button>
      </form>

      {plot.isError && (
        <ErrorBanner message={plot.error instanceof EngineError ? plot.error.message : "Plot failed."} />
      )}

      {plot.data && (
        <>
          <Card className="p-4">
            <PlotView data={plot.data.sampled} dark={dark} />
            {plot.data.sampled.excluded.length > 0 && (
              <p className="px-1 pb-1 text-xs text-slate-500">
                Breaks at: {plot.data.sampled.excluded.join(", ")} (never connected across gaps)
              </p>
            )}
          </Card>
          <AnalysisPanel analysis={plot.data.analysis} />
          <Card className="p-5">
            <h2 className="mb-3 font-semibold">Table of values</h2>
            <form
              className="mb-3 flex flex-wrap items-end gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                table.mutate();
              }}
            >
              {(
                [
                  ["Start", tStart, setTStart],
                  ["End", tEnd, setTEnd],
                  ["Step", tStep, setTStep],
                ] as [string, string, (v: string) => void][]
              ).map(([label, value, set]) => (
                <label key={label} className="text-sm">
                  <span className="mb-1 block text-xs uppercase tracking-wide text-slate-500">{label}</span>
                  <EngineInput
                    value={value}
                    onChange={(e) => set(e.target.value)}
                    className="w-24 py-2 text-base"
                  />
                </label>
              ))}
              <Button type="submit" disabled={table.isPending} className="w-full sm:w-auto">Build table</Button>
            </form>
            {table.data && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500">
                      <th className="px-2 py-1">x</th>
                      {table.data.xs.map((x, i) => (
                        <th key={`${x}-${i}`} className="px-2 py-1 font-medium">
                          <Math tex={table.data.xs_latex[i]} fallback={x} />
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-t border-slate-200 dark:border-white/10">
                      <td className="px-2 py-1 font-medium">y</td>
                      {table.data.ys.map((y, i) => (
                        <td key={i} className={cn("px-2 py-1", y === "undefined" && "text-slate-400")}>
                          <Math tex={table.data.ys_latex[i]} fallback={y} />
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}

function AnalysisPanel({ analysis }: { analysis: AnalysisResult }) {
  const mathRows: [string, string, string][] = [
    ["Gradient", analysis.gradient, analysis.gradient_latex],
    ["Axis of symmetry", analysis.axis_of_symmetry || "—", analysis.axis_latex],
  ];
  const plain: [string, string][] = [
    ["Roots", analysis.roots.length > 0 ? analysis.roots.map((p) => `(${p.x}, ${p.y})`).join(", ") : "none"],
    ["Y-intercept", analysis.y_intercept ? `(${analysis.y_intercept.x}, ${analysis.y_intercept.y})` : "none"],
    [
      "Turning points",
      analysis.turning_points.length > 0
        ? analysis.turning_points.map((p) => `(${p.x}, ${p.y})`).join(", ")
        : "none",
    ],
    [
      "Vertical asymptotes",
      analysis.vertical_asymptotes.length > 0 ? analysis.vertical_asymptotes.join(", ") : "none",
    ],
    ["Horizontal behavior", analysis.horizontal_asymptote || "—"],
  ];
  return (
    <Card className="p-5">
      <h2 className="mb-2 font-semibold">Analysis <span className="text-xs font-normal text-slate-500">(engine-computed)</span></h2>
      <dl className="grid grid-cols-1 gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
        {mathRows.map(([k, v, tex]) => (
          <div key={k} className="flex justify-between gap-4 border-b border-slate-100 py-1.5 dark:border-white/5">
            <dt className="text-slate-500 dark:text-slate-400">{k}</dt>
            <dd className="text-right"><Math tex={tex} fallback={v} /></dd>
          </div>
        ))}
        {plain.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-4 border-b border-slate-100 py-1.5 dark:border-white/5">
            <dt className="text-slate-500 dark:text-slate-400">{k}</dt>
            <dd className="math text-right">{v}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}
