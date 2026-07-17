"""Central configuration: paths, seed, and split ratios."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_PATH = PROJECT_ROOT / "airlines_delay.csv"

MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "model.joblib"
METADATA_PATH = MODELS_DIR / "metadata.json"

REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
METRICS_PATH = REPORTS_DIR / "metrics.json"

RANDOM_SEED = 42

TARGET_COLUMN = "Class"

# Fractions of the *original* dataset. VAL_SIZE/TEST_SIZE are relative to the
# full dataset; TRAIN gets the remainder (~0.70).
VAL_SIZE = 0.15
TEST_SIZE = 0.15

EXPECTED_COLUMNS = [
    "Flight",
    "Time",
    "Length",
    "Airline",
    "AirportFrom",
    "AirportTo",
    "DayOfWeek",
    "Class",
]

NUMERIC_FEATURES = ["Time", "Length"]
LOW_CARD_CATEGORICAL_FEATURES = ["Airline", "DayOfWeek", "TimeOfDayBucket"]
HIGH_CARD_CATEGORICAL_FEATURES = ["AirportFrom", "AirportTo"]

# Raw columns the model actually consumes, i.e. EXPECTED_COLUMNS minus the
# target and minus "Flight" (excluded as a feature: it's just a flight
# number/ID with negligible predictive signal -- see permutation importance
# in reports/metrics.json). This is the single source of truth for what the
# API request schema and prediction helpers should accept.
RAW_FEATURE_COLUMNS = ["Time", "Length", "Airline", "AirportFrom", "AirportTo", "DayOfWeek"]

CLASS_LABELS = {0: "On-time", 1: "Delayed"}
