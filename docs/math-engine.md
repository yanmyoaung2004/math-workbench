# Math Engine API Contracts (V1 binding)

Implementations MUST satisfy these shapes. Tests enforce them
(`tests/unit/test_contracts.py`, golden corpus). Version: `v1`.

## 1. JSON sidecar protocol (stdio JSON-lines)

One request line → one response line. UTF-8, `\n`-terminated.

### Request

```jsonc
{
  "op": "solve_linear" | "solve_quadratic" | "solve_system" | "solve_inequality" | "simplify" | "expand" | "factorise" | "parse" | "sample_graph" | "analyze_graph" | "table_values" | "solve_intersection" | "history_list" | "history_clear" | "practice_generate" | "practice_score" | "ai_explain" | "ai_hint" | "ai_mistake" | "ai_reflect" | "practice_record" | "practice_dashboard" | "review_due" | "review_answer" | "progress_streak" | "assignment_create" | "assignment_list" | "worksheet_generate" | "spec_map" | "concept_note" | "practice_examples" | "glossary_list" | "glossary_get",
  "input": "2x + 5 = 17",   // raw user string, required (except solve_system)
  "equations": ["2x + y = 7", "x - y = 2"],  // solve_system only: exactly 2
  "domain": "reals",         // optional, default "reals" (GCSE); "complex" opts in
  "method": "auto",          // solve_quadratic only: auto | factorise | formula | complete_square
  "curriculum": "gcse"       // accepted but reserved: V1 is GCSE-only throughout
}
```

Multi-solution responses join the final step as `"x = r1; x = r2"`; `exact`
lists each root separately. `NO_SOLUTION` for `x^2+1=0` (reals) carries a
discriminant hint in the message. System responses add `bindings`:
`[{"variable": "x", "exact": "3", "approximate": "3.0"}, ...]` (single-variable
solvers fill one binding each). Inequality responses carry the solution phrase in
`exact` (e.g. `["x > 3"]`), an empty `approximate`, and a `flip_inequality_sign`
step whenever multiplying/dividing by a negative (the step explanation always
states the reversal rule).

Graph ops: `sample_graph` (`x_min/x_max/n`, discontinuity-split `segments` +
`excluded` poles), `analyze_graph` (roots, y-intercept, turning points, axis,
asymptotes, gradient — all engine cross-checked), `table_values`
(Fraction-exact `start/end/step` strings; `"undefined"` cells), and
`solve_intersection` (`inputs: [f, g]` → verified points; `[]` when parallel).

Practice (deterministic, offline): `practice_generate` (`topic` incl. `mixed`,
`difficulty`, `n ≤ 50`, `seed` → engine-verified numeric questions; same seed = same paper)
and `practice_score` (`attempts` with optional `difficulty` → per-topic mastery % with hint penalty,
`unlocked` difficulty gates per topic, weakest-topic recommendation; transparent, no ML).

Presentation LaTeX: every math string ships a `*_latex` twin rendered by SymPy
(`2*x**2` → `2 x^{2}`, `1/2` → `\frac{1}{2}`), structure-preserving so operand
arithmetic survives; unparseable text passes through unchanged. The UI typesets
with KaTeX and falls back to plain text — LaTeX never breaks math delivery.

History (offline-first, SQLite): every successful solve/transform auto-saves to
`$WORKBENCH_DATA_DIR/history.db` (default `~/.math-workbench/history.db`, schema
v1, failures never break math). `history_list` (`limit`, newest-first) and
`history_clear` manage it.

### Success response

```jsonc
{
  "ok": true,
  "op": "solve_linear",
  "interpretation": "2*x + 5 = 17",       // canonical parsed form echoed back (FR-IN-2)
  "result": {
    "exact": ["6"],                        // strings, SymPy sstr, exact preserved
    "approximate": ["6.0"],                // N(x, 15) strings, separate (FR-ALG-5)
    "steps": [
      {
        "operation": "subtract_both_sides",
        "operand": "5",
        "before": "2*x + 5 = 17",
        "after": "2*x = 12",
        "rule": "subtraction_property_of_equality",
        "explanation": "Subtract 5 from both sides to remove the constant term.",
        "verification": "verified",
        "before_latex": "2 x + 5 = 17",   // presentation twins (optional for readers)
        "after_latex": "2 x = 12",
        "operand_latex": "5"
      }
    ],
    "verification": "verified",            // verified | unverifiable (never silent)
    "domain_info": {"domain": "reals", "excluded": []},
    "bindings": [{"variable": "x", "exact": "6", "approximate": "6.0", "exact_latex": "6"}],
    "interpretation_latex": "2 x + 5 = 17",
    "exact_latex": ["6"]
  }
}
```

Other ops return their own `result` shapes (all carry `ok`/`op`/`interpretation`
around them): `parse` → `{kind}`; `sample_graph` → `{segments:[{xs,ys}], excluded}`;
`analyze_graph` → roots/intercept/turning/axis/asymptotes/gradient (+ `*_latex`);
`table_values` → `{xs, ys, ys_approx, xs_latex, ys_latex}` (`"undefined"` cells);
`solve_intersection` → `{points:[{kind,x,y,exact,exact_latex}]}`;
`history_list` → `{entries:[HistoryEntry]}`; `history_clear` → `{cleared}`;
`practice_generate` → `{questions:[{topic,difficulty,prompt,expected,op,prompt_latex,expected_latex}]}`;
`practice_score` → `{mastery, recommendation}`;
`ai_hint` → `{hint, level}`; `ai_explain` → `{explanation, provider}`;
`ai_mistake` → `{correct} | {correct:false, category, explanation, correction}`;
`ai_reflect` (adds `reflection` sentence; short reflections rejected) →
`{accepted, ...mistake}`.
Content ops: `worksheet_generate` (`topic`/`difficulty` or `spec` code, `n`,
`seed`, `with_answers`, `title` → verified prompts + answer key),
`spec_map` (curriculum codes), `concept_note` (`rule` → why-note),
`practice_examples` (engine-proved worked examples), `glossary_list/get`.
Persistence ops: `practice_record`, `practice_dashboard` (mastery + unlocks +
mistake breakdown), `review_due`/`review_answer` (SM-2 schedule),
`progress_streak`, `assignment_create/list`.

### Error response

```jsonc
{
  "ok": false, "op": "solve_linear",
  "error": {"code": "PARSE_ERROR" | "NO_SOLUTION" | "INFINITE_SOLUTIONS" | "UNSOLVABLE" | "VALIDATION_ERROR" | "INTERNAL_ERROR",
            "message": "I couldn't parse '2x + = 17'. Check the expression and try again."}
}
```

Rules: `NO_SOLUTION` (`EmptySet`) vs `INFINITE_SOLUTIONS` (`Reals` identity) are
distinct codes, not empty arrays. `UNSOLVABLE` (`ConditionSet`/NotImplemented)
says the engine could not solve — no guessed answer. `INTERNAL_ERROR` is the
boundary catch-all (student-safe message, traceback to stderr only).
`DOMAIN_ERROR` is defined in the taxonomy but currently unraised (reserved).

## 2. Python use-case signatures (application layer)

Application inverts dependencies: use-cases take `(raw input, parser, solver)`
with SymPy hidden behind ports (`SolverPort.solve_linear/transform/
check_equality/check_identity/check_system_equality/check_inequality/
solve_quadratic/solve_system/solve_inequality` returning
`LinearFacts/TransformFacts/QuadraticFacts/SystemFacts/InequalityFacts`).

```python
solve_linear(raw, parser, solver, domain=Domain.REALS) -> Solution
solve_quadratic(raw, parser, solver, domain=Domain.REALS, method="auto") -> Solution
solve_system(raws: list, parser, solver, domain=Domain.REALS) -> Solution
solve_inequality(raw, parser, solver, domain=Domain.REALS) -> Solution
transform_expression(raw, kind, parser, solver) -> Solution  # kind: simplify|expand|factorise
# parsing: parser.parse(raw) -> Expression directly (no parse_only use-case)
```

All take/return domain DTOs (`domain/models.py`), never SymPy objects.

## 3. Domain DTOs (stdlib-only dataclasses, frozen)

```python
@dataclass(frozen=True) class Expression:
    raw: str            # user input verbatim
    canonical: str      # sstr of parsed SymPy, e.g. "2*x + 5"
    kind: Literal["expression", "equation", "inequality"]

@dataclass(frozen=True) class Step:
    operation: str      # e.g. subtract_both_sides, divide_both_sides
    operand: str        # canonical string of operand
    before: str
    after: str
    rule: str           # e.g. subtraction_property_of_equality
    explanation: str    # GCSE wording, no advanced terms by default
    verification: Literal["verified", "unverifiable"]
    before_latex: str = ""   # presentation twins (optional for readers)
    after_latex: str = ""
    operand_latex: str = ""

@dataclass(frozen=True) class Binding:
    variable: str       # e.g. x
    exact: str
    approximate: str
    exact_latex: str = ""

@dataclass(frozen=True) class Solution:
    interpretation: str
    exact: tuple[str, ...]
    approximate: tuple[str, ...]
    steps: tuple[Step, ...]
    verification: Literal["verified", "unverifiable"]
    domain_info: DomainInfo
    bindings: tuple[Binding, ...] = ()
    interpretation_latex: str = ""
    exact_latex: tuple[str, ...] = ()
```

## 4. Port interfaces

```python
class ParserPort(abc.ABC):
    @abc.abstractmethod
    def parse(self, raw: str) -> Expression: ...

class SolverPort(abc.ABC):
    def solve_linear(self, expr, domain=Domain.REALS) -> LinearFacts: ...
    def solve_quadratic(self, expr, domain=Domain.REALS, method="auto") -> QuadraticFacts: ...
    def solve_system(self, exprs, domain=Domain.REALS) -> SystemFacts: ...
    def solve_inequality(self, expr, domain=Domain.REALS) -> InequalityFacts: ...
    def transform(self, expr, kind) -> TransformFacts: ...  # simplify|expand|factorise
    def check_equality(self, lhs, rhs, symbol, candidate) -> bool: ...
    def check_identity(self, before, after) -> bool: ...
    def check_system_equality(self, equations, bindings) -> bool: ...
    def check_inequality(self, lhs, rhs, rel, symbol, candidate) -> bool: ...
    # Facts = plain-data carriers (interpretation, solutions, set_tag, chain);
    # set_tag mirrors the solveset Set (finite | empty | infinite | condition).
```

Verification lives in `domain/verify.py` as pure string-level checks
(`solution_holds`, `system_holds`, `solution_self_consistent`) with the symbolic
equality injected from the adapter (`simplify(lhs-rhs)==0` semantics) — the
check stays independent of the solver that produced the candidate.

## 5. Step vocabulary (V1b: linear + quadratic)

| operation | rule | example |
|-----------|------|---------|
| `subtract_both_sides` | `subtraction_property_of_equality` | `2x+5=17 → 2x=12` |
| `add_both_sides` | `addition_property_of_equality` | `x-4=9 → x=13` |
| `divide_both_sides` | `division_property_of_equality` | `2x=12 → x=6` |
| `multiply_both_sides` | `multiplication_property_of_equality` | `x/3=4 → x=12` |
| `distribute` | `distributive_property` | `2(x+3)=14 → 2x+6=14` |
| `collect_like_terms` | `combining_like_terms` | `2x+3x=10 → 5x=10` |
| `rewrite` | `equivalent_form` | `x²=4x-3 → x²-4x+3=0` |
| `factorise_equation` | `factorisation` | `x²-5x+6=0 → (x-2)(x-3)=0` |
| `apply_zero_product` | `zero_product_property` | `(x-3)=0 → x=3` |
| `identify_coefficients` | `standard_quadratic_form` | `a=1, b=-5, c=6` |
| `compute_discriminant` | `discriminant` | `25-24=1` |
| `apply_quadratic_formula` | `quadratic_formula` | `x=(-(-5)±√1)/2` |
| `complete_the_square` | `completing_the_square` | `x²+6x+5=0 → (x+3)²=4` |
| `take_square_root_pm` | `square_root_property` | `(x+3)²=4 → x+3=±2` |
| `scale_equation` | `multiplication_property_of_equality` | `2x+y=7 ×3` |
| `eliminate_variable` | `elimination_method` | `add/subtract to kill y` |
| `substitute_back` | `substitution_method` | `x=3 into x-y=2` |
| `flip_inequality_sign` | `inequality_sign_reversal` | `-2x>6 → 2x<-6` |
| `simplify_expression` | `simplification` | `2x+3x → 5x` |
| `expand_expression` | `expansion` | `(x+1)² → x²+2x+1` |
| `factorise_expression` | `factorisation` | `x²+2x+1 → (x+1)²` |

## 6. Compatibility promise

- Adding ops/steps is backward-compatible (new `operation` strings).
- Renaming any field or error code is a **major** contract bump documented in
  `lifecycle-log.md` + ADR.
