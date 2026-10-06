import { SessionEngineService } from "./EngineService.ts";
import { JsonLinesSession, type SpawnFn } from "./protocol.ts";

/** Production transport: long-lived Python sidecar over stdio (ADR-0003). */
export function tauriSpawn(): SpawnFn {
  return async (onLine) => {
    const { Command } = await import("@tauri-apps/plugin-shell");
    const child = await Command.sidecar("binaries/workbench-engine").spawn();
    let stderr = "";
    child.stdout.on("data", (data: string) => onLine(String(data)));
    child.stderr.on("data", (data: string) => {
      stderr += String(data);
      if (stderr.length > 4000) {
        console.error("[engine]", stderr);
        stderr = "";
      }
    });
    return {
      write: (line: string) => child.write(line),
      close: () => child.kill(),
    };
  };
}

export async function connectSidecar(): Promise<SessionEngineService> {
  const session = new JsonLinesSession(tauriSpawn());
  await session.start();
  return new SessionEngineService(session);
}
