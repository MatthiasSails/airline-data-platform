"""Regenerate metrics/plots for a saved model against a fresh test split.

Usage:
    python -m src.airline_delay.evaluate
"""

import sys

from joblib import load

from . import config, data, reporting


def main():
    # Headless script run: force a non-interactive backend. Done here (not
    # at module import time) so importing this module elsewhere doesn't
    # clobber an already-active interactive/inline backend.
    import matplotlib

    matplotlib.use("Agg")

    print(f"Loading model from {config.MODEL_PATH}...")
    pipeline = load(config.MODEL_PATH)

    print("Loading data and recreating the held-out test split...")
    df = data.load_data()
    _, _, test_df = data.split_data(df)
    X_test, y_test = data.get_X_y(test_df)

    y_proba = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    metrics = reporting.compute_metrics(y_test, y_pred, y_proba)
    print(f"Test metrics: {metrics}")

    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    reporting.plot_confusion_matrix(
        y_test, y_pred, config.FIGURES_DIR / "confusion_matrix.png"
    )
    reporting.plot_roc_curve(y_test, y_proba, config.FIGURES_DIR / "roc_curve.png")
    feature_importance = reporting.plot_feature_importance(
        pipeline, X_test, y_test, config.FIGURES_DIR / "feature_importance.png"
    )

    reporting.save_json(
        {"test_metrics": metrics, "feature_importance": feature_importance},
        config.METRICS_PATH,
    )
    print(f"Updated metrics saved to {config.METRICS_PATH}")


if __name__ == "__main__":
    sys.exit(main())
