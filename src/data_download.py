"""One-off download of SNOTEL daily records from the NRCS service.

Source portal:
https://www.nrcs.usda.gov/resources/data-and-reports/snow-and-climate-monitoring-predefined-reports-and-maps

This module is run manually, not from the notebook. Its output lands in
data/raw/ and is committed to the repository, so the notebook and the live
demo never touch the network. Re-run only to extend the period of record.

Record the download date in the README whenever this is run.
"""

from __future__ import annotations

from . import config


def fetch_station_inventory():
    """Station metadata: id, name, lat, lon, elevation, state, start of record."""
    raise NotImplementedError


def fetch_daily(station: str, elements: list[str], start: str, end: str):
    """Daily records for one station over a date range."""
    raise NotImplementedError


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
