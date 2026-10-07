import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getEngine } from "../engine/index.ts";
import { EngineError } from "../engine/types.ts";
import { Button, Card, EngineInput, ErrorBanner, GhostButton } from "../ui/primitives.tsx";
import Math from "../ui/Math.tsx";

export default function ReferenceScreen() {
  const [tab, setTab] = useState<"glossary" | "specs" | "examples">("glossary");
  const [query, setQuery] = useState("");
  const [activeTerm, setActiveTerm] = useState<string | null>(null);

  const glossary = useQuery({
    queryKey: ["glossary"],
    queryFn: async () => (await getEngine()).glossaryList(),
  });
  const specs = useQuery({
    queryKey: ["specs"],
    queryFn: async () => (await getEngine()).specMap(),
  });
  const examples = useQuery({
    queryKey: ["examples"],
    queryFn: async () => (await getEngine()).practiceExamples("all"),
  });
  const definition = useMutation({
    mutationFn: async (term: string) => {
      const engine = await getEngine();
      return engine.glossaryGet(term);
    },
  });

  const terms = (glossary.data?.terms ?? []).filter((t) =>
    t.toLowerCase().includes(query.trim().toLowerCase()),
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2" role="group" aria-label="Reference section">
        {(["glossary", "specs", "examples"] as const).map((t) => (
          <GhostButton key={t} aria-pressed={tab === t} onClick={() => setTab(t)} className={tab === t ? "bg-accent-600/10 font-semibold capitalize" : "capitalize"}>
            {t}
          </GhostButton>
        ))}
      </div>

      {tab === "glossary" && (
        <Card className="p-5">
          <EngineInput
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search terms…"
            aria-label="Search glossary"
            className="mb-3 py-2 text-base"
          />
          {glossary.isError && (
            <ErrorBanner message={glossary.error instanceof EngineError ? glossary.error.message : "Load failed."} />
          )}
          <ul className="flex flex-col gap-1">
            {terms.map((term) => (
              <li key={term}>
                <button
                  className="w-full rounded-lg px-2 py-1.5 text-left text-sm hover:bg-slate-100 dark:hover:bg-white/5"
                  onClick={() => {
                    setActiveTerm(term);
                    definition.mutate(term);
                  }}
                >
                  <span className="font-medium capitalize">{term}</span>
                </button>
                {activeTerm === term && definition.data && (
                  <p className="px-2 pb-2 text-sm text-slate-600 dark:text-slate-300">{definition.data.definition}</p>
                )}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {tab === "specs" && (
        <Card className="p-5">
          <h2 className="mb-2 font-semibold">GCSE spec points</h2>
          <ul className="flex flex-col gap-1 text-sm">
            {(specs.data?.spec_points ?? []).map((point) => (
              <li key={point.code} className="flex justify-between gap-2 border-b border-slate-100 py-1.5 dark:border-white/5">
                <span><span className="font-mono text-xs">{point.code}</span> — {point.label}</span>
                <span className="shrink-0 text-slate-500">{point.topic} · {point.difficulty}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {tab === "examples" && (
        <Card className="p-5">
          <h2 className="mb-2 font-semibold">Worked examples (engine-verified)</h2>
          <ol className="flex flex-col gap-3">
            {(examples.data?.examples ?? []).map((example, i) => (
              <li key={i} className="rounded-lg bg-slate-50 p-3 text-sm dark:bg-white/5">
                <p className="font-medium"><Math tex={example.prompt_latex} fallback={example.prompt} /></p>
                <p className="mt-1">
                  Answer: {example.exact_latex.map((tex, j) => (
                    <span key={j} className="mr-2 font-semibold">
                      <Math tex={tex} fallback={example.exact[j]} />
                    </span>
                  ))}
                </p>
              </li>
            ))}
          </ol>
        </Card>
      )}

      <Card className="p-5">
        <h2 className="mb-2 font-semibold">Worksheet (by spec code)</h2>
        <SpecWorksheetForm />
      </Card>
    </div>
  );
}

function SpecWorksheetForm() {
  const [spec, setSpec] = useState("ALG-QUAD-3");
  const sheet = useMutation({
    mutationFn: async () => {
      const engine = await getEngine();
      return engine.worksheetGenerate("linear", "basic", 10, Date.now() % 100000, true, "", spec);
    },
  });
  return (
    <form
      className="flex flex-col gap-2 sm:flex-row"
      onSubmit={(e) => {
        e.preventDefault();
        sheet.mutate();
      }}
    >
      <EngineInput
        value={spec}
        onChange={(e) => setSpec(e.target.value)}
        placeholder="ALG-QUAD-3"
        aria-label="Spec code"
        className="min-w-0 py-2 font-mono text-base"
      />
      <Button type="submit" disabled={sheet.isPending} className="w-full shrink-0 sm:w-auto">
        Build sheet
      </Button>
      {sheet.data && (
        <p className="text-sm text-slate-500">
          {sheet.data.prompts.length} questions ready — answer key included.
        </p>
      )}
    </form>
  );
}
