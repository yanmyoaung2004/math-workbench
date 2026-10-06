"""Domain value objects: immutability, equality, hashing, defaults."""

from workbench_math.domain.models import (
    Domain,
    DomainInfo,
    Expression,
    Solution,
    Step,
    Verification,
)


def test_expression_equality_by_value():
    assert Expression(raw="2x", canonical="2*x", kind="expression") == Expression(
        raw="2x", canonical="2*x", kind="expression"
    )


def test_step_frozen():
    import dataclasses

    step = Step(
        operation="divide_both_sides", operand="2", before="2*x = 12",
        after="x = 6", rule="division_property_of_equality", explanation="Divide.",
    )
    try:
        step.after = "x = 7"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        pass
    else:
        raise AssertionError("Step must be frozen")
    assert step.verification == Verification.VERIFIED.value


def test_solution_defaults():
    sol = Solution(interpretation="x = 6", exact=("6",), approximate=("6.0",), steps=())
    assert sol.verification == Verification.VERIFIED.value
    assert sol.domain_info == DomainInfo(domain=Domain.REALS.value)
    assert hash(sol)  # usable in sets/dicts (frozen + hashable)
