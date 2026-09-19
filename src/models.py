"""Baselines and machine learning models.

The baselines matter as much as the model. A gradient boosting result means
nothing without a climatology number beside it.
"""

from __future__ import annotations

from . import config


# --------------------------------------------------------------------------
# Baselines
# --------------------------------------------------------------------------
class ClimatologyBaseline:
    """Predict each station's mean (or median) historical disappearance date,
    estimated on training water years only. This is the number the ML model has
    to beat, and the denominator of the skill score."""

    def fit(self, X, y):
        raise NotImplementedError

    def predict(self, X):
        raise NotImplementedError


class DegreeDayBaseline:
    """Physically motivated baseline: melt the 1 March SWE at a calibrated melt
    factor driven by accumulated degree-days, and report the date the pack is
    exhausted. Calibrated on training years only."""

    def fit(self, X, y):
        raise NotImplementedError

    def predict(self, X):
        raise NotImplementedError


class SWEOnlyLinearBaseline:
    """Ordinary least squares on 1 March SWE alone. Establishes how much of the
    signal is simply how much snow is on the ground."""

    def fit(self, X, y):
        raise NotImplementedError

    def predict(self, X):
        raise NotImplementedError


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
def make_ridge():
    raise NotImplementedError


def make_random_forest():
    raise NotImplementedError


def make_gradient_boosting():
    raise NotImplementedError


def make_quantile_models():
    """Lower and upper quantile regressors for the prediction interval shown in
    the demo."""
    raise NotImplementedError
