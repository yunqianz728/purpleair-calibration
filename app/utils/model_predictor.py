"""Model loading and prediction for the public calibration app."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRegressor


MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

INSTANT_FEATURES = [
    "day", "elevation_sensor", "humidity", "life", "sensor_lat", "sensor_lon",
    "sensor_tcc", "sensor temperature", "year", "humidity_squared",
    "temp_squared_sensor", "temp_humidity_product_sensor",
    "temp_life_interaction_sensor", "dewpoint_sensor",
    "dewpoint_depression_sensor", "vapor_pressure_deficit_sensor", "hour_sin",
    "hour_cos", "month_sin", "month_cos", "polar_day_night", "day_of_month",
    "is_hot", "is_cold",
]

SENSOR_TEMPORAL_FEATURES = INSTANT_FEATURES + [
    "sensor_temp_1h_ago", "sensor_temp_2h_ago", "sensor_temp_3h_ago",
    "sensor_temp_4h_ago", "sensor_temp_5h_ago", "sensor_temp_6h_ago",
    "humidity_1h_ago", "humidity_2h_ago", "humidity_3h_ago",
    "temp_change_1h", "temp_change_2h", "temp_change_3h", "temp_acceleration",
    "temp_ma_3h", "temp_ma_6h", "temp_ma_12h", "temp_std_3h",
    "temp_std_6h", "temp_std_12h", "temp_range_3h", "temp_range_6h",
    "temp_trend_3h", "temp_trend_6h", "hot_streak", "cold_streak",
]

PAPER_FEATURES = [
    "day", "elevation_sensor", "humidity", "life", "sensor_lat", "sensor_lon",
    "sensor_tcc", "sensor temperature", "year", "sshf", "ssrd", "strd", "tp",
    "humidity_squared", "temp_squared_sensor", "temp_humidity_product_sensor",
    "temp_life_interaction_sensor", "dewpoint_sensor",
    "dewpoint_depression_sensor", "vapor_pressure_deficit_sensor", "hour_sin",
    "hour_cos", "month_sin", "month_cos", "diurnal_radiation",
    "polar_day_night", "day_of_month", "sensor_temp_1h_ago",
    "sensor_temp_2h_ago", "sensor_temp_3h_ago", "sensor_temp_4h_ago",
    "sensor_temp_5h_ago", "sensor_temp_6h_ago", "humidity_1h_ago",
    "humidity_2h_ago", "humidity_3h_ago", "ssrd_1h_ago", "ssrd_2h_ago",
    "temp_change_1h", "temp_change_2h", "temp_change_3h", "temp_acceleration",
    "temp_ma_3h", "temp_ma_6h", "temp_ma_12h", "temp_std_3h",
    "temp_std_6h", "temp_std_12h", "temp_range_3h", "temp_range_6h",
    "temp_trend_3h", "temp_trend_6h", "ssrd_sum_3h", "ssrd_sum_6h",
    "ssrd_change", "hot_streak", "cold_streak", "u10", "v10",
    "wind_speed", "wind_direction", "is_hot", "is_cold",
]

MODEL_FILES = {
    "instant": "sensor_only_instant_xgboost.ubj",
    "sensor_temporal": "sensor_only_temporal_xgboost.ubj",
    "paper": "paper_temporal_national_xgboost.ubj",
}


class TemperatureCalibrator:
    """Apply the paper model or the accessible sensor-only deployment models."""

    def __init__(self, model_dir: Path = MODEL_DIR):
        self.model_dir = Path(model_dir)
        self.models = {name: self._load_model(filename) for name, filename in MODEL_FILES.items()}
        metadata_path = self.model_dir / "model_metadata.json"
        self.metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}

    def _load_model(self, filename: str) -> XGBRegressor:
        path = self.model_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required model is missing: {path.name}")
        model = XGBRegressor()
        model.load_model(path)
        return model

    @staticmethod
    def _predict(model: XGBRegressor, features: pd.DataFrame, columns: list[str]) -> np.ndarray:
        return model.predict(features[columns])

    def calibrate(self, features: pd.DataFrame, mode: str = "accessible") -> pd.DataFrame:
        """Add calibrated temperature, correction, model, and history status."""
        result = features.copy()
        full_history = result["_history_hours"] >= 6

        if mode == "paper":
            required_weather = ["sshf", "ssrd", "strd", "tp", "u10", "v10"]
            missing = [name for name in required_weather if result[name].isna().any()]
            if missing:
                raise ValueError(
                    "Paper model requires complete ERA5 columns: " + ", ".join(missing)
                )
            predictions = self._predict(self.models["paper"], result, PAPER_FEATURES)
            model_used = np.repeat("Temporal-National (paper model)", len(result)).astype(object)
        elif mode == "accessible":
            predictions = np.empty(len(result), dtype=float)
            predictions[~full_history] = self._predict(
                self.models["instant"], result.loc[~full_history], INSTANT_FEATURES
            )
            predictions[full_history] = self._predict(
                self.models["sensor_temporal"],
                result.loc[full_history],
                SENSOR_TEMPORAL_FEATURES,
            )
            model_used = np.where(
                full_history,
                "Sensor-only temporal",
                "Sensor-only instant (warm-up)",
            )
        else:
            raise ValueError(f"Unknown calibration mode: {mode}")

        result["calibrated_temperature_c"] = predictions
        result["calibration_correction_c"] = result["sensor temperature"] - predictions
        result["model_used"] = model_used
        result["history_status"] = np.where(full_history, "6+ prior hourly records", "warm-up")
        return result

    def get_model_info(self) -> dict:
        return self.metadata
