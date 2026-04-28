import pytest

from stocksense.core.calibration import brier_score


def test_brier_score_for_binary_forecast():
    assert brier_score(0.8, True) == 0.04
    assert brier_score(0.8, False) == 0.64


def test_brier_score_rejects_invalid_probability():
    with pytest.raises(ValueError):
        brier_score(1.2, True)
