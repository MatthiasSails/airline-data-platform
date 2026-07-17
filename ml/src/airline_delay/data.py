"""Loading and splitting the raw airline delay dataset."""

import pandas as pd
from sklearn.model_selection import train_test_split

from . import config


def load_data(path=None) -> pd.DataFrame:
    """Load the raw CSV, validating schema and completeness."""
    df = pd.read_csv(path or config.RAW_DATA_PATH)

    missing_cols = set(config.EXPECTED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Dataset is missing expected columns: {missing_cols}")

    if df.isna().any().any():
        raise ValueError("Dataset contains unexpected null values.")

    return df


def split_data(df: pd.DataFrame, seed: int = config.RANDOM_SEED):
    """Stratified train/val/test split on the target column.

    No temporal column exists in this dataset, so a random stratified split
    is the appropriate choice (rather than a time-based split).
    """
    train_val, test = train_test_split(
        df,
        test_size=config.TEST_SIZE,
        stratify=df[config.TARGET_COLUMN],
        random_state=seed,
    )

    relative_val_size = config.VAL_SIZE / (1 - config.TEST_SIZE)
    train, val = train_test_split(
        train_val,
        test_size=relative_val_size,
        stratify=train_val[config.TARGET_COLUMN],
        random_state=seed,
    )

    return (
        train.reset_index(drop=True),
        val.reset_index(drop=True),
        test.reset_index(drop=True),
    )


def get_X_y(df: pd.DataFrame):
    X = df.drop(columns=[config.TARGET_COLUMN])
    y = df[config.TARGET_COLUMN]
    return X, y
