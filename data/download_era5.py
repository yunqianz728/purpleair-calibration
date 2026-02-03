"""
ERA5 Reanalysis Data Download Module

Downloads meteorological variables from ERA5 reanalysis via Copernicus Climate
Data Store (CDS) API.

Required variables for calibration:
- Surface solar radiation downward (SSRD)
- Surface thermal radiation downward (STRD)
- Surface sensible heat flux (SSHF)
- 10-meter wind components (u10, v10)
- Total precipitation (TP)

Example:
    >>> from data.download_era5 import fetch_era5_data
    >>> data = fetch_era5_data(
    ...     lat=40.0,
    ...     lon=-120.0,
    ...     start_date='2024-01-01',
    ...     end_date='2024-01-31'
    ... )
"""

import os
from datetime import datetime
from typing import List, Optional, Union

import cdsapi
import numpy as np
import pandas as pd
import xarray as xr
from loguru import logger
from tqdm import tqdm


class ERA5Downloader:
    """Download ERA5 reanalysis data from Copernicus Climate Data Store.

    Attributes:
        cds_client: CDS API client instance
        variables: List of ERA5 variable names to download
    """

    # Variable mapping: friendly name -> ERA5 parameter name
    VARIABLE_MAPPING = {
        "solar_radiation": "surface_solar_radiation_downwards",
        "thermal_radiation": "surface_thermal_radiation_downwards",
        "sensible_heat": "surface_sensible_heat_flux",
        "u_wind": "10m_u_component_of_wind",
        "v_wind": "10m_v_component_of_wind",
        "precipitation": "total_precipitation",
        "2m_temperature": "2m_temperature",
        "2m_dewpoint": "2m_dewpoint_temperature",
    }

    def __init__(self):
        """Initialize ERA5 downloader.

        Requires CDS API credentials in ~/.cdsapirc file.
        See: https://cds.climate.copernicus.eu/api-how-to
        """
        try:
            self.cds_client = cdsapi.Client()
            logger.info("ERA5 downloader initialized")
        except Exception as e:
            logger.error(
                f"Failed to initialize CDS API client: {e}\n"
                "Set up credentials at ~/.cdsapirc\n"
                "See: https://cds.climate.copernicus.eu/api-how-to"
            )
            raise

    def download_hourly_data(
        self,
        lat: float,
        lon: float,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        variables: Optional[List[str]] = None,
        output_path: Optional[str] = None
    ) -> str:
        """Download hourly ERA5 data for a specific location.

        Args:
            lat: Latitude (degrees North)
            lon: Longitude (degrees East)
            start_date: Start date (YYYY-MM-DD or datetime)
            end_date: End date (YYYY-MM-DD or datetime)
            variables: List of variable names. If None, downloads all
                calibration-required variables.
            output_path: Path to save NetCDF file. If None, generates
                automatic filename.

        Returns:
            Path to downloaded NetCDF file

        Example:
            >>> downloader = ERA5Downloader()
            >>> file_path = downloader.download_hourly_data(
            ...     lat=40.0,
            ...     lon=-120.0,
            ...     start_date='2024-01-01',
            ...     end_date='2024-01-31'
            ... )
            >>> print(f"Downloaded to {file_path}")
        """
        if variables is None:
            variables = list(self.VARIABLE_MAPPING.keys())

        # Convert to ERA5 parameter names
        era5_variables = [self.VARIABLE_MAPPING[v] for v in variables]

        logger.info(
            f"Downloading ERA5 data for ({lat}, {lon}) "
            f"from {start_date} to {end_date}"
        )

        # Placeholder implementation
        raise NotImplementedError(
            "ERA5 download not yet implemented. "
            "Refer to CDS API documentation: "
            "https://cds.climate.copernicus.eu/cdsapp#!/dataset/"
            "reanalysis-era5-single-levels"
        )

    def process_era5_netcdf(self, netcdf_path: str) -> pd.DataFrame:
        """Process downloaded ERA5 NetCDF file to DataFrame.

        Args:
            netcdf_path: Path to ERA5 NetCDF file

        Returns:
            DataFrame with hourly ERA5 variables

        Processing steps:
            - Extract nearest grid point to sensor location
            - Convert radiation from J/m² to W/m²
            - Calculate wind speed and direction from u/v components
            - Apply quality control (remove negative values for SSRD, TP)
        """
        logger.info(f"Processing ERA5 file: {netcdf_path}")

        # Placeholder implementation
        raise NotImplementedError("ERA5 processing not yet implemented")

    def quality_control(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply quality control to ERA5 data.

        Quality control procedures (following paper methodology):
        1. Set negative SSRD values to 0 (data processing artifact)
        2. Set negative TP values to 0 (data processing artifact)
        3. Truncate SSHF at 1st and 99th percentiles
        4. Check for missing values

        Args:
            data: DataFrame with raw ERA5 variables

        Returns:
            Quality-controlled DataFrame
        """
        logger.info("Applying ERA5 quality control...")

        data = data.copy()

        # Solar radiation: negative values -> 0
        if "SSRD" in data.columns:
            negative_ssrd = (data["SSRD"] < 0).sum()
            if negative_ssrd > 0:
                logger.warning(f"Setting {negative_ssrd} negative SSRD values to 0")
                data.loc[data["SSRD"] < 0, "SSRD"] = 0

        # Precipitation: negative values -> 0
        if "TP" in data.columns:
            negative_tp = (data["TP"] < 0).sum()
            if negative_tp > 0:
                logger.warning(f"Setting {negative_tp} negative TP values to 0")
                data.loc[data["TP"] < 0, "TP"] = 0

        # Sensible heat flux: truncate extremes
        if "SSHF" in data.columns:
            p1, p99 = data["SSHF"].quantile([0.01, 0.99])
            logger.info(f"Truncating SSHF to [{p1:.1f}, {p99:.1f}] W/m²")
            data["SSHF"] = data["SSHF"].clip(p1, p99)

        # Check for missing values
        missing = data.isnull().sum()
        if missing.any():
            logger.warning(f"Missing values found:\n{missing[missing > 0]}")

        logger.info("Quality control completed")
        return data


def fetch_era5_data(
    lat: float,
    lon: float,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime]
) -> pd.DataFrame:
    """Convenience function to download and process ERA5 data.

    Args:
        lat: Latitude (degrees North)
        lon: Longitude (degrees East)
        start_date: Start date (YYYY-MM-DD or datetime)
        end_date: End date (YYYY-MM-DD or datetime)

    Returns:
        DataFrame with hourly ERA5 variables

    Example:
        >>> data = fetch_era5_data(
        ...     lat=40.0,
        ...     lon=-120.0,
        ...     start_date='2024-01-01',
        ...     end_date='2024-01-31'
        ... )
        >>> print(data.columns)
    """
    downloader = ERA5Downloader()
    netcdf_path = downloader.download_hourly_data(lat, lon, start_date, end_date)
    data = downloader.process_era5_netcdf(netcdf_path)
    data = downloader.quality_control(data)
    return data


def main():
    """Command-line interface for downloading ERA5 data."""
    import argparse

    parser = argparse.ArgumentParser(description="Download ERA5 reanalysis data")
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lon", type=float, required=True, help="Longitude")
    parser.add_argument(
        "--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", type=str, required=True, help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output", type=str, default="era5_data.csv", help="Output CSV file"
    )

    args = parser.parse_args()

    data = fetch_era5_data(
        lat=args.lat,
        lon=args.lon,
        start_date=args.start_date,
        end_date=args.end_date
    )

    data.to_csv(args.output, index=False)
    logger.info(f"ERA5 data saved to {args.output}")


if __name__ == "__main__":
    main()
