import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { cn } from "./cn.ts";

/** KaTeX render to string (pure, unit-tested). Null when LaTeX is unusable. */
export function renderMathTex(tex: string): string | null {
  const source = tex.trim();
  if (!source) return null;
  try {
    return katex.renderToString(source, {
      displayMode: false,
      throwOnError: true,
      trust: false,
    });
  } catch {
    return null;
  }
}

/** Real mathematical notation with a plain-text fallback (never blank). */
export default function Math({
  tex,
  fallback,
  className,
}: {
  tex?: string;
  fallback: string;
  className?: string;
}) {
  const html = useMemo(() => (tex ? renderMathTex(tex) : null), [tex]);
  if (!html) {
    return <span className={cn("math", className)}>{fallback}</span>;
  }
  return (
    <span
      className={cn(className)}
      dangerouslySetInnerHTML={{ __html: html }}
      aria-label={fallback}
    />
  );
}
