# Predicting Sustained Snow Disappearance from a March 1 Forecast Origin

CODS-622 Machine Learning, course project.
Author: Khalifa (Student ID 100068062), Khalifa University.
Submission deadline: 10 November 2026.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AlShamsiK/snow-disappearance/blob/main/notebooks/snow_disappearance.ipynb)


---

## Research question

Given only observations available on 1 March of a water year, how accurately can the
date of sustained snow disappearance at a SNOTEL station be predicted, and does a
machine learning model improve on station climatology and on a physically motivated
degree-day melt model?

**Forecast origin:** 1 March. No observation dated after 28/29 February of the target
water year may enter the feature set. This is the central leakage constraint of the
project and every feature is checked against it.

**Target:** the date of sustained snow disappearance (see `src/target.py`). Definition
is parameterised so that sensitivity to the definition can be reported as an ablation.

## Data

Source: USDA NRCS National Water and Climate Center, SNOTEL / SCAN network.
Portal: https://www.nrcs.usda.gov/resources/data-and-reports/snow-and-climate-monitoring-predefined-reports-and-maps

Raw daily station records are downloaded once and committed to `data/raw/`. The
notebook never calls the NRCS service at run time, so results are reproducible and
the live demo does not depend on network availability.

- Download date: `TBD`
- Stations: `TBD` (see `src/config.py`)
- Water years: `TBD`
- Elements: `TBD`

## Repository structure

```
snow-disappearance/
├── notebooks/
│   └── snow_disappearance.ipynb   main notebook, runs end to end
├── src/
│   ├── config.py                  paths, station list, water years, constants
│   ├── data_download.py           one-off NRCS pull, writes data/raw/
│   ├── clean.py                   QC, missingness handling, station screening
│   ├── target.py                  sustained snow disappearance date
│   ├── features.py                March 1 feature construction
│   ├── models.py                  baselines and ML models
│   └── evaluate.py                splits, metrics, skill scores
├── data/
│   ├── raw/                       as downloaded from NRCS, never edited
│   └── processed/                 one row per station-water-year
├── models/                        fitted model artefacts
└── reports/                       figures and tables for the write-up
```

## Running it

In Colab, the first cell of the notebook clones this repo and installs dependencies.
Locally:

```bash
git clone https://github.com/USERNAME/snow-disappearance.git
cd snow-disappearance
pip install -r requirements.txt
jupyter notebook notebooks/snow_disappearance.ipynb
```

To rebuild the processed dataset from the committed raw files:

```bash
python -m src.clean
python -m src.target
python -m src.features
```

Re-downloading the raw data is only needed to extend the record:

```bash
python -m src.data_download
```

## Reproducibility

- `requirements.txt` pins versions.
- `RANDOM_SEED` in `src/config.py` is used everywhere a seed is needed.
- Raw data is committed, so the pipeline is deterministic from a clean clone.
- The fitted model in `models/` is committed, so the demo cell loads rather than trains.
- Python version used: `TBD`

## Demo

The final notebook section takes a station and a water year, shows the features as
they stood on 1 March, produces a predicted disappearance date with a prediction
interval, and compares it to the observed date.
