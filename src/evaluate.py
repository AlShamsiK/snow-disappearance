"""Splits, metrics and skill scores.

Random k-fold is wrong for this data. Station-years are correlated in time and
across nearby stations, so a random split leaks both future information and
information from neighbouring stations in the same year.
"""

from __future__ import annotations

from . import config


# --------------------------------------------------------------------------
# Splits
# --------------------------------------------------------------------------
def forward_chaining_splits(df):
    """Expanding-window splits over water years: train on years up to t, test on
    year t+1. Mimics operational forecasting."""
    raise NotImplementedError


def leave_one_station_out(df):
    """Tests generalisation to a station never seen in training."""
    raise NotImplementedError


def spatial_block_splits(df):
    """Hold out whole regions to blunt spatial autocorrelation between nearby
    stations."""
    raise NotImplementedError


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------
def mae_days(y_true, y_pred):
    raise NotImplementedError


def rmse_days(y_true, y_pred):
    raise NotImplementedError


def bias_days(y_true, y_pred):
    """Signed error. A model that is right on average but late every year in
    warm springs is a different failure from one that is simply noisy."""
    raise NotImplementedError


def skill_score(y_true, y_pred, y_baseline):
    """Fractional reduction in error against a baseline, normally climatology.
    This is the honest headline number for the report."""
    raise NotImplementedError


def interval_coverage(y_true, lower, upper):
    """Share of observations falling inside the predicted interval."""
    raise NotImplementedError


# --------------------------------------------------------------------------
# Ablations
# --------------------------------------------------------------------------
def feature_group_ablation(*args, **kwargs):
    """Snowpack only, plus accumulation-season weather, plus static attributes."""
    raise NotImplementedError


def target_definition_sensitivity(*args, **kwargs):
    """Re-run with different SUSTAIN_DAYS and SWE_ZERO_THRESHOLD values and
    report how much the conclusions move."""
    raise NotImplementedError


def error_by_elevation_band(*args, **kwargs):
    raise NotImplementedError
