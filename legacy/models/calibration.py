"""
Main Calibration Interface

Provides high-level API for calibrating PurpleAir temperature sensors using
pre-trained models.

Example:
    >>> from models.calibration import TemporalTempStratCalibrator
    >>> calibrator = TemporalTempStratCalibrator()
    >>> calibrated_data = calibrator.calibrate(sensor_data)
"""

import os
from typing import Dict, Optional, Union

import joblib
import numpy as np
import pandas as pd
from loguru import logger


class TemporalTempStratCalibrator:
    """Temperature-stratified calibration model (Temporal-TempStrat).

    This is the recommended model achieving MAE of 0.38-0.53°C across
    cold/moderate/hot thermal regimes.

    Attributes:
        models: Dictionary of trained models for each temperature stratum
        feature_names: List of required feature names
        temp_thresholds: Temperature stratification thresholds
    """

    def __init__(self, model_path: Optional[str] = None):
        """Initialize calibrator with pre-trained models.

        Args:
            model_path: Path to directory containing model files. If None,
                downloads from Hugging Face Hub.
        """
        self.model_path = model_path or self._get_default_model_path()
        self.models = {}
        self.temp_thresholds = {}
        self.feature_names = []

        self._load_models()
        logger.info("Temporal-TempStrat calibrator initialized")

    def _get_default_model_path(self) -> str:
        """Get default model path (downloads if needed)."""
        # Placeholder: would download from Hugging Face
        raise NotImplementedError(
            "Model auto-download not implemented. "
            "Download models from: "
            "https://huggingface.co/spaces/yunqianz/purpleair-calibration"
        )

    def _load_models(self):
        """Load pre-trained models for each stratum."""
        logger.info(f"Loading models from {self.model_path}")

        strata = ["cold", "moderate", "hot"]
        for stratum in strata:
            model_file = os.path.join(
                self.model_path, f"xgboost_{stratum}.joblib"
            )
            if os.path.exists(model_file):
                self.models[stratum] = joblib.load(model_file)
                logger.info(f"Loaded {stratum} stratum model")
            else:
                raise FileNotFoundError(f"Model file not found: {model_file}")

        # Load metadata (thresholds, feature names)
        metadata_file = os.path.join(self.model_path, "metadata.json")
        if os.path.exists(metadata_file):
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                self.temp_thresholds = metadata.get("temp_thresholds", {})
                self.feature_names = metadata.get("feature_names", [])

    def calibrate(
        self,
        data: pd.DataFrame,
        return_uncertainty: bool = False
    ) -> pd.DataFrame:
        """Calibrate PurpleAir temperature measurements.

        Args:
            data: DataFrame with sensor data and ERA5 variables
            return_uncertainty: If True, include prediction uncertainty

        Returns:
            DataFrame with calibrated temperatures and metadata

        Required columns in input data:
            - temperature: Raw PurpleAir temperature (°C)
            - humidity: Relative humidity (%)
            - SSRD, STRD, SSHF: ERA5 radiation variables
            - u10, v10: ERA5 wind components
            - elevation, latitude, longitude: Sensor metadata
            - ... (see feature_engineering.py for complete list)

        Output columns:
            - temperature_calibrated: Calibrated temperature (°C)
            - temperature_bias: Estimated sensor bias (°C)
            - stratum: Temperature stratum (cold/moderate/hot)
            - uncertainty: Prediction uncertainty (if return_uncertainty=True)

        Example:
            >>> calibrator = TemporalTempStratCalibrator()
            >>> result = calibrator.calibrate(sensor_data)
            >>> print(result[['temperature', 'temperature_calibrated']].head())
        """
        logger.info(f"Calibrating {len(data)} observations...")

        # Validate input data
        self._validate_input(data)

        # Assign strata
        data = self._assign_strata(data)

        # Calibrate each stratum separately
        results = []
        for stratum in ["cold", "moderate", "hot"]:
            stratum_data = data[data["stratum"] == stratum].copy()

            if len(stratum_data) == 0:
                continue

            # Predict temperature bias
            X = stratum_data[self.feature_names]
            bias_pred = self.models[stratum].predict(X)

            # Calibrated temperature = raw temperature - predicted bias
            stratum_data["temperature_bias"] = bias_pred
            stratum_data["temperature_calibrated"] = (
                stratum_data["temperature"] - bias_pred
            )

            # Uncertainty estimation (if requested)
            if return_uncertainty:
                stratum_data["uncertainty"] = self._estimate_uncertainty(
                    stratum_data, stratum
                )

            results.append(stratum_data)

        # Combine results
        calibrated = pd.concat(results, ignore_index=True)

        logger.info("Calibration complete")
        return calibrated

    def _validate_input(self, data: pd.DataFrame):
        """Validate input data has required columns."""
        required = ["temperature", "humidity", "timestamp"]

        missing = [col for col in required if col not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def _assign_strata(self, data: pd.DataFrame) -> pd.DataFrame:
        """Assign temperature strata based on thresholds."""
        data = data.copy()

        # Use default thresholds if not loaded
        if not self.temp_thresholds:
            self.temp_thresholds = {
                "p25": data["temperature"].quantile(0.25),
                "p75": data["temperature"].quantile(0.75)
            }

        # Assign strata
        conditions = [
            data["temperature"] < self.temp_thresholds["p25"],
            data["temperature"] > self.temp_thresholds["p75"],
        ]
        choices = ["cold", "hot"]
        data["stratum"] = np.select(conditions, choices, default="moderate")

        logger.info(
            f"Stratum distribution: "
            f"cold={sum(data['stratum']=='cold')}, "
            f"moderate={sum(data['stratum']=='moderate')}, "
            f"hot={sum(data['stratum']=='hot')}"
        )

        return data

    def _estimate_uncertainty(
        self, data: pd.DataFrame, stratum: str
    ) -> pd.Series:
        """Estimate prediction uncertainty (placeholder).

        In production, this could use:
        - Quantile regression for prediction intervals
        - Ensemble standard deviation
        - Conformal prediction
        """
        # Placeholder: return constant uncertainty
        return pd.Series(0.5, index=data.index)


class TemporalNationalCalibrator:
    """National-scale calibration without stratification (Temporal-National).

    Simpler alternative to temperature stratification, achieving MAE of 0.77°C.
    Suitable for applications prioritizing simplicity over maximum accuracy.
    """

    def __init__(self, model_path: Optional[str] = None):
        """Initialize national calibrator."""
        self.model_path = model_path
        self.model = None
        self.feature_names = []

        self._load_model()
        logger.info("Temporal-National calibrator initialized")

    def _load_model(self):
        """Load pre-trained national model."""
        # Placeholder implementation
        raise NotImplementedError("National model loading not implemented")

    def calibrate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calibrate using single national model."""
        logger.info(f"Calibrating {len(data)} observations (national model)...")

        # Placeholder implementation
        raise NotImplementedError("National calibration not implemented")


def batch_calibrate(
    data: pd.DataFrame,
    sensor_id_column: str = "sensor_id",
    model_type: str = "temporal_tempstrat",
    n_jobs: int = 1
) -> pd.DataFrame:
    """Calibrate multiple sensors in parallel.

    Args:
        data: DataFrame with data from multiple sensors
        sensor_id_column: Column name containing sensor IDs
        model_type: 'temporal_tempstrat' or 'temporal_national'
        n_jobs: Number of parallel jobs (-1 for all cores)

    Returns:
        Calibrated data for all sensors

    Example:
        >>> calibrated = batch_calibrate(
        ...     data=multi_sensor_data,
        ...     sensor_id_column='sensor_id',
        ...     n_jobs=4
        ... )
    """
    from joblib import Parallel, delayed

    logger.info(
        f"Batch calibrating {data[sensor_id_column].nunique()} sensors "
        f"with {n_jobs} parallel jobs"
    )

    # Initialize calibrator
    if model_type == "temporal_tempstrat":
        calibrator = TemporalTempStratCalibrator()
    elif model_type == "temporal_national":
        calibrator = TemporalNationalCalibrator()
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Process each sensor
    sensor_ids = data[sensor_id_column].unique()

    def process_sensor(sensor_id):
        sensor_data = data[data[sensor_id_column] == sensor_id]
        return calibrator.calibrate(sensor_data)

    results = Parallel(n_jobs=n_jobs)(
        delayed(process_sensor)(sid) for sid in sensor_ids
    )

    # Combine results
    calibrated = pd.concat(results, ignore_index=True)

    logger.info("Batch calibration complete")
    return calibrated


if __name__ == "__main__":
    logger.info("Calibration module loaded")
