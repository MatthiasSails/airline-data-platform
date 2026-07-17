"""Model loading and prediction helpers shared by the FastAPI service."""

import json

import pandas as pd
from joblib import load

from . import config

RAW_FEATURE_COLUMNS = config.RAW_FEATURE_COLUMNS


def load_model(path=None):
    return load(path or config.MODEL_PATH)


def load_metadata(path=None) -> dict:
    with open(path or config.METADATA_PATH) as f:
        return json.load(f)


def records_to_frame(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(records, columns=RAW_FEATURE_COLUMNS)


def predict(pipeline, records: list[dict]) -> list[dict]:
    X = records_to_frame(records)
    probabilities = pipeline.predict_proba(X)[:, 1]
    predictions = []
    for proba in probabilities:
        predicted_class = int(proba >= 0.5)
        predictions.append(
            {
                "predicted_class": predicted_class,
                "predicted_label": config.CLASS_LABELS[predicted_class],
                "probability_delayed": float(proba),
            }
        )
    return predictions
