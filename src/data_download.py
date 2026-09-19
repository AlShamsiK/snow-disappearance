"""One-off download of SNOTEL daily records from the NRCS AWDB REST service.

Source portal:
https://www.nrcs.usda.gov/resources/data-and-reports/snow-and-climate-monitoring-predefined-reports-and-maps
REST service:
https://wcc.sc.egov.usda.gov/awdbRestApi/

This module is run manually, not from the notebook. Its output lands in
data/raw/ and is committed to the repository, so the notebook and the live
demo never touch the network. Re-run only to extend the period of record.

Files written to data/raw/:
    stations.csv          metadata for the selected stations
    station_elements.csv  per-station element metadata (units, period of record)
    snotel_daily.csv.gz   one row per station-date, one column per element plus
                          the NRCS quality-control flag for each element
    DOWNLOAD.md           when and how the pull was made

Record the download date in the README whenever this is run.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import sys
import time
import urllib.parse
import urllib.request

import pandas as pd

from . import config

API = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"


def _get(path: str, **params) -> list | dict:
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def fetch_station_inventory() -> pd.DataFrame:
    """All SNOTEL stations: id, name, lat, lon, elevation, state, record dates."""
    rows = _get("stations", stationTriplets="*:*:SNTL")
    keep = [
        "stationTriplet", "stationId", "stateCode", "name", "countyName", "huc",
        "elevation", "latitude", "longitude", "dataTimeZone", "beginDate", "endDate",
    ]
    df = pd.DataFrame(rows)[keep].rename(columns={"stationTriplet": "station"})
    df["elevation_m"] = (df["elevation"] * 0.3048).round(1)  # NRCS reports feet
    return df


def select_stations(inventory: pd.DataFrame) -> list[str]:
    """Deterministic stratified sample: active western stations with a record
    starting on or before 1 Oct of the first water year, up to
    STATIONS_PER_STATE per state, drawn with a fixed seed."""
    first_oct = f"{config.WATER_YEAR_START - 1}-10-01 00:00"
    cand = inventory[
        inventory["stateCode"].isin(config.WESTERN_STATES)
        & (inventory["beginDate"] <= first_oct)
        & (inventory["endDate"] >= "2099")
    ]
    rng = random.Random(config.STATION_SELECTION_SEED)
    chosen: list[str] = []
    for state in sorted(cand["stateCode"].unique()):
        pool = sorted(cand.loc[cand["stateCode"] == state, "station"])
        chosen += rng.sample(pool, min(config.STATIONS_PER_STATE, len(pool)))
    return sorted(chosen, key=lambda t: (t.split(":")[1], t))


def fetch_daily(station: str, elements: list[str], start: str, end: str):
    """Daily records for one station over a date range.

    Returns (wide_frame, element_metadata). The service rejects large
    multi-station requests, so one station per call over the full range is the
    reliable shape (about 70k values per call).
    """
    payload = _get(
        "data",
        stationTriplets=station,
        elements=",".join(elements),
        duration="DAILY",
        beginDate=start,
        endDate=end,
        returnFlags="true",
    )
    frames, meta = [], []
    for block in payload[0]["data"] if payload else []:
        el = block["stationElement"]
        code = el["elementCode"]
        meta.append({
            "station": station, "element": code,
            "stored_unit": el.get("storedUnitCode"), "original_unit": el.get("originalUnitCode"),
            "begin_date": el.get("beginDate"), "end_date": el.get("endDate"),
        })
        v = pd.DataFrame(block["values"])
        if v.empty:
            continue
        v = v.rename(columns={"value": code, "qcFlag": f"{code}_flag"})
        frames.append(v.set_index("date")[[code, f"{code}_flag"]])
    if not frames:
        return pd.DataFrame(), pd.DataFrame(meta)
    wide = pd.concat(frames, axis=1).reset_index()
    wide.insert(0, "station", station)
    return wide, pd.DataFrame(meta)


def main() -> None:
    start = f"{config.WATER_YEAR_START - 1}-10-01"
    end = f"{config.WATER_YEAR_END}-09-30"
    inv = fetch_station_inventory()
    stations = config.STATIONS or select_stations(inv)
    meta = inv[inv["station"].isin(stations)].sort_values("station")
    meta.to_csv(config.DATA_RAW / config.RAW_STATIONS_FILE, index=False)

    daily, elems = [], []
    for i, s in enumerate(stations, 1):
        wide, em = fetch_daily(s, config.ELEMENTS, start, end)
        daily.append(wide)
        elems.append(em)
        print(f"[{i:>2}/{len(stations)}] {s}: {len(wide):,} days", flush=True)
    all_daily = pd.concat(daily, ignore_index=True)
    cols = ["station", "date"] + [c for e in config.ELEMENTS for c in (e, f"{e}_flag") if c in all_daily]
    all_daily = all_daily[cols].sort_values(["station", "date"])
    all_daily.to_csv(config.DATA_RAW / config.RAW_DAILY_FILE, index=False, compression="gzip")
    pd.concat(elems, ignore_index=True).to_csv(config.DATA_RAW / config.RAW_ELEMENTS_FILE, index=False)

    (config.DATA_RAW / "DOWNLOAD.md").write_text(
        f"# Raw data download record\n\n"
        f"- Downloaded: {dt.date.today().isoformat()}\n"
        f"- Service: {API}/data (duration=DAILY, returnFlags=true)\n"
        f"- Stations: {len(stations)} (see stations.csv; selection rule in data_download.select_stations)\n"
        f"- Date range: {start} to {end} (water years {config.WATER_YEAR_START}-{config.WATER_YEAR_END})\n"
        f"- Elements: {', '.join(config.ELEMENTS)}\n"
        f"- Rows: {len(all_daily):,}\n"
        f"- Raw units: inches for WTEQ/SNWD/PREC, degrees Fahrenheit for TAVG/TMAX/TMIN\n"
        f"- Files are as returned by the service; no values were edited.\n"
    )
    print("done:", config.DATA_RAW / config.RAW_DAILY_FILE, file=sys.stderr)


if __name__ == "__main__":
    main()
