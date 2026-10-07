import type { SolutionResult } from "./types.ts";

/** Render a verified solution as Markdown (copy/share, print-friendly). */
export function solutionToMarkdown(solution: SolutionResult): string {
  const lines = [`# ${solution.interpretation}`, ""];
  lines.push(`**Answer:** ${solution.exact.length > 0 ? solution.exact.join(", ") : solution.interpretation}`, "");
  if (solution.steps.length > 0) {
    lines.push("## Steps", "");
    solution.steps.forEach((step, i) => {
      lines.push(`${i + 1}. ${step.explanation}`, "", `    ${step.before} → ${step.after}`, "");
    });
  }
  lines.push(`_Verified: ${solution.verification}_`);
  return lines.join("\n");
}

/** Substitute single-letter parameters (a, b, c) in a graph template. */
export function substituteParams(template: string, params: Record<string, number>): string {
  return template.replace(/\b([a-c])\b/g, (match, name: string) =>
    Object.hasOwn(params, name) ? String(params[name]) : match,
  );
}
