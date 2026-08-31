"""
Quick Start Example: PurpleAir Temperature Calibration

This script demonstrates the basic workflow for calibrating PurpleAir
temperature sensors using pre-trained models.

Usage:
    python examples/quick_start_example.py

Requirements:
    - Pre-trained models downloaded to results/models/
    - Sample data (or replace with your own)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.calibration import TemporalTempStratCalibrator


def create_sample_data():
    """Create sample sensor data for demonstration.

    In practice, replace this with your actual PurpleAir and ERA5 data.
    """
    print("Creating sample data...")

    # Generate timestamps (100 hours)
    timestamps = pd.date_range(
        start='2024-01-01 00:00:00',
        periods=100,
        freq='H'
    )

    # Simulate PurpleAir sensor data with realistic bias
    true_temperature = 20 + 10 * np.sin(np.arange(100) * 2 * np.pi / 24)  # Diurnal cycle
    sensor_bias = 5.0 + 3.0 * np.sin(np.arange(100) * 2 * np.pi / 24)  # Diurnal bias
    sensor_temperature = true_temperature + sensor_bias + np.random.randn(100) * 0.5

    # Create DataFrame
    data = pd.DataFrame({
        'timestamp': timestamps,
        'temperature': sensor_temperature,
        'humidity': 50 + 20 * np.random.randn(100),
        'latitude': 40.0,
        'longitude': -120.0,
        'elevation': 100.0,
        'life': 365,  # Sensor age in days

        # ERA5 meteorological variables
        'SSRD': np.maximum(0, 1000000 * np.sin(np.arange(100) * 2 * np.pi / 24)),  # Solar radiation
        'STRD': 300000 + 50000 * np.random.randn(100),  # Thermal radiation
        'SSHF': 100 + 200 * np.sin(np.arange(100) * 2 * np.pi / 24),  # Sensible heat
        'u10': 2.0 + 1.0 * np.random.randn(100),  # U-wind
        'v10': 1.0 + 0.5 * np.random.randn(100),  # V-wind
        'precipitation': np.maximum(0, 0.001 * np.random.randn(100)),  # Precipitation

        # Reference temperature (for validation only - not used in calibration)
        'reference_temp': true_temperature
    })

    # Ensure humidity is in valid range
    data['humidity'] = data['humidity'].clip(0, 100)

    print(f"Created {len(data)} hourly observations")
    return data


def main():
    """Main workflow demonstration."""

    print("=" * 60)
    print("PurpleAir Temperature Calibration - Quick Start Example")
    print("=" * 60)
    print()

    # Step 1: Create or load data
    print("Step 1: Loading data...")
    data = create_sample_data()

    print(f"Data shape: {data.shape}")
    print(f"Temperature range: {data['temperature'].min():.1f} to {data['temperature'].max():.1f}°C")
    print()

    # Step 2: Initialize calibrator
    print("Step 2: Initializing calibrator...")
    print("Note: This requires pre-trained models in results/models/")
    print("      Download models using: python scripts/download_models.py")
    print()

    try:
        calibrator = TemporalTempStratCalibrator(
            model_path='results/models/temporal_tempstrat'
        )
        print("Calibrator initialized successfully!")
    except Exception as e:
        print(f"Error initializing calibrator: {e}")
        print("\nPlease ensure models are downloaded to results/models/")
        print("Run: python scripts/download_models.py")
        return

    print()

    # Step 3: Calibrate data
    print("Step 3: Calibrating temperature measurements...")

    try:
        calibrated = calibrator.calibrate(
            data=data,
            return_uncertainty=True
        )
        print("Calibration complete!")
    except Exception as e:
        print(f"Error during calibration: {e}")
        return

    print()

    # Step 4: Display results
    print("Step 4: Results summary")
    print("-" * 60)

    # Calculate errors (if reference available)
    if 'reference_temp' in data.columns:
        uncalibrated_error = (data['temperature'] - data['reference_temp']).abs()
        calibrated_error = (calibrated['temperature_calibrated'] - data['reference_temp']).abs()

        print(f"Uncalibrated MAE:  {uncalibrated_error.mean():.2f}°C")
        print(f"Calibrated MAE:    {calibrated_error.mean():.2f}°C")
        print(f"Error reduction:   {(1 - calibrated_error.mean() / uncalibrated_error.mean()) * 100:.1f}%")
        print()

    # Show sample of results
    print("Sample calibrated results:")
    print(calibrated[['timestamp', 'temperature', 'temperature_calibrated',
                      'temperature_bias', 'stratum']].head(10))
    print()

    # Stratum distribution
    print("Temperature stratum distribution:")
    print(calibrated['stratum'].value_counts())
    print()

    # Step 5: Save results
    print("Step 5: Saving results...")
    output_file = 'examples/calibrated_output.csv'
    calibrated.to_csv(output_file, index=False)
    print(f"Results saved to: {output_file}")
    print()

    # Step 6: Visualization (optional)
    print("Step 6: Generating visualization...")
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Plot 1: Temperature comparison
        axes[0].plot(calibrated['timestamp'], data['temperature'],
                    label='Uncalibrated', alpha=0.7)
        axes[0].plot(calibrated['timestamp'], calibrated['temperature_calibrated'],
                    label='Calibrated', alpha=0.7)
        if 'reference_temp' in data.columns:
            axes[0].plot(calibrated['timestamp'], data['reference_temp'],
                        label='Reference', linestyle='--', color='black')
        axes[0].set_ylabel('Temperature (°C)')
        axes[0].set_title('Temperature Calibration Results')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Plot 2: Bias over time
        axes[1].plot(calibrated['timestamp'], calibrated['temperature_bias'])
        axes[1].set_xlabel('Time')
        axes[1].set_ylabel('Estimated Bias (°C)')
        axes[1].set_title('Predicted Sensor Bias')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('examples/calibration_visualization.png', dpi=300)
        print("Visualization saved to: examples/calibration_visualization.png")

    except ImportError:
        print("Matplotlib not available, skipping visualization")

    print()
    print("=" * 60)
    print("Quick start example completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Replace sample data with your actual PurpleAir and ERA5 data")
    print("2. See docs/USAGE.md for detailed documentation")
    print("3. Explore notebooks/ for interactive examples")
    print("4. Visit https://huggingface.co/spaces/yunqianz/purpleair-calibration")
    print("   for web-based calibration (no coding required)")


if __name__ == "__main__":
    main()
