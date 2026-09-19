"""Feature construction as of the 1 March forecast origin.

LEAKAGE RULE: every feature must be computable from data dated strictly before
1 March of the target water year, plus static station attributes, plus
statistics estimated on training water years only. assert_no_leakage() is the
guard and is called in the notebook.
"""

from __future__ import annotations

import pandas as pd

from . import config


def snowpack_state(daily: pd.DataFrame) -> pd.DataFrame:
    """Condition of the snowpack on 1 March: SWE, snow depth, implied density,
    days since peak SWE so far, SWE relative to the station's training-set
    median for that date."""
    raise NotImplementedError


def accumulation_season_aggregates(daily: pd.DataFrame) -> pd.DataFrame:
    """Oct 1 to Feb 28/29 summaries: cumulative precipitation, mean and anomaly
    temperature, accumulated degree-days above freezing, count of mid-winter
    melt events, timing of first substantial accumulation."""
    raise NotImplementedError


def static_attributes(stations: pd.DataFrame) -> pd.DataFrame:
    """Elevation, latitude, longitude, and station climatology computed on
    training water years only."""
    raise NotImplementedError


def assert_no_leakage(features: pd.DataFrame, daily: pd.DataFrame) -> None:
    """Fail loudly if any feature depends on data dated on or after 1 March of
    its own water year, or on statistics computed over test water years."""
    raise NotImplementedError


def build_feature_table() -> pd.DataFrame:
    """One row per station-water-year, joined to the target."""
    raise NotImplementedError


if __name__ == "__main__":
    pass
