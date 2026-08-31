"""Feature engineering for PurpleAir temperature calibration.

Temporal operations are isolated by sensor and by continuous hourly segment so
one device can never borrow history from another.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


ERA5_COLUMNS = ("sshf", "ssrd", "strd", "tp", "u10", "v10")


class FeatureEngineer:
    """Create model-ready features from standardized upload columns."""

    @staticmethod
    def calculate_dewpoint(temperature_c, relative_humidity):
        humidity = np.clip(relative_humidity.astype(float), 0.1, 100.0)
        alpha = (17.27 * temperature_c) / (237.7 + temperature_c) + np.log(humidity / 100.0)
        return 237.7 * alpha / (17.27 - alpha)

    @staticmethod
    def calculate_vpd(temperature_c, relative_humidity):
        humidity = np.clip(relative_humidity.astype(float), 0.0, 100.0)
        saturation = 0.6108 * np.exp((17.27 * temperature_c) / (temperature_c + 237.3))
        return saturation * (1.0 - humidity / 100.0)

    @staticmethod
    def _streak(values: pd.Series) -> pd.Series:
        groups = (~values.astype(bool)).cumsum()
        return values.groupby(groups).cumsum().astype(int)

    def engineer_all_features(self, source: pd.DataFrame) -> pd.DataFrame:
        """Return a feature table while preserving the upload's row order.

        Required columns are ``timestamp``, ``temperature`` (already converted
        to Celsius), ``humidity``, ``latitude`` and ``longitude``. ``sensor_id``
        is optional; coordinates identify a sensor when it is absent.
        """
        df = source.copy()
        df["_row_order"] = np.arange(len(df))
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")

        if "sensor_id" in df and df["sensor_id"].notna().any():
            df["_sensor_key"] = df["sensor_id"].fillna("").astype(str)
        else:
            df["_sensor_key"] = (
                df["latitude"].round(5).astype(str) + ":" + df["longitude"].round(5).astype(str)
            )

        df = df.sort_values(["_sensor_key", "timestamp", "_row_order"]).reset_index(drop=True)
        gaps = df.groupby("_sensor_key", sort=False)["timestamp"].diff().dt.total_seconds().div(3600)
        breaks = gaps.isna() | (gaps < 0.5) | (gaps > 1.5)
        df["_segment"] = breaks.groupby(df["_sensor_key"]).cumsum().astype(int)
        group_columns = ["_sensor_key", "_segment"]
        grouped = df.groupby(group_columns, sort=False, group_keys=False)

        timestamp = df["timestamp"]
        df["year"] = timestamp.dt.year
        df["month"] = timestamp.dt.month
        df["day"] = timestamp.dt.dayofyear
        df["hour"] = timestamp.dt.hour
        df["day_of_month"] = timestamp.dt.day
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
        df["month_sin"] = np.sin(2 * np.pi * (df["month"] - 1) / 12)
        df["month_cos"] = np.cos(2 * np.pi * (df["month"] - 1) / 12)

        df["sensor temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
        df["sensor_lat"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["sensor_lon"] = pd.to_numeric(df["longitude"], errors="coerce")
        df["elevation_sensor"] = pd.to_numeric(df.get("elevation", np.nan), errors="coerce")
        df["sensor_tcc"] = pd.to_numeric(
            df.get("tree_canopy_cover", df.get("tcc", np.nan)), errors="coerce"
        )
        df["life"] = pd.to_numeric(df.get("life", np.nan), errors="coerce")

        for name in ERA5_COLUMNS:
            df[name] = pd.to_numeric(df.get(name, np.nan), errors="coerce")

        df["humidity_squared"] = df["humidity"] ** 2
        df["temp_squared_sensor"] = df["sensor temperature"] ** 2
        df["temp_humidity_product_sensor"] = df["sensor temperature"] * df["humidity"]
        df["temp_life_interaction_sensor"] = df["sensor temperature"] * df["life"]
        df["dewpoint_sensor"] = self.calculate_dewpoint(df["sensor temperature"], df["humidity"])
        df["dewpoint_depression_sensor"] = df["sensor temperature"] - df["dewpoint_sensor"]
        df["vapor_pressure_deficit_sensor"] = self.calculate_vpd(
            df["sensor temperature"], df["humidity"]
        )
        df["diurnal_radiation"] = df["ssrd"] * np.abs(np.sin(2 * np.pi * df["hour"] / 24))
        df["polar_day_night"] = (
            (df["sensor_lat"].abs() > 60)
            & (
                (df["month"].isin([6, 7, 8]) & (df["sensor_lat"] > 0))
                | (df["month"].isin([12, 1, 2]) & (df["sensor_lat"] < 0))
            )
        ).astype(int)
        df["wind_speed"] = np.sqrt(df["u10"] ** 2 + df["v10"] ** 2)
        df["wind_direction"] = np.degrees(np.arctan2(df["v10"], df["u10"]))

        for lag in range(1, 7):
            df[f"sensor_temp_{lag}h_ago"] = grouped["sensor temperature"].shift(lag)
        for lag in range(1, 4):
            df[f"humidity_{lag}h_ago"] = grouped["humidity"].shift(lag)
        df["ssrd_1h_ago"] = grouped["ssrd"].shift(1)
        df["ssrd_2h_ago"] = grouped["ssrd"].shift(2)

        df["temp_change_1h"] = df["sensor temperature"] - df["sensor_temp_1h_ago"]
        df["temp_change_2h"] = df["sensor temperature"] - df["sensor_temp_2h_ago"]
        df["temp_change_3h"] = df["sensor temperature"] - df["sensor_temp_3h_ago"]
        df["temp_acceleration"] = df["temp_change_1h"] - grouped["temp_change_1h"].shift(1)

        def rolling(column: str, window: int, operation: str) -> pd.Series:
            series = grouped[column].rolling(window=window, min_periods=1)
            result = getattr(series, operation)().reset_index(level=group_columns, drop=True)
            return result.reindex(df.index)

        for window in (3, 6, 12):
            df[f"temp_ma_{window}h"] = rolling("sensor temperature", window, "mean")
            df[f"temp_std_{window}h"] = rolling("sensor temperature", window, "std").fillna(0)
        for window in (3, 6):
            maximum = rolling("sensor temperature", window, "max")
            minimum = rolling("sensor temperature", window, "min")
            df[f"temp_range_{window}h"] = maximum - minimum
            df[f"temp_trend_{window}h"] = rolling("temp_change_1h", window, "mean")
        df["ssrd_sum_3h"] = rolling("ssrd", 3, "sum")
        df["ssrd_sum_6h"] = rolling("ssrd", 6, "sum")
        df["ssrd_change"] = df["ssrd"] - df["ssrd_1h_ago"]

        df["is_hot"] = (df["sensor temperature"] > 30).astype(int)
        df["is_cold"] = (df["sensor temperature"] < 10).astype(int)
        df["hot_streak"] = grouped["is_hot"].transform(self._streak)
        df["cold_streak"] = grouped["is_cold"].transform(self._streak)
        df["_history_hours"] = grouped.cumcount()

        return df.sort_values("_row_order").reset_index(drop=True)
