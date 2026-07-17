"""Train candidate models, quick-tune the winner, and save the final pipeline.

Usage:
    python -m src.airline_delay.train
"""

import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import sklearn
from joblib import dump
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import RandomizedSearchCV, train_test_split

from . import config, data, features, reporting

SEARCH_SAMPLE_SIZE = 100_000
SEARCH_N_ITER = 20
SEARCH_CV = 3

PARAM_DISTRIBUTIONS = {
    "LogisticRegression": {
        "classifier__C": [0.01, 0.1, 1, 10, 100],
    },
    "RandomForestClassifier": {
        "classifier__n_estimators": [100, 200, 300, 400],
        "classifier__max_depth": [None, 10, 20, 30],
        "classifier__min_samples_leaf": [1, 2, 5, 10],
        "classifier__max_features": ["sqrt", "log2", 0.5],
    },
    "HistGradientBoostingClassifier": {
        "classifier__learning_rate": [0.01, 0.03, 0.05, 0.1, 0.2],
        "classifier__max_iter": [100, 150, 200, 300],
        "classifier__max_leaf_nodes": [15, 31, 63, 127],
        "classifier__min_samples_leaf": [10, 20, 50, 100],
        "classifier__l2_regularization": [0, 0.1, 1, 10],
    },
}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def build_candidates():
    baseline_preprocessor = features.build_baseline_preprocessor()
    tree_preprocessor, categorical_mask = features.build_tree_preprocessor()

    candidates = {
        "LogisticRegression": features.make_pipeline(
            baseline_preprocessor,
            LogisticRegression(max_iter=1000, random_state=config.RANDOM_SEED),
        ),
        "RandomForestClassifier": features.make_pipeline(
            tree_preprocessor,
            RandomForestClassifier(
                n_estimators=200,
                random_state=config.RANDOM_SEED,
                n_jobs=-1,
            ),
        ),
        "HistGradientBoostingClassifier": features.make_pipeline(
            tree_preprocessor,
            HistGradientBoostingClassifier(
                categorical_features=categorical_mask,
                random_state=config.RANDOM_SEED,
            ),
        ),
    }
    return candidates


def select_best_candidate(candidates, X_train, y_train, X_val, y_val):
    results = {}
    for name, pipeline in candidates.items():
        log(f"Fitting candidate '{name}' on train split...")
        pipeline.fit(X_train, y_train)
        y_proba = pipeline.predict_proba(X_val)[:, 1]
        y_pred = (y_proba >= 0.5).astype(int)
        roc_auc = roc_auc_score(y_val, y_proba)
        f1 = f1_score(y_val, y_pred)
        results[name] = {"roc_auc": roc_auc, "f1": f1}
        log(f"  {name}: val ROC-AUC={roc_auc:.4f}, val F1={f1:.4f}")

    best_name = max(results, key=lambda n: results[n]["roc_auc"])
    log(f"Selected best candidate: {best_name}")
    return best_name, results


def quick_tune(name, pipeline, X_train, y_train):
    param_distributions = PARAM_DISTRIBUTIONS[name]

    if len(X_train) > SEARCH_SAMPLE_SIZE:
        X_search, _, y_search, _ = train_test_split(
            X_train,
            y_train,
            train_size=SEARCH_SAMPLE_SIZE,
            stratify=y_train,
            random_state=config.RANDOM_SEED,
        )
    else:
        X_search, y_search = X_train, y_train

    log(
        f"Running quick RandomizedSearchCV for {name} "
        f"(n_iter={SEARCH_N_ITER}, cv={SEARCH_CV}, sample={len(X_search)})..."
    )
    search = RandomizedSearchCV(
        pipeline,
        param_distributions=param_distributions,
        n_iter=SEARCH_N_ITER,
        cv=SEARCH_CV,
        scoring="roc_auc",
        random_state=config.RANDOM_SEED,
        n_jobs=-1,
    )
    search.fit(X_search, y_search)
    log(f"Best params: {search.best_params_} (CV ROC-AUC={search.best_score_:.4f})")
    return search.best_params_


def main():
    # Headless script run: force a non-interactive backend. Done here (not
    # at module import time) so importing this module's functions elsewhere
    # -- e.g. the walkthrough notebook -- doesn't clobber an already-active
    # interactive/inline backend.
    import matplotlib

    matplotlib.use("Agg")

    log("Loading data...")
    df = data.load_data()
    train_df, val_df, test_df = data.split_data(df)
    log(
        f"Split sizes -> train: {len(train_df)}, val: {len(val_df)}, "
        f"test: {len(test_df)}"
    )

    X_train, y_train = data.get_X_y(train_df)
    X_val, y_val = data.get_X_y(val_df)
    X_test, y_test = data.get_X_y(test_df)

    candidates = build_candidates()
    best_name, selection_results = select_best_candidate(
        candidates, X_train, y_train, X_val, y_val
    )

    best_pipeline = candidates[best_name]
    best_params = quick_tune(best_name, best_pipeline, X_train, y_train)
    best_pipeline.set_params(**best_params)

    log("Refitting best pipeline on train+val...")
    X_trainval = pd.concat([X_train, X_val], ignore_index=True)
    y_trainval = pd.concat([y_train, y_val], ignore_index=True)
    best_pipeline.fit(X_trainval, y_trainval)

    log("Evaluating on held-out test set...")
    y_test_proba = best_pipeline.predict_proba(X_test)[:, 1]
    y_test_pred = (y_test_proba >= 0.5).astype(int)
    test_metrics = reporting.compute_metrics(y_test, y_test_pred, y_test_proba)
    log(f"Test metrics: {test_metrics}")

    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    reporting.plot_confusion_matrix(
        y_test, y_test_pred, config.FIGURES_DIR / "confusion_matrix.png"
    )
    reporting.plot_roc_curve(
        y_test, y_test_proba, config.FIGURES_DIR / "roc_curve.png"
    )
    feature_importance = reporting.plot_feature_importance(
        best_pipeline, X_test, y_test, config.FIGURES_DIR / "feature_importance.png"
    )

    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dump(best_pipeline, config.MODEL_PATH)
    log(f"Saved model to {config.MODEL_PATH}")

    raw_feature_schema = {
        "Time": "float (minutes since midnight, 0-1439)",
        "Length": "float (flight duration in minutes)",
        "Airline": "string (IATA carrier code)",
        "AirportFrom": "string (IATA airport code)",
        "AirportTo": "string (IATA airport code)",
        "DayOfWeek": "int (1=Monday .. 7=Sunday)",
    }
    assert set(raw_feature_schema) == set(config.RAW_FEATURE_COLUMNS), (
        "raw_feature_schema is out of sync with config.RAW_FEATURE_COLUMNS -- "
        "update both together."
    )

    metadata = {
        "model_name": best_name,
        "model_version": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "best_params": {k: str(v) for k, v in best_params.items()},
        "selection_results": selection_results,
        "test_metrics": test_metrics,
        "feature_importance": feature_importance,
        "class_labels": config.CLASS_LABELS,
        "raw_feature_schema": raw_feature_schema,
        "dataset_rows": len(df),
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "library_versions": {
            "scikit-learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
    }
    reporting.save_json(metadata, config.METADATA_PATH)
    reporting.save_json(
        {"selection_results": selection_results, "test_metrics": test_metrics},
        config.METRICS_PATH,
    )
    log(f"Saved metadata to {config.METADATA_PATH} and metrics to {config.METRICS_PATH}")


if __name__ == "__main__":
    sys.exit(main())
