import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { getEngine } from "../engine/index.ts";
import { EngineError, type Question } from "../engine/types.ts";
import { Button, Card, ErrorBanner, GhostButton } from "../ui/primitives.tsx";
import Math from "../ui/Math.tsx";
import { cn } from "../ui/cn.ts";

const TOPICS = ["linear", "quadratic"];
const LEVELS = ["beginner", "basic", "intermediate", "advanced", "exam"];

export default function PracticeScreen() {
  const [topic, setTopic] = useState("linear");
  const [difficulty, setDifficulty] = useState("basic");
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});
  const [marks, setMarks] = useState<Record<string, boolean | null>>({});
  const generate = useMutation({
    mutationFn: async () => {
      const engine = await getEngine();
      return engine.practiceGenerate(topic, difficulty, 5, Date.now() % 100000);
    },
  });
  const score = useMutation({
    mutationFn: async (attempts: { topic: string; correct: boolean; hints_used: number }[]) => {
      const engine = await getEngine();
      return engine.practiceScore(attempts);
    },
  });

  const questions: Question[] = generate.data?.questions ?? [];

  return (
    <div className="flex flex-col gap-4">
      <Card className="p-5">
        <div className="flex flex-wrap gap-4">
          <label className="text-sm">
            <span className="mb-1 block text-xs uppercase tracking-wide text-slate-500">Topic</span>
            <span className="flex gap-1">
              {TOPICS.map((t) => (
                <GhostButton key={t} onClick={() => setTopic(t)} className={topic === t ? "bg-accent-600/10 font-semibold" : ""}>
                  {t}
                </GhostButton>
              ))}
            </span>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-xs uppercase tracking-wide text-slate-500">Difficulty</span>
            <span className="flex flex-wrap gap-1">
              {LEVELS.map((d) => (
                <GhostButton key={d} onClick={() => setDifficulty(d)} className={difficulty === d ? "bg-accent-600/10 font-semibold" : ""}>
                  {d}
                </GhostButton>
              ))}
            </span>
          </label>
        </div>
        <Button
          className="mt-4 w-full sm:w-auto"
          disabled={generate.isPending}
          onClick={() => {
            setRevealed({});
            setMarks({});
            generate.mutate();
          }}
        >
          {generate.isPending ? "Generating…" : "Generate 5 questions"}
        </Button>
        {generate.isError && (
          <div className="mt-3">
            <ErrorBanner message={generate.error instanceof EngineError ? generate.error.message : "Generation failed."} />
          </div>
        )}
      </Card>

      {questions.length > 0 && (
        <Card className="p-5">
          <ol className="flex flex-col gap-3">
            {questions.map((q, i) => (
              <li key={`${q.prompt}-${i}`} className="rounded-lg bg-slate-50 p-3 dark:bg-white/5">
                <p className="font-medium">
                  {i + 1}. <Math tex={q.prompt_latex} fallback={q.prompt} />
                </p>
                <div className="mt-2 flex flex-col gap-2 text-sm sm:flex-row sm:flex-wrap sm:items-center">
                  <GhostButton onClick={() => setRevealed((r) => ({ ...r, [i]: !r[i] }))}>
                    {revealed[i] ? "Hide answer" : "Reveal answer"}
                  </GhostButton>
                  {revealed[i] && (
                    <span className="font-semibold">
                      {q.expected_latex.map((tex, j) => (
                        <span key={j} className="mr-2">
                          <Math tex={tex} fallback={q.expected[j]} />
                        </span>
                      ))}
                    </span>
                  )}
                  <span className="flex gap-1 sm:ml-auto">
                    <GhostButton
                      onClick={() => setMarks((m) => ({ ...m, [i]: true }))}
                      className={marks[i] === true ? "bg-mint-500/15 font-semibold" : ""}
                    >
                      I got it
                    </GhostButton>
                    <GhostButton
                      onClick={() => setMarks((m) => ({ ...m, [i]: false }))}
                      className={marks[i] === false ? "bg-red-500/15 font-semibold" : ""}
                    >
                      I missed it
                    </GhostButton>
                  </span>
                </div>
              </li>
            ))}
          </ol>
          <Button
            className="mt-4 w-full sm:w-auto"
            disabled={score.isPending}
            onClick={() =>
              score.mutate(
                questions.map((q, i) => ({
                  topic: q.topic,
                  correct: marks[i] === true,
                  hints_used: 0,
                })),
              )
            }
          >
            Score me
          </Button>
          {score.data && (
            <div className={cn("mt-3 rounded-lg p-3 text-sm")}>
              <p className="font-semibold">{score.data.recommendation}</p>
              <p className="text-slate-500">
                {Object.entries(score.data.mastery).map(([t, v]) => `${t}: ${v}%`).join("  ")}
              </p>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
