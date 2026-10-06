import type { BaseEngineService } from "./EngineService.ts";
import { MockEngineService } from "./MockEngineService.ts";
import { connectSidecar } from "./TauriEngineService.ts";
import { useAppStore } from "../state/store.ts";

function runningUnderTauri(): boolean {
  if (typeof window === "undefined") return false;
  return (
    "__TAURI_INTERNALS__" in window ||
    window.location.protocol === "tauri:" ||
    window.location.hostname === "tauri.localhost"
  );
}

export function resolveEngineKind(): "tauri" | "mock" {
  const override = localStorage.getItem("wb-engine");
  if (override === "tauri" || override === "mock") return override;
  return runningUnderTauri() ? "tauri" : "mock";
}

/** Engine singleton for screens. Mock in browser dev; sidecar under Tauri. */
let cached: Promise<BaseEngineService> | null = null;

export function getEngine(): Promise<BaseEngineService> {
  if (!cached) {
    cached = (async () => {
      const explicit = useAppStore.getState().engineKind;
      const kind = explicit !== "auto" ? explicit : resolveEngineKind();
      if (kind === "tauri") {
        try {
          return await connectSidecar();
        } catch (err) {
          console.warn("[engine] sidecar unavailable, falling back to mock:", err);
        }
      }
      return new MockEngineService();
    })();
  }
  return cached;
}
