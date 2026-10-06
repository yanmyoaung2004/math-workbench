import { SessionEngineService } from "./EngineService.ts";
import { JsonLinesSession, type SpawnFn } from "./protocol.ts";

/** Production transport: long-lived Python sidecar over stdio (ADR-0003).
 *  Stream events attach to the Command (plugin-shell v2); the Child only
 *  offers write/kill. Listeners attach before spawn so no output is lost. */
export function tauriSpawn(): SpawnFn {
  return async (onLine) => {
    const { Command } = await import("@tauri-apps/plugin-shell");
    const command = Command.sidecar("binaries/workbench-engine");
    command.stdout.on("data", (line: string) => onLine(String(line)));
    let stderr = "";
    command.stderr.on("data", (line: string) => {
      stderr += String(line);
      if (stderr.length > 4000) {
        console.error("[engine]", stderr);
        stderr = "";
      }
    });
    const child = await command.spawn();
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
