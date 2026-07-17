"""Shared evaluation metrics and plotting helpers used by train.py and evaluate.py.

Does not force a matplotlib backend: script entry points (train.py,
evaluate.py) set a headless "Agg" backend themselves before importing this
module, while interactive contexts (the walkthrough notebook) keep their own
inline backend so plots render live.
"""

import json

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from . import config

PERMUTATION_IMPORTANCE_SAMPLE_SIZE = 20_000


def compute_metrics(y_true, y_pred, y_proba) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred)),
        "recall": float(recall_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "pr_auc": float(average_precision_score(y_true, y_proba)),
    }


def plot_confusion_matrix(y_true, y_pred, out_path):
    fig, ax = plt.subplots(figsize=(5, 5))
    cm = confusion_matrix(y_true, y_pred)
    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=[config.CLASS_LABELS[0], config.CLASS_LABELS[1]],
    )
    display.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Confusion Matrix (Test Set)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_roc_curve(y_true, y_proba, out_path):
    fig, ax = plt.subplots(figsize=(5, 5))
    RocCurveDisplay.from_predictions(y_true, y_proba, ax=ax)
    ax.set_title("ROC Curve (Test Set)")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_feature_importance(pipeline, X, y, out_path, seed=config.RANDOM_SEED):
    """Permutation importance computed on raw (pre-engineering) feature columns."""
    if len(X) > PERMUTATION_IMPORTANCE_SAMPLE_SIZE:
        X_sample = X.sample(
            n=PERMUTATION_IMPORTANCE_SAMPLE_SIZE, random_state=seed
        )
        y_sample = y.loc[X_sample.index]
    else:
        X_sample, y_sample = X, y

    result = permutation_importance(
        pipeline,
        X_sample,
        y_sample,
        n_repeats=5,
        random_state=seed,
        scoring="roc_auc",
        n_jobs=-1,
    )

    importances = (
        pd.Series(result.importances_mean, index=X_sample.columns)
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(7, 5))
    importances.plot.barh(ax=ax, color="#4C72B0")
    ax.set_xlabel("Mean ROC-AUC decrease when permuted")
    ax.set_title("Permutation Feature Importance (Test Sample)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    return importances.sort_values(ascending=False).to_dict()


def save_json(obj: dict, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)
