"""AI services: deterministic hints, mistake classification, grounded tutor."""

import pytest

from workbench_math.ai.hints import hint
from workbench_math.ai.mistakes import classify
from workbench_math.ai.provider import AIProviderError, StubProvider
from workbench_math.ai.tutor import TutorReply, TutorService
from workbench_math.domain.exceptions import ValidationError
from workbench_math.domain.models import Solution
from workbench_math.domain.steps import make_step


def _solution():
    steps = (
        make_step("subtract_both_sides", "5", "2*x + 5 = 17", "2*x = 12"),
        make_step("divide_both_sides", "2", "2*x = 12", "x = 6"),
    )
    return Solution(interpretation="2*x + 5 = 17", exact=("6",),
                    approximate=("6.0",), steps=steps)


def identical(a, b):
    return a == b  # fake identity check for unit tier


def test_stub_deterministic_offline():
    provider = StubProvider()
    assert provider.complete("hello") == provider.complete("hello")
    assert provider.complete("hello").startswith("[offline")


def test_hint_ladder_never_leaks_early():
    sol = _solution()
    l1, l2, l3 = hint(sol, 1), hint(sol, 2), hint(sol, 3)
    for text in (l1, l2, l3):
        assert "x = 6" not in text and "Answer" not in text
    assert "2*x = 12" in hint(sol, 4)  # next step revealed
    l5 = hint(sol, 5)
    assert "x = 6" in l5 and "Answer" in l5


def test_hint_validation():
    sol = _solution()
    with pytest.raises(ValidationError):
        hint(sol, 0)
    with pytest.raises(ValidationError):
        hint(sol, 6)
    with pytest.raises(ValidationError):
        hint(sol, 1, step_index=9)


def test_mistake_bracket_product_example():
    step = make_step("distribute", "2*(x + 3)", "2*(x + 3) = 14", "2*x + 6 = 14")
    mistake = classify(step, "2*x + 3 = 14", identical)
    assert mistake is not None
    assert mistake.category == "bracket_distribution"
    assert "2*x + 6 = 14" in mistake.explanation  # minimal correction shown


def test_mistake_correct_step_returns_none():
    step = make_step("divide_both_sides", "2", "2*x = 12", "x = 6")
    assert classify(step, "x = 6", identical) is None


def test_mistake_sign_and_unparseable():
    step = make_step("subtract_both_sides", "5", "2*x + 5 = 17", "2*x = 12")
    mistake = classify(step, "2*x = 22", identical)
    assert mistake.category == "sign"

    def _boom(a, b):
        raise ValueError("nope")

    bad = classify(step, "@@@", _boom)
    assert bad.category == "unparseable"


def test_tutor_stub_and_fallback():
    sol = _solution()
    reply = TutorService().explain(sol, "Why subtract 5?")
    assert isinstance(reply, TutorReply) and reply.provider == "stub"

    class _Failing(StubProvider):
        name = "broken"

        def complete(self, prompt, **kwargs):
            raise AIProviderError("down")

    fallen = TutorService(_Failing()).explain(sol, "Why?")
    assert fallen.provider == "fallback"
    assert "6" in fallen.explanation  # verified math stays visible
