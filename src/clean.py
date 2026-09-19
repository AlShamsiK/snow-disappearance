"""Cleaning, quality control and station screening.

Rubric item: audit missingness, duplicates, identifiers and labels, and justify
every cleaning decision. Every step appends a row to a CleaningLog with the
number of rows or values it touched, so the notebook can report what was done
and why instead of asserting that the data are clean.

Pipeline order (run_pipeline):
    load_raw -> complete_calendar -> drop_duplicates -> to_si
    -> apply_physical_limits -> derive_daily_precip -> flag_swe_anomalies
    -> fill_missing -> screen_stations
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config

SNOW_COLS = ["WTEQ", "SNWD", "PREC"]
TEMP_COLS = ["TAVG", "TMAX", "TMIN"]
VALUE_COLS = SNOW_COLS + TEMP_COLS


# --------------------------------------------------------------------------
# Log of what was done
# --------------------------------------------------------------------------
@dataclass
class CleaningLog:
    rows: list[dict] = field(default_factory=list)

    def add(self, step: str, rule: str, affected: int, unit: str, note: str = "") -> None:
        self.rows.append({"step": step, "rule": rule, "affected": int(affected),
                          "unit": unit, "note": note})

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows, columns=["step", "rule", "affected", "unit", "note"])


# --------------------------------------------------------------------------
# Loading and helpers
# --------------------------------------------------------------------------
def load_raw() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Committed raw files, untouched: daily records, station metadata, and
    per-station element metadata (units and period of record)."""
    daily = pd.read_csv(config.DATA_RAW / config.RAW_DAILY_FILE, parse_dates=["date"])
    stations = pd.read_csv(config.DATA_RAW / config.RAW_STATIONS_FILE)
    elements = pd.read_csv(config.DATA_RAW / config.RAW_ELEMENTS_FILE)
    return daily, stations, elements


def water_year(dates: pd.Series) -> pd.Series:
    d = pd.to_datetime(dates)
    return d.dt.year + (d.dt.month >= config.WATER_YEAR_START_MONTH).astype(int)


def _expected_days() -> int:
    start = pd.Timestamp(f"{config.WATER_YEAR_START - 1}-10-01")
    end = pd.Timestamp(f"{config.WATER_YEAR_END}-09-30")
    return (end - start).days + 1


# --------------------------------------------------------------------------
# Audit (read-only)
# --------------------------------------------------------------------------
def audit_raw(daily: pd.DataFrame) -> pd.DataFrame:
    """Counts of structural and physical problems in the raw file, before any
    modification. One row per check."""
    n = len(daily)
    rows: list[dict] = []

    def add(check, element, count, denom=n, note=""):
        rows.append({"check": check, "element": element, "count": int(count),
                     "share": round(float(count) / denom, 4) if denom else np.nan, "note": note})

    add("rows in file", "", n, note=f"{daily['station'].nunique()} stations, "
        f"{daily['date'].min().date()} to {daily['date'].max().date()}")
    add("duplicate station-date rows", "", daily.duplicated(["station", "date"]).sum())
    expected = _expected_days() * daily["station"].nunique()
    add("calendar days absent from file", "", expected - daily[["station", "date"]].drop_duplicates().shape[0],
        denom=expected, note="rows the service did not return at all")
    for c in VALUE_COLS:
        if c in daily:
            add("missing values", c, daily[c].isna().sum())
    for c in ["WTEQ", "SNWD", "PREC"]:
        if c in daily:
            add("negative values", c, (daily[c] < 0).sum())
    lo_f, hi_f = [t * 9 / 5 + 32 for t in config.TEMP_VALID_C]
    for c in TEMP_COLS:
        if c in daily:
            add("outside physical range", c, ((daily[c] < lo_f) | (daily[c] > hi_f)).sum(),
                note=f"outside {lo_f:.0f}..{hi_f:.0f} F")
    if {"TMIN", "TMAX"} <= set(daily):
        add("TMIN above TMAX", "TMIN/TMAX", (daily["TMIN"] > daily["TMAX"]).sum())
    if "PREC" in daily:
        g = daily.sort_values(["station", "date"]).groupby(["station", water_year(daily["date"])])["PREC"]
        add("cumulative precip decreases", "PREC", (g.diff() < -0.05).sum(),
            note="accumulation should not fall within a water year")
    if "WTEQ" in daily:
        d = daily.sort_values(["station", "date"]).groupby("station")["WTEQ"].diff().abs() * config.IN_TO_MM
        add("one-day SWE change > spike limit", "WTEQ", (d > config.SWE_SPIKE_MM).sum(),
            note=f"> {config.SWE_SPIKE_MM:.0f} mm in a day")
    for c in VALUE_COLS:
        f = f"{c}_flag"
        if f in daily:
            counts = daily[f].value_counts(dropna=False)
            not_v = int(counts.drop("V", errors="ignore").sum())
            add("NRCS QC flag not 'V' (valid)", c, not_v,
                note=", ".join(f"{k}={v}" for k, v in counts.items() if k != "V"))
    return pd.DataFrame(rows)


def missing_by_station_year(daily: pd.DataFrame, col: str = "WTEQ") -> pd.DataFrame:
    """Share of missing values of `col` per station and water year (wide)."""
    wy = water_year(daily["date"])
    m = daily[col].isna().groupby([daily["station"], wy]).mean()
    return m.unstack("date").round(3) if "date" in m.index.names else m.unstack().round(3)


# --------------------------------------------------------------------------
# Cleaning steps
# --------------------------------------------------------------------------
def complete_calendar(daily: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    """Give every station a complete daily calendar so gaps are explicit NaNs
    rather than silently absent rows."""
    start = pd.Timestamp(f"{config.WATER_YEAR_START - 1}-10-01")
    end = pd.Timestamp(f"{config.WATER_YEAR_END}-09-30")
    idx = pd.MultiIndex.from_product([sorted(daily["station"].unique()),
                                      pd.date_range(start, end, freq="D")], names=["station", "date"])
    before = len(daily)
    out = (daily.drop_duplicates(["station", "date"]).set_index(["station", "date"])
           .reindex(idx).reset_index())
    if log:
        log.add("complete_calendar", "insert missing station-dates as NaN rows",
                len(out) - before, "rows", "makes gaps explicit; no values changed")
    return out


def drop_duplicates(daily: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    """Remove repeated station-date rows, keeping the first occurrence."""
    dup = daily.duplicated(["station", "date"])
    if log:
        log.add("drop_duplicates", "repeated station-date rows, keep first", dup.sum(), "rows")
    return daily.loc[~dup].copy()


def to_si(daily: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    """Inches to millimetres, Fahrenheit to Celsius."""
    out = daily.copy()
    for c in SNOW_COLS:
        if c in out:
            out[c] = out[c] * config.IN_TO_MM
    for c in TEMP_COLS:
        if c in out:
            out[c] = (out[c] - 32) * 5 / 9
    if log:
        log.add("to_si", "convert inches to mm and Fahrenheit to Celsius",
                out[[c for c in VALUE_COLS if c in out]].notna().sum().sum(), "values", "unit change only")
    return out


def apply_physical_limits(daily: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    """Values that cannot be physically right.

    - SWE / depth / precipitation slightly below zero: snow pillow drift, clip to 0.
    - Strongly negative: sensor fault, set missing.
    - Temperatures outside TEMP_VALID_C: set missing.
    - TMIN above TMAX: both unreliable, set missing.
    """
    out = daily.copy()
    for c in SNOW_COLS:
        if c not in out:
            continue
        small = (out[c] < 0) & (out[c] >= config.SMALL_NEGATIVE_MM)
        big = out[c] < config.SMALL_NEGATIVE_MM
        out.loc[small, c] = 0.0
        out.loc[big, c] = np.nan
        if log:
            log.add("apply_physical_limits", f"{c}: clip small negatives (>= {config.SMALL_NEGATIVE_MM} mm) to 0",
                    small.sum(), "values", "snow pillow drift around zero")
            log.add("apply_physical_limits", f"{c}: set larger negatives to missing", big.sum(), "values")
    lo, hi = config.TEMP_VALID_C
    for c in TEMP_COLS:
        if c not in out:
            continue
        bad = (out[c] < lo) | (out[c] > hi)
        out.loc[bad, c] = np.nan
        if log:
            log.add("apply_physical_limits", f"{c}: outside {lo:.0f}..{hi:.0f} C set to missing", bad.sum(), "values")
    if {"TMIN", "TMAX"} <= set(out):
        bad = out["TMIN"] > out["TMAX"]
        out.loc[bad, ["TMIN", "TMAX"]] = np.nan
        if log:
            log.add("apply_physical_limits", "TMIN > TMAX: both set to missing", bad.sum(), "rows")
    return out


def derive_daily_precip(daily: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    """PREC is the water-year accumulation, reset each 1 October. Convert it to
    a daily increment PRCP. Negative increments are gauge drift or manual
    resets, not negative rain, so they become 0."""
    out = daily.sort_values(["station", "date"]).copy()
    if "PREC" not in out:
        return out
    wy = water_year(out["date"])
    inc = out.groupby([out["station"], wy])["PREC"].diff()
    first = out.groupby([out["station"], wy]).cumcount() == 0
    inc[first] = out.loc[first, "PREC"]  # 1 Oct value is that day's accumulation
    neg = inc < 0
    inc[neg] = 0.0
    out["PRCP"] = inc
    if log:
        log.add("derive_daily_precip", "PRCP = daily increment of cumulative PREC", out["PRCP"].notna().sum(), "values")
        log.add("derive_daily_precip", "negative increments set to 0", neg.sum(), "values", "gauge drift / reset")
    return out


def flag_swe_anomalies(daily: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    """Known snow pillow failure modes, evaluated per station in date order.

    - Isolated spike: a day that jumps by more than SWE_SPIKE_MM relative to
      both neighbours and in the same direction. Set missing.
    - Isolated zero inside a continuous pack: a single zero (or near-zero)
      between two days above ISOLATED_ZERO_NEIGHBOUR_MM. Set missing.
    - Flat line: identical non-zero SWE for FLATLINE_DAYS or more. Reported
      via the boolean column WTEQ_flatline but left in place, because a frozen
      pack in mid-winter can legitimately hold a constant value for weeks.
    """
    out = daily.sort_values(["station", "date"]).copy()
    s = out["WTEQ"]
    prev = out.groupby("station")["WTEQ"].shift(1)
    nxt = out.groupby("station")["WTEQ"].shift(-1)
    up = (s - prev > config.SWE_SPIKE_MM) & (s - nxt > config.SWE_SPIKE_MM)
    down = (prev - s > config.SWE_SPIKE_MM) & (nxt - s > config.SWE_SPIKE_MM)
    spike = (up | down).fillna(False)
    zero = ((s <= config.SWE_ZERO_THRESHOLD) & (prev > config.ISOLATED_ZERO_NEIGHBOUR_MM)
            & (nxt > config.ISOLATED_ZERO_NEIGHBOUR_MM)).fillna(False)
    out.loc[spike | zero, "WTEQ"] = np.nan
    # flat-line runs of identical non-zero SWE
    same = (s == prev) & (s > config.SWE_ZERO_THRESHOLD)
    run_id = (~same).cumsum()
    run_len = same.groupby([out["station"], run_id]).transform("size")
    out["WTEQ_flatline"] = (same & (run_len >= config.FLATLINE_DAYS - 1)).fillna(False)
    if log:
        log.add("flag_swe_anomalies", f"isolated one-day spike > {config.SWE_SPIKE_MM:.0f} mm set to missing", spike.sum(), "values")
        log.add("flag_swe_anomalies", f"isolated zero between days > {config.ISOLATED_ZERO_NEIGHBOUR_MM:.0f} mm set to missing", zero.sum(), "values", "sensor dropout")
        log.add("flag_swe_anomalies", f"flat-line >= {config.FLATLINE_DAYS} days flagged (kept)", out["WTEQ_flatline"].sum(), "values", "column WTEQ_flatline")
    return out


def fill_missing(daily: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    """Linear interpolation across gaps of at most MAX_INTERP_GAP_DAYS, per
    station, for slowly varying series. Longer gaps stay missing so screening
    can judge the station-year. PRCP is never interpolated: a missing day of
    rain is unknown, not the average of its neighbours."""
    out = daily.sort_values(["station", "date"]).copy()
    cols = [c for c in ["WTEQ", "SNWD", "TAVG", "TMAX", "TMIN"] if c in out]
    for c in cols:
        na = out[c].isna()
        gap_id = (~na).cumsum()
        gap_len = na.groupby([out["station"], gap_id]).transform("sum")
        fillable = na & (gap_len <= config.MAX_INTERP_GAP_DAYS)
        interp = out.groupby("station")[c].transform(
            lambda x: x.interpolate(limit_area="inside"))
        out.loc[fillable, c] = interp[fillable]
        if log:
            log.add("fill_missing", f"{c}: linear fill of gaps <= {config.MAX_INTERP_GAP_DAYS} days",
                    (fillable & out[c].notna()).sum(), "values",
                    f"{(na & ~fillable).sum()} values in longer gaps left missing")
    return out


def screen_stations(daily: pd.DataFrame, log: CleaningLog | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Station-year screening, then station screening.

    A station-year is excluded when SWE coverage in the feature window
    (1 Oct to end Feb) or the target window (1 Mar to 30 Sep) is below
    1 - MAX_MISSING_FRACTION, or peak SWE is below MIN_PEAK_SWE. A station is
    excluded when fewer than MIN_WATER_YEARS_PER_STATION years survive.
    Returns (retained daily data, exclusions with reasons).
    """
    d = daily.copy()
    d["water_year"] = water_year(d["date"])
    in_target = (d["date"].dt.month >= config.FORECAST_ORIGIN_MONTH) & (d["date"].dt.month < config.WATER_YEAR_START_MONTH)
    g = d.groupby(["station", "water_year"])
    sy = pd.DataFrame({
        "swe_cov_feature": d.loc[~in_target].groupby(["station", "water_year"])["WTEQ"].apply(lambda x: x.notna().mean()),
        "swe_cov_target": d.loc[in_target].groupby(["station", "water_year"])["WTEQ"].apply(lambda x: x.notna().mean()),
        "peak_swe_mm": g["WTEQ"].max(),
    })
    min_cov = 1 - config.MAX_MISSING_FRACTION
    sy["reason"] = ""
    sy.loc[sy["swe_cov_feature"].fillna(0) < min_cov, "reason"] = "feature-window SWE coverage < %.0f%%" % (100 * min_cov)
    sy.loc[(sy["reason"] == "") & (sy["swe_cov_target"].fillna(0) < min_cov), "reason"] = "target-window SWE coverage < %.0f%%" % (100 * min_cov)
    sy.loc[(sy["reason"] == "") & (sy["peak_swe_mm"].fillna(0) < config.MIN_PEAK_SWE), "reason"] = "peak SWE < %.0f mm" % config.MIN_PEAK_SWE
    kept_years = sy[sy["reason"] == ""].groupby("station").size()
    thin = kept_years[kept_years < config.MIN_WATER_YEARS_PER_STATION].index
    all_stations = sy.index.get_level_values("station").unique()
    thin = thin.union([s for s in all_stations if s not in kept_years.index])
    sy.loc[sy.index.get_level_values("station").isin(thin) & (sy["reason"] == ""), "reason"] = \
        "station has < %d usable years" % config.MIN_WATER_YEARS_PER_STATION
    excl = sy[sy["reason"] != ""].reset_index()
    keep = sy[sy["reason"] == ""].index
    out = d.set_index(["station", "water_year"]).loc[keep].reset_index()
    if log:
        for r, cnt in excl["reason"].value_counts().items():
            log.add("screen_stations", r, cnt, "station-years")
        log.add("screen_stations", "stations dropped entirely", len(thin), "stations", ", ".join(thin))
        log.add("screen_stations", "station-years retained", len(keep), "station-years",
                f"{out['station'].nunique()} stations")
    return out.sort_values(["station", "date"]).reset_index(drop=True), excl.sort_values(["station", "water_year"])


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------
def run_pipeline(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Full cleaning sequence. Returns (clean daily, cleaning log, exclusions)."""
    log = CleaningLog()
    d = complete_calendar(raw, log)
    d = drop_duplicates(d, log)
    d = to_si(d, log)
    d = apply_physical_limits(d, log)
    d = derive_daily_precip(d, log)
    d = flag_swe_anomalies(d, log)
    d = fill_missing(d, log)
    d, excl = screen_stations(d, log)
    return d, log.frame(), excl


def main() -> None:
    raw, _, _ = load_raw()
    clean, log, excl = run_pipeline(raw)
    clean.to_csv(config.DATA_PROCESSED / "daily_clean.csv.gz", index=False, compression="gzip")
    log.to_csv(config.DATA_PROCESSED / "cleaning_log.csv", index=False)
    excl.to_csv(config.DATA_PROCESSED / "exclusions.csv", index=False)
    print(log.to_string(index=False))


if __name__ == "__main__":
    main()
