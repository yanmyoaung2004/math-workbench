"""Mastery scoring: exact deterministic percentages and recommendations."""

from workbench_math.practice.mastery import Attempt, attempt_score, recommend, topic_mastery


def test_attempt_scores():
    assert attempt_score(Attempt("linear", True, 0)) == 1.0
    assert attempt_score(Attempt("linear", True, 2)) == 0.7
    assert attempt_score(Attempt("linear", True, 5)) == 0.4
    assert attempt_score(Attempt("linear", False, 0)) == 0.0


def test_mastery_and_recommendation():
    attempts = (
        Attempt("linear", True, 0), Attempt("linear", True, 0),
        Attempt("quadratics", True, 1), Attempt("quadratics", False, 0),
    )
    mastery = topic_mastery(attempts)
    assert mastery == {"linear": 100.0, "quadratics": 35.0}
    assert recommend(mastery) == "Recommended practice: quadratics (35.0% mastery)."


def test_empty_and_balanced():
    assert "beginner" in recommend({})
    assert recommend({"linear": 92.0}) == "Balanced across topics — try exam-style questions."
