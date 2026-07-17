import numpy as np

from src.airline_delay import config, data, features


def _sample_X_y(n=500):
    df = data.load_data()
    sample = df.sample(n=n, random_state=config.RANDOM_SEED)
    return data.get_X_y(sample)


def test_add_engineered_features_adds_expected_columns():
    X, _ = _sample_X_y()
    out = features.add_engineered_features(X)
    assert "IsWeekend" in out.columns
    assert "TimeOfDayBucket" in out.columns
    assert set(out["IsWeekend"].unique()).issubset({0, 1})
    assert set(out["TimeOfDayBucket"].unique()).issubset(
        set(features.TIME_BUCKET_LABELS)
    )


def test_baseline_preprocessor_transforms_without_nans():
    X, y = _sample_X_y()
    X_eng = features.add_engineered_features(X)
    preprocessor = features.build_baseline_preprocessor()
    transformed = preprocessor.fit_transform(X_eng, y)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    assert transformed.shape[0] == len(X_eng)
    assert not np.isnan(transformed).any()


def test_tree_preprocessor_transforms_without_nans():
    X, y = _sample_X_y()
    X_eng = features.add_engineered_features(X)
    preprocessor, categorical_mask = features.build_tree_preprocessor()
    transformed = preprocessor.fit_transform(X_eng, y)
    assert transformed.shape[0] == len(X_eng)
    assert not np.isnan(transformed).any()
    # AirportFrom/AirportTo are excluded from native-categorical handling
    # (HGB's 255-bin cap can't fit their 293 distinct values), so only the
    # low-cardinality columns are marked categorical.
    assert categorical_mask.sum() == len(config.LOW_CARD_CATEGORICAL_FEATURES)
