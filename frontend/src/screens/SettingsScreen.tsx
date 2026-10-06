import { useState } from "react";
import { getEngine } from "../engine/index.ts";
import { useAppStore } from "../state/store.ts";
import { Card, GhostButton } from "../ui/primitives.tsx";
import { cn } from "../ui/cn.ts";

export default function SettingsScreen() {
  const theme = useAppStore((s) => s.theme);
  const setTheme = useAppStore((s) => s.setTheme);
  const engineKind = useAppStore((s) => s.engineKind);
  const setEngineKind = useAppStore((s) => s.setEngineKind);
  const [connection, setConnection] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-4">
      <fieldset>
        <Card className="p-5">
          <legend className="mb-2 px-1 font-semibold">Appearance</legend>
          <div className="flex gap-2">
            {(["light", "dark", "system"] as const).map((t) => (
              <GhostButton key={t} aria-pressed={theme === t} onClick={() => setTheme(t)} className={cn(theme === t && "bg-accent-600/10 font-semibold")}>
                {t[0].toUpperCase() + t.slice(1)}
              </GhostButton>
            ))}
          </div>
        </Card>
      </fieldset>
      <fieldset>
        <Card className="p-5">
          <legend className="mb-2 px-1 font-semibold">Math engine</legend>
          <div className="flex gap-2">
            {(["auto", "tauri", "mock"] as const).map((k) => (
              <GhostButton key={k} aria-pressed={engineKind === k} onClick={() => setEngineKind(k)} className={cn(engineKind === k && "bg-accent-600/10 font-semibold")}>
                {k[0].toUpperCase() + k.slice(1)}
              </GhostButton>
            ))}
          </div>
          <p className="mt-2 text-sm text-slate-500">
            Auto uses the Python sidecar inside the desktop app and the built-in
            mock in the browser. Restart the app after switching.
            <button
              className="ml-2 underline"
              onClick={() => {
                setConnection("Testing…");
                void getEngine().then(
                  () => setConnection("Engine reachable."),
                  (err: unknown) => setConnection(`Unreachable: ${err instanceof Error ? err.message : err}`),
                );
              }}
            >
              Test connection
            </button>
            {connection && <span className="ml-2" role="status">{connection}</span>}
          </p>
        </Card>
      </fieldset>
    </div>
  );
}
