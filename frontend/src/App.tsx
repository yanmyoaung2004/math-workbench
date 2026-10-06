import { useEffect, useState } from "react";
import { effectiveTheme, useAppStore, type Screen } from "./state/store.ts";
import { cn } from "./ui/cn.ts";
import SolverScreen from "./screens/SolverScreen.tsx";
import GraphScreen from "./screens/GraphScreen.tsx";
import PracticeScreen from "./screens/PracticeScreen.tsx";
import HistoryScreen from "./screens/HistoryScreen.tsx";
import SettingsScreen from "./screens/SettingsScreen.tsx";

const NAV: { id: Screen; label: string; hint: string }[] = [
  { id: "solver", label: "Solver", hint: "Solve with steps" },
  { id: "graph", label: "Graph", hint: "Visualize functions" },
  { id: "practice", label: "Practice", hint: "Train by topic" },
  { id: "history", label: "History", hint: "Past calculations" },
  { id: "settings", label: "Settings", hint: "Theme and engine" },
];

export default function App() {
  const screen = useAppStore((s) => s.screen);
  const go = useAppStore((s) => s.go);
  const theme = useAppStore((s) => s.theme);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", effectiveTheme(theme) === "dark");
  }, [theme]);

  useEffect(() => {
    if (!sidebarOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sidebarOpen]);

  return (
    <div className="flex h-full bg-slate-50 text-slate-900 dark:bg-ink-950 dark:text-slate-100">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-10 bg-black/30 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
      <aside
        className={cn(
          "z-20 flex w-60 shrink-0 flex-col gap-1 border-r border-slate-200 bg-white p-4",
          "dark:border-white/10 dark:bg-ink-900",
          "max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:transform max-md:transition-transform",
          sidebarOpen ? "max-md:translate-x-0" : "max-md:-translate-x-full",
        )}
      >
        <div className="px-2 pb-4">
          <h1 className="text-lg font-bold tracking-tight">Math Workbench</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">GCSE/O-Level tutor</p>
        </div>
        <nav className="flex flex-col gap-1" aria-label="Modules">
          {NAV.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                go(item.id);
                setSidebarOpen(false);
              }}
              aria-current={screen === item.id ? "page" : undefined}
              className={cn(
                "rounded-lg px-3 py-2 text-left transition-colors",
                screen === item.id
                  ? "bg-accent-600/10 font-semibold text-accent-600 dark:bg-accent-500/15 dark:text-accent-500"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/5",
              )}
            >
              <span className="block text-sm">{item.label}</span>
              <span className="block text-xs opacity-70">{item.hint}</span>
            </button>
          ))}
        </nav>
        <p className="mt-auto px-2 pt-4 text-[11px] leading-relaxed text-slate-400 dark:text-slate-500">
          Answers come from a verified engine. AI explains — never invents.
        </p>
      </aside>
      <button
        className="fixed left-3 top-3 z-30 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm md:hidden dark:border-white/10 dark:bg-ink-900"
        onClick={() => setSidebarOpen((v) => !v)}
        aria-label="Toggle navigation"
      >
        Menu
      </button>
      <main className="mx-auto w-full max-w-4xl min-w-0 flex-1 overflow-y-auto p-4 pt-14 sm:p-6 sm:pt-14 md:p-8 md:pt-8">
        {screen === "solver" && <SolverScreen />}
        {screen === "graph" && <GraphScreen />}
        {screen === "practice" && <PracticeScreen />}
        {screen === "history" && <HistoryScreen />}
        {screen === "settings" && <SettingsScreen />}
      </main>
    </div>
  );
}
