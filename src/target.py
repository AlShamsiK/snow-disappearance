"""Construct the prediction target: the date of sustained snow disappearance.

Definition used here, stated explicitly because the whole project rests on it:

    Within a water year, the sustained snow disappearance date is the first day D
    on which SWE <= SWE_ZERO_THRESHOLD and on which SWE remains at or below that
    threshold for the following SUSTAIN_DAYS consecutive days.

The search starts at the forecast origin (1 March) so that a snow-free autumn
before the snowpack builds cannot be mistaken for disappearance. The "sustained"
requirement is what separates a real melt-out from a brief mid-season bare-ground
spell or a sensor dropout, and from an ephemeral late-season snowfall that melts
within days.

Station-years with no qualifying day are returned as missing and handled
explicitly rather than silently dropped.
"""

from __future__ import annotations

import pandas as pd

from . import config


def water_year(dates: pd.Series) -> pd.Series:
    """Map dates to their water year (1 Oct of Y-1 through 30 Sep of Y)."""
    dates = pd.to_datetime(dates)
    return dates.dt.year + (dates.dt.month >= config.WATER_YEAR_START_MONTH).astype(int)


def days_from_origin(date: pd.Timestamp, wy: int) -> int:
    """Days between the 1 March forecast origin of water year `wy` and `date`.

    Modelling the number of days remaining rather than a raw day-of-year keeps
    the target comparable across leap and non-leap years.
    """
    origin = pd.Timestamp(
        year=wy, month=config.FORECAST_ORIGIN_MONTH, day=config.FORECAST_ORIGIN_DAY
    )
    return (pd.Timestamp(date) - origin).days


def sustained_disappearance_date(
    swe: pd.Series,
    wy: int,
    swe_threshold: float | None = None,
    sustain_days: int | None = None,
) -> pd.Timestamp | None:
    """First sustained snow-free day in one station-water-year.

    Parameters
    ----------
    swe
        Daily SWE indexed by date, covering one water year, sorted ascending.
    wy
        The water year, used to locate the forecast origin and the search window.
    swe_threshold, sustain_days
        Override the configured definition. Used by the sensitivity ablation.

    Returns
    -------
    The disappearance date, or None if the snowpack never disappears within the
    search window or the record is too incomplete to tell.
    """
    threshold = (
        config.SWE_ZERO_THRESHOLD if swe_threshold is None else swe_threshold
    )
    n_sustain = config.SUSTAIN_DAYS if sustain_days is None else sustain_days

    raise NotImplementedError(
        "Implement once the SWE units, missing-value encoding and the chosen "
        "values of SWE_ZERO_THRESHOLD and SUSTAIN_DAYS are settled."
    )


def build_targets(daily: pd.DataFrame) -> pd.DataFrame:
    """One row per station-water-year with the target and its diagnostics.

    Returns columns:
        station, water_year, disappearance_date, days_from_march1,
        target_is_censored, reason_missing
    """
    raise NotImplementedError


if __name__ == "__main__":
    pass
