"""BKT-lite: closed-form updates, bounds, monotonicity, gates, risk flags."""

import pytest

from workbench_math.practice.at_risk import detect
from workbench_math.practice.bkt import BKTParams, predict_correct, track, update
from workbench_math.practice.mastery import bkt_gated_levels


def test_bkt_update_hand_computed():
    params = BKTParams(p_init=0.3, p_learn=0.1, p_slip=0.1, p_guess=0.2)
    assert update(0.3, True, params) == pytest.approx(0.6926829)
    assert update(0.3, False, params) == pytest.approx(0.1457627)
    assert predict_correct(0.3, params) == pytest.approx(0.41)


def test_bkt_bounds_and_monotone():
    assert track((True,) * 10) > 0.95
    assert track((False,) * 10) < 0.5
    assert 0.0 <= track((True, False, True)) <= 1.0
    assert update(0.0, False) >= 0.0 and update(1.0, True) <= 1.0


def test_bkt_gates():
    assert bkt_gated_levels(0.5, 1) == ["beginner", "basic"]
    assert bkt_gated_levels(0.97, 10) == ["beginner", "basic", "intermediate", "advanced", "exam"]
    assert bkt_gated_levels(0.97, 2) == ["beginner", "basic"]  # needs evidence


def _attempt(topic, correct, hints=0, mistake=""):
    from workbench_math.ports.practice_store import PracticeAttempt

    return PracticeAttempt(id=1, timestamp="2026-10-07T10:00:00", topic=topic,
                           difficulty="basic", correct=correct, hints_used=hints,
                           mistake=mistake)


def test_risk_flags():
    struggling = tuple(_attempt("linear", False) for _ in range(3))
    flags = detect(struggling)
    assert any(f.flag == "struggling" for f in flags)

    hinted = tuple(_attempt("linear", True, hints=3) for _ in range(6))
    assert any(f.flag == "hint-dependent" for f in detect(hinted))

    spike = tuple(_attempt("linear", i % 2 == 0, mistake="sign") for i in range(6))
    assert any(f.flag == "repeated-sign" for f in detect(spike))

    healthy = tuple(_attempt("linear", True) for _ in range(5))
    assert detect(healthy) == ()


def test_store_bkt_and_override(tmp_path):
    from workbench_math.adapters.sqlite_practice import SqlitePractice

    store = SqlitePractice(tmp_path / "p.db")
    assert store.get_bkt("linear") == (0.3, 0)
    store.set_bkt("linear", 0.9, 5)
    assert store.get_bkt("linear") == (0.9, 5)
    row = store.record_attempt("linear", "basic", False, 0, "")
    assert store.record_override(row, True) is True
    assert store.recent_attempts()[0].correct is True
    assert store.record_override(9999, True) is False
