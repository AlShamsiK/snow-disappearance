"""Cleaning, quality control and station screening.

Rubric item: audit missingness, duplicates, identifiers and labels, and justify
every cleaning decision. Each function below returns both the cleaned frame and
an audit record so the notebook can report what was removed and why.
"""

from __future__ import annotations

import pandas as pd

from . import config


def audit_raw(daily: pd.DataFrame) -> pd.DataFrame:
    """Counts of missing values, duplicate station-date rows, and out-of-range
    values, per station and water year. Produced before any modification."""
    raise NotImplementedError


def drop_duplicates(daily: pd.DataFrame) -> pd.DataFrame:
    """Remove repeated station-date rows, keeping the first occurrence."""
    raise NotImplementedError


def flag_swe_anomalies(daily: pd.DataFrame) -> pd.DataFrame:
    """Flag known snow pillow failure modes: negative SWE, implausible
    day-to-day jumps, flat-lined stretches, and isolated zeros inside an
    otherwise continuous snowpack."""
    raise NotImplementedError


def fill_missing(daily: pd.DataFrame) -> pd.DataFrame:
    """Interpolate short gaps only. Long gaps invalidate the station-year and
    are left missing so screening can remove it."""
    raise NotImplementedError


def screen_stations(daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the screening rules in config. Returns the retained data and a
    table of exclusions with reasons."""
    raise NotImplementedError


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
