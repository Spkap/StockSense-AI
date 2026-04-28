from __future__ import annotations


def brier_score(probability: float, outcome: bool) -> float:
    if probability < 0 or probability > 1:
        raise ValueError("probability must be between 0 and 1")
    observed = 1.0 if outcome else 0.0
    return round((probability - observed) ** 2, 6)
