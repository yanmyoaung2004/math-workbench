import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { getEngine } from "../engine/index.ts";
import { EngineError, type Question, type Worksheet } from "../engine/types.ts";
import { Button, Card, EngineInput, ErrorBanner, GhostButton } from "../ui/primitives.tsx";
import MathNotation from "../ui/Math.tsx";
import { cn } from "../ui/cn.ts";

const TOPICS = ["linear", "quadratic", "mixed"];
const LEVELS = ["beginner", "basic", "intermediate", "advanced", "exam"];
const EXAM_SECONDS = 600;

function fmtClock(total: number): string {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function PracticeScreen() {
  const client = useQueryClient();
  const [topic, setTopic] = useState("linear");
  const [difficulty, setDifficulty] = useState("basic");
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});
  const [marks, setMarks] = useState<Record<string, boolean | null>>({});
  const [examMode, setExamMode] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(EXAM_SECONDS);
  const [sheetTitle, setSheetTitle] = useState("");
  const [sheet, setSheet] = useState<Worksheet | null>(null);

  useEffect(() => {
    if (!examMode) return;
    setSecondsLeft(EXAM_SECONDS);
    const timer = window.setInterval(() => setSecondsLeft((s) => Math.max(0, s - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [examMode]);

  const generate = useMutation({
    mutationFn: async () => {
      const engine = await getEngine();
      return engine.practiceGenerate(topic, difficulty, 5, Date.now() % 100000);
    },
  });
  const record = useMutation({
    mutationFn: async (attempt: { topic: string; difficulty: string; correct: boolean; mistake?: string }) => {
      const engine = await getEngine();
      return engine.practiceRecord({ topic: attempt.topic, correct: attempt.correct, hints_used: 0, difficulty: attempt.difficulty, mistake: attempt.mistake });
    },
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["dashboard"] });
      void client.invalidateQueries({ queryKey: ["streak"] });
    },
  });
  const score = useMutation({
    mutationFn: async (attempts: { topic: string; correct: boolean; hints_used: number; difficulty: string }[]) => {
      const engine = await getEngine();
      return engine.practiceScore(attempts);
    },
  });
  const worksheet = useMutation({
    mutationFn: async () => {
      const engine = await getEngine();
      return engine.worksheetGenerate(topic, difficulty, 10, Date.now() % 100000, true, sheetTitle);
    },
  });
  const upNext = useMutation({
    mutationFn: async () => {
      const engine = await getEngine();
      return engine.practiceNext(topic === "mixed" ? "linear" : topic, Date.now() % 100000);
    },
  });

  const questions: Question[] = generate.data?.questions ?? [];

  const mark = (i: number, q: Question, correct: boolean) => {
    setMarks((m) => ({ ...m, [i]: correct }));
    void record.mutate({ topic: q.topic, difficulty: q.difficulty, correct });
  };

  return (
    <div className="flex flex-col gap-4">
      <Card className="p-5">
        <div className="flex flex-wrap gap-4">
          <fieldset className="text-sm">
            <legend className="mb-1 text-xs uppercase tracking-wide text-slate-500">Topic</legend>
            <span className="flex flex-wrap gap-1">
              {TOPICS.map((t) => (
                <GhostButton key={t} aria-pressed={topic === t} onClick={() => setTopic(t)} className={topic === t ? "bg-accent-600/10 font-semibold" : ""}>
                  {t}
                </GhostButton>
              ))}
            </span>
          </fieldset>
          <fieldset className="text-sm">
            <legend className="mb-1 text-xs uppercase tracking-wide text-slate-500">Difficulty</legend>
            <span className="flex flex-wrap gap-1">
              {LEVELS.map((d) => (
                <GhostButton key={d} aria-pressed={difficulty === d} onClick={() => setDifficulty(d)} className={difficulty === d ? "bg-accent-600/10 font-semibold" : ""}>
                  {d}
                </GhostButton>
              ))}
            </span>
          </fieldset>
          <fieldset className="text-sm">
            <legend className="mb-1 text-xs uppercase tracking-wide text-slate-500">Mode</legend>
            <span className="flex gap-1">
              <GhostButton aria-pressed={!examMode} onClick={() => setExamMode(false)} className={!examMode ? "bg-accent-600/10 font-semibold" : ""}>
                Learn
              </GhostButton>
              <GhostButton aria-pressed={examMode} onClick={() => setExamMode(true)} className={examMode ? "bg-accent-600/10 font-semibold" : ""}>
                Exam (10 min)
              </GhostButton>
            </span>
          </fieldset>
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
          {examMode && (
            <p className={cn("mb-3 text-lg font-bold", secondsLeft < 60 && "text-red-600")} role="timer">
              {fmtClock(secondsLeft)} left — answers stay hidden until you score.
            </p>
          )}
          <ol className="flex flex-col gap-3">
            {questions.map((q, i) => (
              <li key={`${q.prompt}-${i}`} className="rounded-lg bg-slate-50 p-3 dark:bg-white/5">
                <p className="font-medium">
                  {i + 1}. <MathNotation tex={q.prompt_latex} fallback={q.prompt} />
                </p>
                <div className="mt-2 flex flex-col gap-2 text-sm sm:flex-row sm:flex-wrap sm:items-center">
                  {!examMode && (
                    <>
                      <GhostButton onClick={() => setRevealed((r) => ({ ...r, [i]: !r[i] }))}>
                        {revealed[i] ? "Hide answer" : "Reveal answer"}
                      </GhostButton>
                      {revealed[i] && (
                        <span className="font-semibold">
                          {q.expected_latex.map((tex, j) => (
                            <span key={j} className="mr-2">
                              <MathNotation tex={tex} fallback={q.expected[j]} />
                            </span>
                          ))}
                        </span>
                      )}
                    </>
                  )}
                  <span className="flex gap-1 sm:ml-auto">
                    <GhostButton
                      aria-pressed={marks[i] === true}
                      onClick={() => mark(i, q, true)}
                      className={marks[i] === true ? "bg-mint-500/15 font-semibold" : ""}
                    >
                      I got it
                    </GhostButton>
                    <GhostButton
                      aria-pressed={marks[i] === false}
                      onClick={() => mark(i, q, false)}
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
                  difficulty: q.difficulty,
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

      <Card className="p-5">
        <h2 className="mb-1 font-semibold">Up next — picked for you</h2>
        <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">
          The adaptive engine chooses your weakest unlocked material.
        </p>
        <Button disabled={upNext.isPending} onClick={() => upNext.mutate()}>
          {upNext.isPending ? "Choosing…" : "What should I do next?"}
        </Button>
        {upNext.data && (
          <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm dark:bg-white/5">
            <span className="font-medium">{upNext.data.difficulty}: </span>
            <MathNotation tex={upNext.data.prompt_latex} fallback={upNext.data.prompt} />
          </p>
        )}
      </Card>

      <Card className="p-5">
        <h2 className="mb-2 font-semibold">Worksheet (printable)</h2>
        <form
          className="mb-3 flex flex-col gap-2 sm:flex-row"
          onSubmit={(e) => {
            e.preventDefault();
            setSheet(null);
            worksheet.mutate();
          }}
        >
          <EngineInput
            value={sheetTitle}
            onChange={(e) => setSheetTitle(e.target.value)}
            placeholder="Worksheet title"
            aria-label="Worksheet title"
            className="min-w-0 py-2 text-base"
          />
          <Button type="submit" disabled={worksheet.isPending} className="w-full shrink-0 sm:w-auto">
            Build 10-question sheet
          </Button>
        </form>
        {worksheet.data && (
          <div>
            <ol className="flex flex-col gap-1 text-sm">
              {worksheet.data.prompts.map((prompt, i) => (
                <li key={i} className="math">
                  {i + 1}. {prompt}
                </li>
              ))}
            </ol>
            <div className="mt-3 flex gap-2">
              <GhostButton onClick={() => setSheet(worksheet.data ?? null)}>
                {sheet ? "Hide answer key" : "Show answer key"}
              </GhostButton>
              <GhostButton onClick={() => window.print()}>Print</GhostButton>
            </div>
            {sheet && (
              <ol className="mt-2 flex flex-col gap-1 text-sm text-slate-600 dark:text-slate-300">
                {sheet.answer_key.map((answers, i) => (
                  <li key={i} className="math">
                    {i + 1}. {answers.join(", ")}
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
