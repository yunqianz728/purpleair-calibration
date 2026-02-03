"""
PurpleAir Data Download Module

This module provides functions to download temperature and humidity data from
PurpleAir sensors via the PurpleAir API.

Example:
    >>> from data.download_purpleair import fetch_purpleair_data
    >>> data = fetch_purpleair_data(
    ...     sensor_id=123456,
    ...     start_date='2024-01-01',
    ...     end_date='2024-01-31'
    ... )
    >>> print(data.head())
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Optional, Union

import aiohttp
import pandas as pd
import requests
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

# Load API key from environment
load_dotenv()
API_KEY = os.getenv("PURPLEAIR_API_KEY")


class PurpleAirDownloader:
    """Download and process PurpleAir sensor data.

    Attributes:
        api_key: PurpleAir API key (required)
        base_url: Base URL for PurpleAir API
        rate_limit: Maximum requests per minute
    """

    def __init__(self, api_key: str = None):
        """Initialize PurpleAir downloader.

        Args:
            api_key: PurpleAir API key. If None, reads from PURPLEAIR_API_KEY
                environment variable.

        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or API_KEY
        if not self.api_key:
            raise ValueError(
                "PurpleAir API key required. Set PURPLEAIR_API_KEY "
                "environment variable or pass api_key parameter."
            )

        self.base_url = "https://api.purpleair.com/v1"
        self.rate_limit = 60  # requests per minute
        logger.info("PurpleAir downloader initialized")

    def get_sensor_list(
        self,
        bounds: Optional[tuple] = None,
        states: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Get list of active PurpleAir sensors.

        Args:
            bounds: Geographic bounding box as (west, south, east, north)
            states: List of U.S. state abbreviations (e.g., ['CA', 'NY'])

        Returns:
            DataFrame containing sensor metadata: sensor_id, name, latitude,
            longitude, elevation, date_created

        Example:
            >>> downloader = PurpleAirDownloader()
            >>> sensors = downloader.get_sensor_list(states=['CA', 'NY'])
            >>> print(f"Found {len(sensors)} sensors")
        """
        logger.info("Fetching PurpleAir sensor list...")

        # Placeholder implementation
        # In production, this would query the PurpleAir API
        raise NotImplementedError(
            "Sensor list download not yet implemented. "
            "Refer to PurpleAir API documentation: "
            "https://api.purpleair.com/#api-sensors-get-sensors-data"
        )

    def fetch_sensor_history(
        self,
        sensor_id: int,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        fields: List[str] = None
    ) -> pd.DataFrame:
        """Download historical data for a single sensor.

        Args:
            sensor_id: PurpleAir sensor ID
            start_date: Start date (YYYY-MM-DD or datetime object)
            end_date: End date (YYYY-MM-DD or datetime object)
            fields: List of fields to download. If None, downloads:
                ['temperature', 'humidity', 'pressure']

        Returns:
            DataFrame with columns: timestamp, temperature, humidity, pressure

        Example:
            >>> downloader = PurpleAirDownloader()
            >>> data = downloader.fetch_sensor_history(
            ...     sensor_id=123456,
            ...     start_date='2024-01-01',
            ...     end_date='2024-01-31'
            ... )
            >>> print(data.describe())
        """
        if fields is None:
            fields = ["temperature", "humidity", "pressure"]

        logger.info(
            f"Downloading sensor {sensor_id} data from {start_date} to {end_date}"
        )

        # Placeholder implementation
        raise NotImplementedError(
            "Historical data download not yet implemented. "
            "Refer to PurpleAir API documentation: "
            "https://api.purpleair.com/#api-sensors-get-sensor-history"
        )

    async def fetch_multiple_sensors_async(
        self,
        sensor_ids: List[int],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime]
    ) -> pd.DataFrame:
        """Download data from multiple sensors asynchronously.

        Args:
            sensor_ids: List of PurpleAir sensor IDs
            start_date: Start date (YYYY-MM-DD or datetime object)
            end_date: End date (YYYY-MM-DD or datetime object)

        Returns:
            Combined DataFrame with data from all sensors

        Example:
            >>> downloader = PurpleAirDownloader()
            >>> sensor_ids = [123456, 123457, 123458]
            >>> data = asyncio.run(downloader.fetch_multiple_sensors_async(
            ...     sensor_ids=sensor_ids,
            ...     start_date='2024-01-01',
            ...     end_date='2024-01-31'
            ... ))
        """
        logger.info(f"Downloading data from {len(sensor_ids)} sensors (async)")

        # Placeholder for async implementation
        raise NotImplementedError("Async download not yet implemented")


def fetch_purpleair_data(
    sensor_id: int,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """Convenience function to download PurpleAir data.

    Args:
        sensor_id: PurpleAir sensor ID
        start_date: Start date (YYYY-MM-DD or datetime object)
        end_date: End date (YYYY-MM-DD or datetime object)
        api_key: Optional PurpleAir API key

    Returns:
        DataFrame with temperature, humidity, and metadata

    Example:
        >>> data = fetch_purpleair_data(
        ...     sensor_id=123456,
        ...     start_date='2024-01-01',
        ...     end_date='2024-01-31'
        ... )
        >>> print(data.head())
    """
    downloader = PurpleAirDownloader(api_key=api_key)
    return downloader.fetch_sensor_history(sensor_id, start_date, end_date)


def main():
    """Command-line interface for downloading PurpleAir data."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download PurpleAir sensor data"
    )
    parser.add_argument(
        "--sensor-id",
        type=int,
        required=True,
        help="PurpleAir sensor ID"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="purpleair_data.csv",
        help="Output CSV file path"
    )

    args = parser.parse_args()

    data = fetch_purpleair_data(
        sensor_id=args.sensor_id,
        start_date=args.start_date,
        end_date=args.end_date
    )

    data.to_csv(args.output, index=False)
    logger.info(f"Data saved to {args.output}")


if __name__ == "__main__":
    main()
