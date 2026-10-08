"""BKT-lite: Bayesian Knowledge Tracing per topic (pure, deterministic).

Standard BKT (Corbett & Anderson 1995): binary latent mastery per skill,
four fixed literature-standard parameters, five closed-form updates. No fitting
library, no neural net — interpretable probabilities the teacher UI can show
("mastery 0.97 because: 12 correct, 1 slip"). The transparent percentage
scorer stays alongside as the explainer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BKTParams:
    p_init: float = 0.3
    p_learn: float = 0.1
    p_slip: float = 0.1
    p_guess: float = 0.2


def _clamp(p: float) -> float:
    return max(0.0, min(1.0, p))


def update(prior: float, correct: bool, params: BKTParams = BKTParams()) -> float:
    """Posterior P(L_{t+1}) after one observed response."""
    p_l, s, g, t = _clamp(prior), params.p_slip, params.p_guess, params.p_learn
    if correct:
        posterior = p_l * (1 - s) / (p_l * (1 - s) + (1 - p_l) * g)
    else:
        posterior = p_l * s / (p_l * s + (1 - p_l) * (1 - g))
    return _clamp(posterior + (1 - posterior) * t)


def predict_correct(prior: float, params: BKTParams = BKTParams()) -> float:
    p_l = _clamp(prior)
    return _clamp(p_l * (1 - params.p_slip) + (1 - p_l) * params.p_guess)


def track(history: tuple[bool, ...], params: BKTParams = BKTParams()) -> float:
    """Fold a correctness history into P(mastery). Oldest first."""
    p = params.p_init
    for correct in history:
        p = update(p, correct, params)
    return p
