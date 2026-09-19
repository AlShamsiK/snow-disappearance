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
# Stations: all active SNOTEL stations in the 11 western states whose record
# starts on or before 1 October 1990 (548 candidates), stratified by state with
# up to six per state drawn with a fixed seed (random.Random(42)). See
# data_download.select_stations().
STATIONS: list[str] = [
    "308:AZ:SNTL", "310:AZ:SNTL", "488:AZ:SNTL", "511:AZ:SNTL",
    "866:AZ:SNTL", "877:AZ:SNTL", "391:CA:SNTL", "428:CA:SNTL",
    "446:CA:SNTL", "697:CA:SNTL", "784:CA:SNTL", "834:CA:SNTL",
    "335:CO:SNTL", "345:CO:SNTL", "412:CO:SNTL", "564:CO:SNTL",
    "580:CO:SNTL", "780:CO:SNTL", "320:ID:SNTL", "534:ID:SNTL",
    "546:ID:SNTL", "749:ID:SNTL", "770:ID:SNTL", "845:ID:SNTL",
    "307:MT:SNTL", "433:MT:SNTL", "576:MT:SNTL", "646:MT:SNTL",
    "700:MT:SNTL", "918:MT:SNTL", "394:NM:SNTL", "486:NM:SNTL",
    "491:NM:SNTL", "532:NM:SNTL", "595:NM:SNTL", "715:NM:SNTL",
    "337:NV:SNTL", "445:NV:SNTL", "476:NV:SNTL", "498:NV:SNTL",
    "573:NV:SNTL", "750:NV:SNTL", "344:OR:SNTL", "388:OR:SNTL",
    "422:OR:SNTL", "619:OR:SNTL", "712:OR:SNTL", "759:OR:SNTL",
    "348:UT:SNTL", "368:UT:SNTL", "474:UT:SNTL", "514:UT:SNTL",
    "596:UT:SNTL", "864:UT:SNTL", "478:WA:SNTL", "502:WA:SNTL",
    "515:WA:SNTL", "648:WA:SNTL", "692:WA:SNTL", "734:WA:SNTL",
    "468:WY:SNTL", "512:WY:SNTL", "716:WY:SNTL", "730:WY:SNTL",
    "731:WY:SNTL", "807:WY:SNTL",
]
WATER_YEAR_START = 1991           # first water year to include
WATER_YEAR_END = 2025             # last water year to include, inclusive
STATIONS_PER_STATE = 6
STATION_SELECTION_SEED = 42
WESTERN_STATES = ["AZ", "CA", "CO", "ID", "MT", "NM", "NV", "OR", "UT", "WA", "WY"]

# NRCS element codes. Raw units are inches (WTEQ, SNWD, PREC) and degrees
# Fahrenheit (TAVG, TMAX, TMIN); cleaning converts to mm and degrees Celsius.
ELEMENTS: list[str] = ["WTEQ", "SNWD", "PREC", "TAVG", "TMAX", "TMIN"]
RAW_DAILY_FILE = "snotel_daily.csv.gz"
RAW_STATIONS_FILE = "stations.csv"
RAW_ELEMENTS_FILE = "station_elements.csv"

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
# A day counts as snow-free when SWE is at or below this threshold (mm). A small
# positive threshold absorbs snow pillow sensor noise around zero; 2.5 mm is
# about 0.1 inch, the reporting precision of the sensor.
SWE_ZERO_THRESHOLD = 2.5

# Disappearance is "sustained" when the first snow-free day is followed by at
# least this many consecutive snow-free days. Vary this in the ablation.
SUSTAIN_DAYS = 14

# Latest date in the water year at which a disappearance can be recorded before
# the station-year is treated as not melting out.
MELT_OUT_SEARCH_END_MONTH = 9
MELT_OUT_SEARCH_END_DAY = 30

# --------------------------------------------------------------------------
# Station screening
# --------------------------------------------------------------------------
# A station-year is usable when SWE coverage in both the feature window
# (1 Oct to end of Feb) and the target window (1 Mar to 30 Sep) is at least
# 1 - MAX_MISSING_FRACTION after short-gap interpolation, and the snowpack
# actually built up (peak SWE >= MIN_PEAK_SWE mm). A station is kept when it
# retains at least MIN_WATER_YEARS_PER_STATION usable years.
MIN_WATER_YEARS_PER_STATION = 20
MAX_MISSING_FRACTION = 0.10
MIN_PEAK_SWE = 50.0               # mm; drop station-years with negligible snowpack

# --------------------------------------------------------------------------
# Cleaning rules (see clean.py; every rule reports how many values it touched)
# --------------------------------------------------------------------------
IN_TO_MM = 25.4
SMALL_NEGATIVE_MM = -5.0          # SWE/depth between this and 0 is pillow drift: clip to 0
TEMP_VALID_C = (-50.0, 50.0)      # daily temperatures outside this are sensor faults
SWE_SPIKE_MM = 50.0               # one-day up-and-back excursion larger than this is a spike
ISOLATED_ZERO_NEIGHBOUR_MM = 25.0 # a single zero between two days above this is a dropout
FLATLINE_DAYS = 20                # identical non-zero SWE for this many days is suspicious
MAX_INTERP_GAP_DAYS = 5           # linear interpolation only across gaps up to this length

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
