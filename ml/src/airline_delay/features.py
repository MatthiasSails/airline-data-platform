"""Feature engineering and preprocessing pipelines.

Two preprocessing strategies are provided:
  - baseline: one-hot / target encoding, feeds a linear model (Logistic Regression).
  - tree: ordinal-encoded categoricals with native categorical support, feeds
    tree-based models (RandomForest / HistGradientBoosting).
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
    TargetEncoder,
)

from . import config

TIME_BUCKET_BINS = [-0.1, 359, 719, 1079, 1439]
TIME_BUCKET_LABELS = ["night", "morning", "afternoon", "evening"]

ENGINEERED_NUMERIC_FEATURES = config.NUMERIC_FEATURES + ["IsWeekend"]


def add_engineered_features(X: pd.DataFrame) -> pd.DataFrame:
    """Add IsWeekend and TimeOfDayBucket columns derived from raw features."""
    X = X.copy()
    X["IsWeekend"] = X["DayOfWeek"].isin([6, 7]).astype(int)
    X["TimeOfDayBucket"] = pd.cut(
        X["Time"], bins=TIME_BUCKET_BINS, labels=TIME_BUCKET_LABELS
    ).astype(str)
    return X


def make_feature_engineer() -> FunctionTransformer:
    return FunctionTransformer(add_engineered_features)


def build_baseline_preprocessor() -> ColumnTransformer:
    """One-hot + target encoding preprocessor for the linear baseline model."""
    return ColumnTransformer(
        transformers=[
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore"),
                config.LOW_CARD_CATEGORICAL_FEATURES,
            ),
            (
                "target",
                TargetEncoder(random_state=config.RANDOM_SEED),
                config.HIGH_CARD_CATEGORICAL_FEATURES,
            ),
            ("scale", StandardScaler(), ENGINEERED_NUMERIC_FEATURES),
        ]
    )


def build_tree_preprocessor():
    """Ordinal-encoded preprocessor for tree-based models.

    All categoricals are ordinal-encoded (avoids one-hot blow-up from the
    293-value AirportFrom/AirportTo columns). Returns the ColumnTransformer
    plus the boolean mask (over the transformed output columns) identifying
    which columns should be treated as *native* categorical by
    HistGradientBoostingClassifier(categorical_features=...).

    AirportFrom/AirportTo are excluded from that mask: HGB's native
    categorical handling caps cardinality at 255 bins, below their 293
    distinct values, so they are passed through as ordinal-encoded numeric
    instead (the same treatment RandomForest gives them).
    """
    categorical_cols = (
        config.LOW_CARD_CATEGORICAL_FEATURES + config.HIGH_CARD_CATEGORICAL_FEATURES
    )
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "ordinal",
                OrdinalEncoder(
                    handle_unknown="use_encoded_value", unknown_value=-1
                ),
                categorical_cols,
            ),
            ("passthrough", "passthrough", ENGINEERED_NUMERIC_FEATURES),
        ]
    )
    n_total = len(categorical_cols) + len(ENGINEERED_NUMERIC_FEATURES)
    categorical_mask = np.zeros(n_total, dtype=bool)
    categorical_mask[: len(config.LOW_CARD_CATEGORICAL_FEATURES)] = True
    return preprocessor, categorical_mask


def make_pipeline(preprocessor: ColumnTransformer, estimator) -> Pipeline:
    return Pipeline(
        steps=[
            ("feature_engineering", make_feature_engineer()),
            ("preprocessing", preprocessor),
            ("classifier", estimator),
        ]
    )
