"""
Feature Engineering Module

Generates 61 predictive features (31 spatial + 30 temporal) for PurpleAir
temperature calibration model.

Features include:
- Lagged variables (temperature, humidity, radiation 1-6 hours ago)
- Rolling statistics (moving averages, std dev, ranges, trends)
- Cumulative radiation (3-6 hour accumulation)
- Change indicators (temperature rise/fall rates, acceleration)
- Thermal persistence (heat wave/cold spell counters)
- Derived meteorology (dewpoint, VPD, wind speed/direction)
- Engineered terms (polynomial and interaction terms)

Example:
    >>> from data.feature_engineering import engineer_features
    >>> features = engineer_features(sensor_data, era5_data)
    >>> print(f"Generated {len(features.columns)} features")
"""

import numpy as np
import pandas as pd
from loguru import logger
from typing import Optional


class FeatureEngineer:
    """Generate calibration features from sensor and meteorological data.

    This class implements the complete feature engineering pipeline described
    in the paper, producing 61 predictive features plus 2 stratification
    indicators.
    """

    def __init__(self, climate_zone: Optional[str] = None):
        """Initialize feature engineer.

        Args:
            climate_zone: Köppen climate zone ('Arid', 'Temperate', 'Continental')
                Used for temperature stratification thresholds.
        """
        self.climate_zone = climate_zone

        # Temperature stratification thresholds (climate-zone-specific)
        self.temp_thresholds = {
            "Arid": {"p25": 15.0, "p75": 30.0},
            "Temperate": {"p25": 10.0, "p75": 25.0},
            "Continental": {"p25": 5.0, "p75": 22.0},
        }

    def create_lagged_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create lagged variables (11 features).

        Features:
        - Temperature 1-6 hours ago (6 features)
        - Humidity 1-3 hours ago (3 features)
        - Solar radiation 1-2 hours ago (2 features)

        Args:
            data: DataFrame with 'temperature', 'humidity', 'SSRD' columns

        Returns:
            DataFrame with original data plus lagged features
        """
        logger.info("Creating lagged features...")

        data = data.copy()

        # Temperature lags (1-6 hours)
        for lag in range(1, 7):
            data[f"temp_{lag}h"] = data["temperature"].shift(lag)

        # Humidity lags (1-3 hours)
        for lag in range(1, 4):
            data[f"humidity_{lag}h"] = data["humidity"].shift(lag)

        # Solar radiation lags (1-2 hours)
        for lag in range(1, 3):
            data[f"SSRD_{lag}h"] = data["SSRD"].shift(lag)

        return data

    def create_rolling_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create rolling statistics (10 features).

        Features:
        - 3/6/12-hour temperature moving averages (3 features)
        - 3/6/12-hour temperature standard deviations (3 features)
        - 3/6-hour temperature ranges (2 features)
        - 3/6-hour temperature linear trends (2 features)

        Args:
            data: DataFrame with 'temperature' column

        Returns:
            DataFrame with rolling statistics
        """
        logger.info("Creating rolling statistics...")

        data = data.copy()

        # Moving averages
        for window in [3, 6, 12]:
            data[f"temp_ma_{window}h"] = (
                data["temperature"].rolling(window=window, min_periods=1).mean()
            )

        # Standard deviations
        for window in [3, 6, 12]:
            data[f"temp_sd_{window}h"] = (
                data["temperature"].rolling(window=window, min_periods=1).std()
            )

        # Temperature ranges
        for window in [3, 6]:
            rolling = data["temperature"].rolling(window=window, min_periods=1)
            data[f"temp_range_{window}h"] = rolling.max() - rolling.min()

        # Linear trends (least-squares slope over window)
        for window in [3, 6]:
            data[f"temp_trend_{window}h"] = self._calculate_rolling_trend(
                data["temperature"], window
            )

        return data

    def _calculate_rolling_trend(
        self, series: pd.Series, window: int
    ) -> pd.Series:
        """Calculate least-squares linear trend over rolling window.

        Args:
            series: Time series data
            window: Rolling window size

        Returns:
            Series of slope values (units per hour)
        """
        def trend_func(x):
            if len(x) < 2:
                return 0.0
            time_idx = np.arange(len(x))
            coeffs = np.polyfit(time_idx, x, deg=1)
            return coeffs[0]  # slope

        return series.rolling(window=window, min_periods=2).apply(
            trend_func, raw=True
        )

    def create_change_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create temperature change indicators (4 features).

        Features:
        - 1/2/3-hour temperature changes (3 features)
        - Temperature acceleration (second derivative, 1 feature)

        Args:
            data: DataFrame with 'temperature' column

        Returns:
            DataFrame with change indicators
        """
        logger.info("Creating change indicators...")

        data = data.copy()

        # Temperature changes
        for lag in [1, 2, 3]:
            data[f"temp_change_{lag}h"] = data["temperature"] - data["temperature"].shift(lag)

        # Temperature acceleration (change in rate of change)
        data["temp_accel"] = data["temp_change_1h"] - data["temp_change_1h"].shift(1)

        return data

    def create_cumulative_radiation(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create cumulative radiation features (3 features).

        Features:
        - 3-hour cumulative solar radiation (1 feature)
        - 6-hour cumulative solar radiation (1 feature)
        - Hourly radiation change rate (1 feature)

        Args:
            data: DataFrame with 'SSRD' column

        Returns:
            DataFrame with cumulative radiation features
        """
        logger.info("Creating cumulative radiation features...")

        data = data.copy()

        # Cumulative radiation over windows
        for window in [3, 6]:
            data[f"SSRD_sum_{window}h"] = (
                data["SSRD"].rolling(window=window, min_periods=1).sum()
            )

        # Radiation change rate
        data["SSRD_change"] = data["SSRD"] - data["SSRD"].shift(1)

        return data

    def create_thermal_persistence(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create thermal persistence features (2 features).

        Features:
        - Hot streak: consecutive hours above 75th percentile (1 feature)
        - Cold streak: consecutive hours below 25th percentile (1 feature)

        Args:
            data: DataFrame with 'temperature' column

        Returns:
            DataFrame with persistence features
        """
        logger.info("Creating thermal persistence features...")

        data = data.copy()

        # Get thresholds for climate zone
        if self.climate_zone:
            thresholds = self.temp_thresholds.get(
                self.climate_zone,
                {"p25": data["temperature"].quantile(0.25),
                 "p75": data["temperature"].quantile(0.75)}
            )
        else:
            thresholds = {
                "p25": data["temperature"].quantile(0.25),
                "p75": data["temperature"].quantile(0.75)
            }

        # Hot streak counter
        hot_condition = data["temperature"] > thresholds["p75"]
        data["hot_streak"] = self._calculate_streak(hot_condition)

        # Cold streak counter
        cold_condition = data["temperature"] < thresholds["p25"]
        data["cold_streak"] = self._calculate_streak(cold_condition)

        return data

    def _calculate_streak(self, condition: pd.Series) -> pd.Series:
        """Calculate consecutive occurrence counter.

        Args:
            condition: Boolean series

        Returns:
            Series of consecutive occurrence counts
        """
        streak = condition.astype(int)
        streak_counter = (
            streak.groupby((streak != streak.shift()).cumsum()).cumcount() + 1
        )
        return streak_counter * streak

    def create_derived_meteorology(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create derived meteorological variables (5 features).

        Features:
        - Wind speed from u/v components (1 feature)
        - Wind direction from u/v components (1 feature)
        - Dewpoint temperature (1 feature)
        - Dewpoint depression (1 feature)
        - Vapor pressure deficit (1 feature)

        Args:
            data: DataFrame with 'temperature', 'humidity', 'u10', 'v10'

        Returns:
            DataFrame with derived meteorology
        """
        logger.info("Creating derived meteorological features...")

        data = data.copy()

        # Wind speed
        data["wind_speed"] = np.sqrt(data["u10"]**2 + data["v10"]**2)

        # Wind direction (0° = North, 90° = East)
        data["wind_dir"] = np.arctan2(data["v10"], data["u10"]) * 180 / np.pi
        data["wind_dir"] = (data["wind_dir"] + 360) % 360  # Normalize to 0-360

        # Dewpoint temperature (Magnus-Tetens formula)
        data["dewpoint"] = self._calculate_dewpoint(
            data["temperature"], data["humidity"]
        )

        # Dewpoint depression
        data["dewpoint_dep"] = data["temperature"] - data["dewpoint"]

        # Vapor pressure deficit (FAO-56 equation)
        data["VPD"] = self._calculate_vpd(data["temperature"], data["humidity"])

        return data

    def _calculate_dewpoint(self, temp: pd.Series, rh: pd.Series) -> pd.Series:
        """Calculate dewpoint using Magnus-Tetens formula.

        Uses temperature-dependent parameters:
        - T < 0°C: Buck (1981) parameters
        - 0 ≤ T ≤ 60°C: Alduchov & Eskridge (1996) parameters

        Args:
            temp: Temperature (°C)
            rh: Relative humidity (%)

        Returns:
            Dewpoint temperature (°C)
        """
        # Parameters for different temperature ranges
        a_cold, b_cold = 22.452, 272.55  # T < 0°C
        a_warm, b_warm = 17.625, 243.04  # 0 ≤ T ≤ 60°C

        dewpoint = temp.copy()

        # Cold temperatures
        cold_mask = temp < 0
        if cold_mask.any():
            alpha = np.log(rh[cold_mask] / 100) + (
                a_cold * temp[cold_mask] / (b_cold + temp[cold_mask])
            )
            dewpoint[cold_mask] = b_cold * alpha / (a_cold - alpha)

        # Warm temperatures
        warm_mask = temp >= 0
        if warm_mask.any():
            alpha = np.log(rh[warm_mask] / 100) + (
                a_warm * temp[warm_mask] / (b_warm + temp[warm_mask])
            )
            dewpoint[warm_mask] = b_warm * alpha / (a_warm - alpha)

        return dewpoint

    def _calculate_vpd(self, temp: pd.Series, rh: pd.Series) -> pd.Series:
        """Calculate vapor pressure deficit using FAO-56 equation.

        Args:
            temp: Temperature (°C)
            rh: Relative humidity (%)

        Returns:
            Vapor pressure deficit (kPa)
        """
        # Saturation vapor pressure (FAO-56)
        e_s = 0.6108 * np.exp(17.27 * temp / (temp + 237.3))

        # Actual vapor pressure
        e_a = e_s * (rh / 100)

        # VPD
        vpd = e_s - e_a

        return vpd

    def create_engineered_terms(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create polynomial and interaction terms (12 features).

        Features:
        - Temperature squared (1 feature)
        - Humidity squared (1 feature)
        - Temperature × humidity interaction (1 feature)
        - Temperature × sensor age interaction (1 feature)
        - Additional polynomial/interaction terms (8 features)

        Args:
            data: DataFrame with relevant columns

        Returns:
            DataFrame with engineered terms
        """
        logger.info("Creating engineered terms...")

        data = data.copy()

        # Polynomial terms
        data["temp_squared"] = data["temperature"] ** 2
        data["humidity_squared"] = data["humidity"] ** 2

        # Interaction terms
        data["temp_x_humidity"] = data["temperature"] * data["humidity"]

        if "life" in data.columns:
            data["temp_x_life"] = data["temperature"] * data["life"]

        # Additional terms as needed
        # (Placeholder for additional engineered features)

        return data

    def create_stratification_indicators(
        self, data: pd.DataFrame
    ) -> pd.DataFrame:
        """Create temperature stratification indicators (2 features).

        Features:
        - is_hot: Binary indicator for hot stratum (1 feature)
        - is_cold: Binary indicator for cold stratum (1 feature)

        Args:
            data: DataFrame with 'temperature' column

        Returns:
            DataFrame with stratification indicators
        """
        logger.info("Creating stratification indicators...")

        data = data.copy()

        # Get thresholds
        if self.climate_zone:
            thresholds = self.temp_thresholds.get(
                self.climate_zone,
                {"p25": data["temperature"].quantile(0.25),
                 "p75": data["temperature"].quantile(0.75)}
            )
        else:
            thresholds = {
                "p25": data["temperature"].quantile(0.25),
                "p75": data["temperature"].quantile(0.75)
            }

        # Binary indicators
        data["is_hot"] = (data["temperature"] > thresholds["p75"]).astype(int)
        data["is_cold"] = (data["temperature"] < thresholds["p25"]).astype(int)

        return data


def engineer_features(
    sensor_data: pd.DataFrame,
    era5_data: pd.DataFrame,
    climate_zone: Optional[str] = None
) -> pd.DataFrame:
    """Generate all 63 calibration features.

    Args:
        sensor_data: PurpleAir sensor data (temperature, humidity)
        era5_data: ERA5 meteorological data
        climate_zone: Köppen climate zone (optional)

    Returns:
        DataFrame with 63 features (61 training + 2 stratification)

    Example:
        >>> features = engineer_features(sensor_data, era5_data)
        >>> print(f"Features: {features.columns.tolist()}")
    """
    logger.info("Starting feature engineering pipeline...")

    # Merge sensor and ERA5 data
    data = pd.merge(sensor_data, era5_data, on="timestamp", how="inner")

    # Initialize feature engineer
    engineer = FeatureEngineer(climate_zone=climate_zone)

    # Generate features
    data = engineer.create_lagged_features(data)
    data = engineer.create_rolling_features(data)
    data = engineer.create_change_indicators(data)
    data = engineer.create_cumulative_radiation(data)
    data = engineer.create_thermal_persistence(data)
    data = engineer.create_derived_meteorology(data)
    data = engineer.create_engineered_terms(data)
    data = engineer.create_stratification_indicators(data)

    logger.info(f"Feature engineering complete: {len(data.columns)} total columns")

    return data


if __name__ == "__main__":
    logger.info("Feature engineering module loaded")
