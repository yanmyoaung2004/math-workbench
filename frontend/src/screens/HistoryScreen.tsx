import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getEngine } from "../engine/index.ts";
import { EngineError } from "../engine/types.ts";
import { Button, Card, ErrorBanner } from "../ui/primitives.tsx";
import Math from "../ui/Math.tsx";

export default function HistoryScreen() {
  const client = useQueryClient();
  const history = useQuery({
    queryKey: ["history"],
    queryFn: async () => (await getEngine()).historyList(50),
  });
  const clear = useMutation({
    mutationFn: async () => (await getEngine()).historyClear(),
    onSuccess: () => void client.invalidateQueries({ queryKey: ["history"] }),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">Calculation history</h2>
        <Button disabled={clear.isPending} onClick={() => clear.mutate()} className="w-full sm:w-auto">
          Clear
        </Button>
      </div>
      {history.isError && (
        <ErrorBanner message={history.error instanceof EngineError ? history.error.message : "Load failed."} />
      )}
      {(history.data?.entries ?? []).length === 0 && !history.isPending && (
        <p className="text-sm text-slate-500">Nothing yet — solved problems appear here, offline.</p>
      )}
      {(history.data?.entries ?? []).map((entry) => (
        <Card key={entry.id} className="p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">{entry.op}</p>
          <p className="mt-0.5"><Math tex={entry.interpretation_latex} fallback={entry.interpretation} /></p>
          <p className="mt-1 font-semibold">
            {entry.exact_latex.map((tex, i) => (
              <span key={i} className="mr-3">
                <Math tex={tex} fallback={entry.exact[i]} />
              </span>
            ))}
          </p>
          <p className="mt-1 text-xs text-slate-400">{new Date(entry.timestamp).toLocaleString()}</p>
        </Card>
      ))}
    </div>
  );
}
