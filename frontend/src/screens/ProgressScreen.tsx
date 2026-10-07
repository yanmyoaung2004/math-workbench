import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getEngine } from "../engine/index.ts";
import { EngineError } from "../engine/types.ts";
import { Button, Card, EngineInput, ErrorBanner, GhostButton } from "../ui/primitives.tsx";

export default function ProgressScreen() {
  const client = useQueryClient();
  const [title, setTitle] = useState("Friday set");
  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await getEngine()).practiceDashboard(),
  });
  const streak = useQuery({
    queryKey: ["streak"],
    queryFn: async () => (await getEngine()).progressStreak(),
  });
  const due = useQuery({
    queryKey: ["review-due"],
    queryFn: async () => (await getEngine()).reviewDue(),
  });
  const assignments = useQuery({
    queryKey: ["assignments"],
    queryFn: async () => (await getEngine()).assignmentList(),
  });
  const createAssignment = useMutation({
    mutationFn: async () => {
      const engine = await getEngine();
      return engine.assignmentCreate(title || "Untitled set", "linear", "basic", 5, Date.now() % 100000);
    },
    onSuccess: () => void client.invalidateQueries({ queryKey: ["assignments"] }),
  });
  const answerReview = useMutation({
    mutationFn: async ({ prompt, topic, correct }: { prompt: string; topic: string; correct: boolean }) => {
      const engine = await getEngine();
      return engine.reviewAnswer(prompt, topic, correct, 0);
    },
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["review-due"] });
      void client.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="p-5">
          <p className="text-xs uppercase tracking-wide text-slate-500">Day streak</p>
          <p className="mt-1 text-3xl font-bold">{streak.data?.streak_days ?? "—"}</p>
          <p className="text-xs text-slate-500">{streak.data?.active_today ? "Active today" : "Practice today to keep it going"}</p>
        </Card>
        <Card className="p-5 sm:col-span-2">
          <p className="text-xs uppercase tracking-wide text-slate-500">Mastery</p>
          {dashboard.data ? (
            <>
              <p className="mt-1 text-sm">
                {Object.entries(dashboard.data.mastery).map(([t, v]) => `${t}: ${v}%`).join("   ") || "No attempts yet"}
              </p>
              <p className="mt-1 text-sm font-semibold">{dashboard.data.recommendation}</p>
            </>
          ) : (
            <p className="mt-1 text-sm text-slate-500">Loading…</p>
          )}
          {dashboard.isError && (
            <ErrorBanner message={dashboard.error instanceof EngineError ? dashboard.error.message : "Load failed."} />
          )}
        </Card>
      </div>

      {dashboard.data && Object.keys(dashboard.data.by_mistake).length > 0 && (
        <Card className="p-5">
          <h2 className="mb-2 font-semibold">Mistake patterns</h2>
          <ul className="flex flex-col gap-1 text-sm">
            {Object.entries(dashboard.data.by_mistake).map(([kind, count]) => (
              <li key={kind} className="flex justify-between border-b border-slate-100 py-1 dark:border-white/5">
                <span>{kind.replace(/_/g, " ")}</span>
                <span className="font-semibold">×{count}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card className="p-5">
        <h2 className="mb-2 font-semibold">Review due ({due.data?.due.length ?? 0})</h2>
        {(due.data?.due ?? []).length === 0 && (
          <p className="text-sm text-slate-500">Nothing due — spaced repetition will schedule reviews here.</p>
        )}
        <ul className="flex flex-col gap-2">
          {(due.data?.due ?? []).map((item) => (
            <li key={item.prompt} className="flex flex-wrap items-center gap-2 rounded-lg bg-slate-50 p-3 text-sm dark:bg-white/5">
              <span className="math font-medium">{item.prompt}</span>
              <span className="ml-auto flex gap-1">
                <GhostButton
                  onClick={() => answerReview.mutate({ prompt: item.prompt, topic: item.topic, correct: true })}
                >
                  Got it
                </GhostButton>
                <GhostButton
                  onClick={() => answerReview.mutate({ prompt: item.prompt, topic: item.topic, correct: false })}
                >
                  Missed
                </GhostButton>
              </span>
            </li>
          ))}
        </ul>
      </Card>

      <Card className="p-5">
        <h2 className="mb-2 font-semibold">Assignments</h2>
        <form
          className="mb-3 flex flex-col gap-2 sm:flex-row"
          onSubmit={(e) => {
            e.preventDefault();
            createAssignment.mutate();
          }}
        >
          <EngineInput value={title} onChange={(e) => setTitle(e.target.value)} aria-label="Assignment title" className="min-w-0 py-2 text-base" />
          <Button type="submit" className="w-full shrink-0 sm:w-auto">Save current set</Button>
        </form>
        <ul className="flex flex-col gap-1 text-sm">
          {(assignments.data?.assignments ?? []).map((a) => (
            <li key={a.id} className="flex justify-between gap-2 border-b border-slate-100 py-1.5 dark:border-white/5">
              <span className="font-medium">{a.title}</span>
              <span className="text-slate-500">{a.topic} · {a.difficulty} · {a.n} questions</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
