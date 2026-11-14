"""Evaluate saved final models on a frozen, labeled test CSV.

Usage: python evaluate.py data/test.csv
Never use these results to tune the model or threshold.
"""

import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report, confusion_matrix, f1_score,
    precision_score, recall_score, average_precision_score, accuracy_score
)
from inference import load_models, predict_dataframe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("test_csv", help="Test CSV containing 'Label' and 'attack_cat'")
    args = parser.parse_args()

    models = load_models()
    y_binary, y_family, score, pred_binary, pred_family = [], [], [], [], []
    for chunk in pd.read_csv(args.test_csv, chunksize=10_000):
        if "Label" not in chunk.columns or "attack_cat" not in chunk.columns:
            raise ValueError("Test CSV must contain Label and attack_cat columns")
        results = predict_dataframe(chunk, models)
        y_binary.extend(chunk["Label"].astype(int).tolist())
        y_family.extend(chunk["attack_cat"].astype(str).tolist())
        score.extend(results["Tier1_Attack_Score"].tolist())
        pred_binary.extend((results["Tier1_Prediction"] == "Attack").astype(int).tolist())
        pred_family.extend(results["Predicted_Class"].tolist())

    if not y_binary:
        raise ValueError("Test CSV was empty")

    y_binary = np.asarray(y_binary)
    pred_binary = np.asarray(pred_binary)
    tn, fp, fn, tp = confusion_matrix(y_binary, pred_binary, labels=[0, 1]).ravel()
    print("TIER 1 — TEST")
    print(f"TN={tn}  FP={fp}  FN={fn}  TP={tp}")
    print(f"Precision={precision_score(y_binary, pred_binary, zero_division=0):.6f}")
    print(f"Recall={recall_score(y_binary, pred_binary, zero_division=0):.6f}")
    print(f"F1={f1_score(y_binary, pred_binary, zero_division=0):.6f}")
    print(f"FPR={fp / (fp + tn):.6f}")
    print(f"Average precision={average_precision_score(y_binary, score):.6f}")

    families = sorted(set(y_family) - {"Normal"})
    print("\nEND-TO-END — TEST")
    print(classification_report(
        y_family, pred_family, labels=["Normal"] + families,
        digits=4, zero_division=0
    ))
    print("Attack-family macro F1:", f1_score(
        y_family, pred_family, labels=families, average="macro", zero_division=0
    ))
    print("Overall accuracy:", accuracy_score(y_family, pred_family))


if __name__ == "__main__":
    main()
