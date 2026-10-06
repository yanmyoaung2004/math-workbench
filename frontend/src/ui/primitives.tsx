import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { cn } from "./cn.ts";

export function Button({
  className,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg bg-accent-600 px-4 py-2",
        "text-sm font-semibold text-white shadow-sm transition-colors",
        "hover:bg-accent-500 disabled:cursor-not-allowed disabled:opacity-50",
        "dark:bg-accent-500 dark:hover:bg-accent-600",
        className,
      )}
      {...rest}
    />
  );
}

export function GhostButton({
  className,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-3 py-1.5",
        "text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100",
        "dark:text-slate-300 dark:hover:bg-white/10",
        className,
      )}
      {...rest}
    />
  );
}

export function Card({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <section
      className={cn(
        "rounded-xl2 border border-slate-200 bg-white shadow-sm",
        "dark:border-white/10 dark:bg-ink-900",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function EngineInput({
  className,
  ...rest
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      spellCheck={false}
      autoComplete="off"
      className={cn(
        "math w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-lg",
        "placeholder:font-sans placeholder:text-base placeholder:text-slate-400",
        "dark:border-white/15 dark:bg-ink-800 dark:text-slate-100",
        className,
      )}
      {...rest}
    />
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200"
    >
      {message}
    </div>
  );
}
