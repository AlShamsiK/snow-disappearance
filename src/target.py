"""Construct the prediction target: the date of sustained snow disappearance.

The raw data carry no label. The target is derived from the SWE series, which
makes this a supervised regression problem with a constructed label, and the
construction rule is a modelling decision that must be stated and tested.

Definition:

    Within a water year, the sustained snow disappearance date is the first day D
    on or after the 1 March forecast origin on which SWE <= SWE_ZERO_THRESHOLD and
    on which SWE remains at or below that threshold for the following
    SUSTAIN_DAYS consecutive days.

The search starts at the forecast origin so that a snow-free autumn before the
snowpack builds cannot be mistaken for disappearance. The "sustained"
requirement is what separates a real melt-out from a brief mid-season
bare-ground spell or a sensor dropout, and from an ephemeral late-season
snowfall that melts within days.

Station-years with no qualifying day are returned with a reason and handled
explicitly rather than silently dropped.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def water_year(dates: pd.Series) -> pd.Series:
    """Map dates to their water year (1 Oct of Y-1 through 30 Sep of Y)."""
    dates = pd.to_datetime(dates)
    return dates.dt.year + (dates.dt.month >= config.WATER_YEAR_START_MONTH).astype(int)


def forecast_origin(wy: int) -> pd.Timestamp:
    return pd.Timestamp(year=wy, month=config.FORECAST_ORIGIN_MONTH, day=config.FORECAST_ORIGIN_DAY)


def days_from_origin(date: pd.Timestamp, wy: int) -> int:
    """Days between the 1 March forecast origin of water year `wy` and `date`.

    Modelling the number of days remaining rather than a raw day-of-year keeps
    the target comparable across leap and non-leap years.
    """
    return (pd.Timestamp(date) - forecast_origin(wy)).days


def sustained_disappearance_date(
    swe: pd.Series,
    wy: int,
    swe_threshold: float | None = None,
    sustain_days: int | None = None,
) -> tuple[pd.Timestamp | None, str]:
    """First sustained snow-free day in one station-water-year.

    Parameters
    ----------
    swe
        Daily SWE in mm indexed by date, covering one water year, sorted.
    wy
        The water year, used to locate the forecast origin and search window.
    swe_threshold, sustain_days
        Override the configured definition. Used by the sensitivity ablation.

    Returns
    -------
    (date, reason). date is None when no qualifying day exists; reason is one
    of "melt_out", "gone_at_origin", "never_disappears", "no_data",
    "gap_before_melt_out".
    """
    thr = config.SWE_ZERO_THRESHOLD if swe_threshold is None else swe_threshold
    n = config.SUSTAIN_DAYS if sustain_days is None else sustain_days
    origin = forecast_origin(wy)
    end = pd.Timestamp(year=wy, month=config.MELT_OUT_SEARCH_END_MONTH, day=config.MELT_OUT_SEARCH_END_DAY)
    window = swe.loc[origin:end]
    if window.notna().sum() == 0:
        return None, "no_data"
    below = (window <= thr).astype(float)
    below[window.isna()] = np.nan
    # a day qualifies when it and the next n days are all known and all below
    vals = below.to_numpy()
    for i in range(len(vals) - n):
        block = vals[i:i + n + 1]
        if np.all(block == 1.0):
            date = window.index[i]
            # a long unknown stretch before the melt-out date makes it unreliable
            gap = window.iloc[:i].isna()
            if gap.sum() > config.MAX_INTERP_GAP_DAYS:
                return date, "gap_before_melt_out"
            return date, ("gone_at_origin" if i == 0 else "melt_out")
    return None, "never_disappears"


def build_targets(daily: pd.DataFrame) -> pd.DataFrame:
    """One row per station-water-year with the target and its diagnostics.

    Columns:
        station, water_year, disappearance_date, days_from_march1,
        target_is_censored, reason, swe_march1_mm, peak_swe_mm, peak_swe_date
    """
    d = daily.copy()
    if "water_year" not in d:
        d["water_year"] = water_year(d["date"])
    rows = []
    for (st, wy), g in d.groupby(["station", "water_year"], sort=True):
        s = g.set_index("date")["WTEQ"].sort_index()
        date, reason = sustained_disappearance_date(s, wy)
        origin = forecast_origin(wy)
        rows.append({
            "station": st,
            "water_year": int(wy),
            "disappearance_date": date,
            "days_from_march1": days_from_origin(date, wy) if date is not None else np.nan,
            "target_is_censored": date is None,
            "reason": reason,
            "swe_march1_mm": s.get(origin, np.nan),
            "peak_swe_mm": s.max(),
            "peak_swe_date": s.idxmax() if s.notna().any() else pd.NaT,
        })
    return pd.DataFrame(rows)


def main() -> None:
    daily = pd.read_csv(config.DATA_PROCESSED / "daily_clean.csv.gz", parse_dates=["date"])
    t = build_targets(daily)
    t.to_csv(config.DATA_PROCESSED / "targets.csv", index=False)
    print(t["reason"].value_counts())


if __name__ == "__main__":
    main()
