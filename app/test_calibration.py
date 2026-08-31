"""Fast integration checks for the public calibration application."""

from pathlib import Path

import numpy as np
import pandas as pd

from utils.feature_engineering import ERA5_COLUMNS, FeatureEngineer
from utils.model_predictor import TemperatureCalibrator


APP_DIR = Path(__file__).resolve().parent


def sample_frame():
    frame = pd.read_csv(APP_DIR / "sample_data.csv")
    frame["temperature"] = (frame["temperature"] - 32) * 5 / 9
    return frame


def test_sensor_only_pipeline():
    source = sample_frame()
    features = FeatureEngineer().engineer_all_features(source)
    result = TemperatureCalibrator().calibrate(features, mode="accessible")
    assert len(result) == len(source)
    assert np.isfinite(result["calibrated_temperature_c"]).all()
    assert (result["_history_hours"].iloc[:6] == np.arange(6)).all()
    assert result["model_used"].iloc[5] == "Sensor-only instant (warm-up)"
    assert result["model_used"].iloc[6] == "Sensor-only temporal"


def test_paper_model_pipeline():
    source = sample_frame()
    source["sshf"] = np.linspace(-100_000, 100_000, len(source))
    source["ssrd"] = np.linspace(0, 2_000_000, len(source))
    source["strd"] = 1_000_000
    source["tp"] = 0.0
    source["u10"] = 2.0
    source["v10"] = 1.0
    features = FeatureEngineer().engineer_all_features(source)
    result = TemperatureCalibrator().calibrate(features, mode="paper")
    assert np.isfinite(result["calibrated_temperature_c"]).all()
    assert set(result["model_used"]) == {"Temporal-National (paper model)"}


def test_sensor_history_is_isolated():
    first = sample_frame().iloc[:4].copy()
    first["sensor_id"] = "A"
    second = first.copy()
    second["sensor_id"] = "B"
    second["temperature"] += 10
    features = FeatureEngineer().engineer_all_features(pd.concat([first, second], ignore_index=True))
    first_b = features.index[features["_sensor_key"] == "B"][0]
    assert np.isnan(features.loc[first_b, "sensor_temp_1h_ago"])
    assert features.loc[first_b, "_history_hours"] == 0


if __name__ == "__main__":
    test_sensor_only_pipeline()
    test_paper_model_pipeline()
    test_sensor_history_is_isolated()
    print("All calibration integration checks passed.")
