import { create } from "zustand";

export type Screen = "solver" | "graph" | "practice" | "progress" | "reference" | "history" | "settings";

interface AppState {
  screen: Screen;
  theme: "light" | "dark" | "system";
  engineKind: "auto" | "tauri" | "mock";
  go: (screen: Screen) => void;
  setTheme: (theme: AppState["theme"]) => void;
  setEngineKind: (kind: AppState["engineKind"]) => void;
}

function initialTheme(): AppState["theme"] {
  const saved = localStorage.getItem("wb-theme");
  return saved === "light" || saved === "dark" ? saved : "system";
}

function initialEngine(): AppState["engineKind"] {
  const saved = typeof window === "undefined" ? "" : localStorage.getItem("wb-engine");
  return saved === "tauri" || saved === "mock" ? saved : "auto";
}

export const useAppStore = create<AppState>()((set) => ({
  screen: "solver",
  theme: typeof window === "undefined" ? "system" : initialTheme(),
  engineKind: typeof window === "undefined" ? "auto" : initialEngine(),
  go: (screen) => set({ screen }),
  setTheme: (theme) => {
    localStorage.setItem("wb-theme", theme);
    set({ theme });
  },
  setEngineKind: (engineKind) => {
    localStorage.setItem("wb-engine", engineKind === "auto" ? "" : engineKind);
    set({ engineKind });
  },
}));

export function effectiveTheme(theme: AppState["theme"]): "light" | "dark" {
  if (theme !== "system") return theme;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
