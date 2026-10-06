# Math Engine API Contracts (Phase 0 → 1b binding)

Implementations MUST satisfy these shapes. Tests enforce them
(`tests/unit/test_contracts.py`, golden corpus). Version: `v1b`.

## 1. JSON sidecar protocol (stdio JSON-lines)

One request line → one response line. UTF-8, `\n`-terminated.

### Request

```jsonc
{
  "op": "solve_linear" | "solve_quadratic" | "solve_system" | "solve_inequality" | "simplify" | "expand" | "factorise" | "parse" | "sample_graph" | "analyze_graph" | "table_values" | "solve_intersection",
  "input": "2x + 5 = 17",   // raw user string, required (except solve_system)
  "equations": ["2x + y = 7", "x - y = 2"],  // solve_system only: exactly 2
  "domain": "reals",         // optional, default "reals" (GCSE); "complex" opts in
  "method": "auto",          // solve_quadratic only: auto | factorise | formula | complete_square
  "curriculum": "gcse"       // optional, default "gcse"; gates advanced output
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
        "verification": "verified"
      }
    ],
    "verification": "verified",            // verified | unverifiable (never silent)
    "domain_info": {"domain": "reals", "excluded": []}
  }
}
```

### Error response

```jsonc
{
  "ok": false, "op": "solve_linear",
  "error": {"code": "PARSE_ERROR" | "NO_SOLUTION" | "INFINITE_SOLUTIONS" | "UNSOLVABLE" | "DOMAIN_ERROR" | "VALIDATION_ERROR",
            "message": "I couldn't parse '2x + = 17'. Check the expression and try again."}
}
```

Rules: `NO_SOLUTION` (`EmptySet`) vs `INFINITE_SOLUTIONS` (`Reals` identity) are
distinct codes, not empty arrays. `UNSOLVABLE` (`ConditionSet`/NotImplemented)
says the engine could not solve — no guessed answer.

## 2. Python use-case signatures (application layer)

```python
solve_linear(expr: str, domain: Domain = Domain.REALS) -> Solution
simplify_expression(expr: str) -> Solution          # single-result, steps=[transform]
expand_expression(expr: str) -> Solution
factorise_expression(expr: str) -> Solution
parse_only(expr: str) -> Expression                 # for FR-IN-2 echo + error UX
```

All take/return domain DTOs (`domain/models.py`), never SymPy objects.

## 3. Domain DTOs (stdlib-only dataclasses, frozen)

```python
@dataclass(frozen=True) class Expression:
    raw: str            # user input verbatim
    canonical: str      # sstr of parsed SymPy, e.g. "2*x + 5"
    kind: Literal["expression", "equation"]

@dataclass(frozen=True) class Step:
    operation: str      # e.g. subtract_both_sides, divide_both_sides
    operand: str        # canonical string of operand
    before: str
    after: str
    rule: str           # e.g. subtraction_property_of_equality
    explanation: str    # GCSE wording, no advanced terms by default
    verification: Literal["verified", "unverifiable"]

@dataclass(frozen=True) class Solution:
    interpretation: str
    exact: tuple[str, ...]
    approximate: tuple[str, ...]
    steps: tuple[Step, ...]
    verification: Literal["verified", "unverifiable"]
    domain_info: DomainInfo
```

## 4. Port interfaces

```python
class ParserPort(abc.ABC):
    @abc.abstractmethod
    def parse(self, raw: str) -> Expression: ...

class SolverPort(abc.ABC):
    @abc.abstractmethod
    def solve_linear(self, expr: Expression, domain: Domain) -> SolverResult: ...
    # SolverResult = raw exact SymPy-strings + steps data + set_tag
    # (EmptySet | FiniteSet | Reals-identity | ConditionSet-unsolvable)
```

Verification lives in `domain/verify.py` as a pure function
(`check_solution(equation, candidate) -> bool` via `simplify(lhs-rhs)==0`),
called by application — not hidden inside the SymPy adapter (so the check is independent).

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

Inequality sign-flip (`…reverse the inequality…`) lands with A3.

## 6. Compatibility promise

- Adding ops/steps is backward-compatible (new `operation` strings).
- Renaming any field or error code is a **major** contract bump documented in
  `lifecycle-log.md` + ADR.
