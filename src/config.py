"""Central configuration.

Every tunable lives here so that ablations change one value in one place and the
notebook can print the full configuration for reproducibility.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"

for _p in (DATA_RAW, DATA_PROCESSED, MODELS, REPORTS):
    _p.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------
RANDOM_SEED = 42

# --------------------------------------------------------------------------
# Data scope
# --------------------------------------------------------------------------
# Station identifiers, water year range and element codes are filled in once the
# NRCS download mechanics and station screening are settled.
STATIONS: list[str] = []          # e.g. ["301:CA:SNTL", ...]
WATER_YEAR_START = None           # first water year to include
WATER_YEAR_END = None             # last water year to include, inclusive
ELEMENTS: list[str] = []          # e.g. ["WTEQ", "SNWD", "PREC", "TAVG"]

# Water year convention: 1 October of year Y-1 through 30 September of year Y.
WATER_YEAR_START_MONTH = 10
WATER_YEAR_START_DAY = 1

# --------------------------------------------------------------------------
# Forecast origin
# --------------------------------------------------------------------------
# No observation dated on or after this date may be used as a feature.
FORECAST_ORIGIN_MONTH = 3
FORECAST_ORIGIN_DAY = 1

# --------------------------------------------------------------------------
# Target definition: sustained snow disappearance
# --------------------------------------------------------------------------
# A day counts as snow-free when SWE is at or below this threshold. A small
# positive threshold absorbs snow pillow sensor noise around zero.
SWE_ZERO_THRESHOLD = 0.0          # units follow the downloaded data

# Disappearance is "sustained" when the first snow-free day is followed by at
# least this many consecutive snow-free days. Vary this in the ablation.
SUSTAIN_DAYS = 0

# Latest date in the water year at which a disappearance can be recorded before
# the station-year is treated as not melting out.
MELT_OUT_SEARCH_END_MONTH = 9
MELT_OUT_SEARCH_END_DAY = 30

# --------------------------------------------------------------------------
# Station screening
# --------------------------------------------------------------------------
MIN_WATER_YEARS_PER_STATION = None
MAX_MISSING_FRACTION = None
MIN_PEAK_SWE = None               # drop station-years with negligible snowpack

# --------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------
# Water years held out as the final test set. Chosen as the most recent block so
# the split mimics operational forecasting: train on the past, predict forward.
TEST_WATER_YEARS: list[int] = []
N_CV_FOLDS = 5


def as_dict() -> dict:
    """Configuration snapshot, printed in the notebook for the record."""
    return {
        k: v
        for k, v in globals().items()
        if k.isupper() and not k.startswith("_")
    }
