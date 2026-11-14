"""Train deployment-friendly models and export the final paper model.

This script is provided for reproducibility. It expects the engineered training
table used by the manuscript and the fitted Temporal-National XGBoost pickle.
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from utils.model_predictor import INSTANT_FEATURES, SENSOR_TEMPORAL_FEATURES


MODEL_PARAMETERS = {
    "objective": "reg:squarederror",
    "colsample_bytree": 0.8354380299230508,
    "gamma": 4.499581762807693,
    "learning_rate": 0.07359432865677237,
    "max_depth": 12,
    "min_child_weight": 5,
    "n_estimators": 400,
    "n_jobs": -1,
    "random_state": 42,
    "reg_alpha": 0.017607113202194175,
    "reg_lambda": 0.0024769724107909412,
    "subsample": 0.7103953442753852,
    "tree_method": "hist",
}


def fit_and_score(train, test, features, output_path):
    model = XGBRegressor(**MODEL_PARAMETERS)
    model.fit(
        train[features],
        train["station temperature"],
        sample_weight=train["Wsample"],
        verbose=False,
    )
    predictions = model.predict(test[features])
    model.save_model(output_path)
    return {
        "features": len(features),
        "test_mae_c": round(float(mean_absolute_error(test["station temperature"], predictions)), 3),
        "test_rmse_c": round(float(np.sqrt(mean_squared_error(test["station temperature"], predictions))), 3),
        "test_r2": round(float(r2_score(test["station temperature"], predictions)), 4),
        "n_train": int(len(train)),
        "n_test": int(len(test)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--paper-model", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("models"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    usecols = sorted(
        set(INSTANT_FEATURES + SENSOR_TEMPORAL_FEATURES + ["station temperature", "Wsample"])
    )
    print(f"Reading {args.data} ...", flush=True)
    data = pd.read_csv(args.data, usecols=usecols)
    train, test = train_test_split(data, test_size=0.2, random_state=42)

    print("Training sensor-only instant model ...", flush=True)
    instant = fit_and_score(
        train, test, INSTANT_FEATURES, args.output / "sensor_only_instant_xgboost.ubj"
    )
    print(instant, flush=True)

    print("Training sensor-only temporal model ...", flush=True)
    temporal = fit_and_score(
        train,
        test,
        SENSOR_TEMPORAL_FEATURES,
        args.output / "sensor_only_temporal_xgboost.ubj",
    )
    print(temporal, flush=True)

    print("Exporting manuscript Temporal-National model ...", flush=True)
    with args.paper_model.open("rb") as handle:
        paper_model = pickle.load(handle)
    paper_model.save_model(args.output / "paper_temporal_national_xgboost.ubj")

    metadata = {
        "paper": {
            "label": "Temporal-National (paper model)",
            "features": 63,
            "test_mae_c": 0.78,
            "test_rmse_c": 1.089,
            "test_r2": 0.9874,
            "note": (
                "Temporal-National configuration as released in v2.0.0, measured on the "
                "held-out 20% of the 797,744 observations (random_state=42); complete ERA5 "
                "inputs required. The manuscript reports a model of this configuration refit "
                "under the revised evaluation protocol."
            ),
        },
        "sensor_temporal": {
            "label": "Sensor-only temporal",
            **temporal,
            "note": "Deployment model trained for the web app; six prior hourly records recommended.",
        },
        "instant": {
            "label": "Sensor-only instant",
            **instant,
            "note": "Warm-up model for isolated readings or the first six hours of a sequence.",
        },
        "training_dataset": {
            "observations": int(len(data)),
            "validation": "Fixed 80/20 random observation-level split (random_state=42)",
        },
    }
    (args.output / "model_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == "__main__":
    main()
