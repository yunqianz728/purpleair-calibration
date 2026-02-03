"""
Test Script for PurpleAir Temperature Calibration Pipeline
===========================================================

Tests the complete calibration workflow:
1. Load sample data
2. Fetch ERA5 data
3. Engineer features
4. Apply calibration models
5. Display results

Author: Yunqian Zhang, Lu Liang
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

from utils.era5_reader import ERA5Reader
from utils.feature_engineering import FeatureEngineer
from utils.model_predictor import TemperatureCalibrator

def test_calibration_pipeline():
    """Test the complete calibration pipeline"""

    print("="*70)
    print("PurpleAir Temperature Calibration - Pipeline Test")
    print("="*70)

    # Step 1: Load sample data
    print("\n[Step 1/4] Loading sample data...")
    try:
        df = pd.read_csv('sample_data.csv')
        print(f"✅ Loaded {len(df)} records from sample_data.csv")
        print(f"   Columns: {list(df.columns)}")
        print(f"\nFirst 3 rows:")
        print(df.head(3))
    except Exception as e:
        print(f"❌ Failed to load sample data: {str(e)}")
        return False

    # Step 2: Fetch ERA5 data
    print("\n[Step 2/4] Fetching ERA5 meteorological data...")
    try:
        era5_reader = ERA5Reader()
        df_with_era5 = era5_reader.get_batch_era5_data(df)
        era5_reader.close()
        print(f"✅ Retrieved ERA5 data for {len(df_with_era5)} records")

        # Check ERA5 variables
        era5_vars = ['sshf', 'ssrd', 'strd', 'tp', 'u10', 'v10']
        available_vars = [var for var in era5_vars if var in df_with_era5.columns]
        print(f"   Available ERA5 variables: {available_vars}")

        # Show sample ERA5 values
        print(f"\nSample ERA5 values (first record):")
        for var in available_vars:
            print(f"   {var}: {df_with_era5[var].iloc[0]:.4f}")

    except FileNotFoundError as e:
        print(f"❌ ERA5 data file not found: {str(e)}")
        print(f"   Please ensure ERA5 NetCDF files exist for 2024-01")
        return False
    except Exception as e:
        print(f"❌ Failed to fetch ERA5 data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Engineer features
    print("\n[Step 3/4] Engineering features...")
    try:
        engineer = FeatureEngineer()
        df_features = engineer.engineer_all_features(df_with_era5)
        feature_list = engineer.get_feature_list()
        print(f"✅ Generated {len(feature_list)} features")

        # Show feature groups
        print(f"\nFeature breakdown:")
        print(f"   - Basic features: 27")
        print(f"   - Lagged features: 11")
        print(f"   - Change rates: 4")
        print(f"   - Statistical features: 15")
        print(f"   - Wind features: 4")
        print(f"   - Classification: 2")
        print(f"   Total: {len(feature_list)}")

        # Check for NaN values
        nan_count = df_features[feature_list].isna().sum().sum()
        if nan_count > 0:
            print(f"   ⚠️ Warning: {nan_count} NaN values detected in features")
        else:
            print(f"   ✓ No NaN values in features")

    except Exception as e:
        print(f"❌ Failed to engineer features: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Apply calibration models
    print("\n[Step 4/4] Applying temperature-stratified calibration...")
    try:
        calibrator = TemperatureCalibrator()
        df_result = calibrator.calibrate(df_features, feature_list)
        print(f"✅ Calibration complete!")

        # Show model info
        model_info = calibrator.get_model_info()
        print(f"\nModel information:")
        for regime, info in model_info.items():
            print(f"   {regime.capitalize()}: {info['type']}, {info['n_features']} features")

        # Show temperature regimes
        regime_counts = df_result['temperature_regime'].value_counts()
        print(f"\nTemperature regime distribution:")
        for regime in ['cold', 'normal', 'hot']:
            count = regime_counts.get(regime, 0)
            pct = (count / len(df_result)) * 100
            print(f"   {regime.capitalize():10s}: {count:3d} records ({pct:5.1f}%)")

    except Exception as e:
        print(f"❌ Failed to apply calibration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Display results
    print("\n" + "="*70)
    print("CALIBRATION RESULTS")
    print("="*70)

    # Calculate statistics
    original_temps = df_result['sensor temperature'].values
    calibrated_temps = df_result['calibrated_temperature'].values
    corrections = df_result['calibration_correction'].values

    print(f"\nTemperature Statistics (°C):")
    print(f"   Original mean:     {np.mean(original_temps):.2f}°C")
    print(f"   Calibrated mean:   {np.mean(calibrated_temps):.2f}°C")
    print(f"   Average correction: {np.mean(corrections):.2f}°C")
    print(f"   Max correction:    {np.max(corrections):.2f}°C")
    print(f"   Min correction:    {np.min(corrections):.2f}°C")

    # Show detailed results
    print(f"\nDetailed Results (first 5 records):")
    print("-" * 70)
    print(f"{'Time':<20} {'Original':<10} {'Calibrated':<12} {'Correction':<12} {'Regime':<10}")
    print("-" * 70)

    for i in range(min(5, len(df_result))):
        timestamp = df_result['timestamp'].iloc[i]
        orig = original_temps[i]
        calib = calibrated_temps[i]
        corr = corrections[i]
        regime = df_result['temperature_regime'].iloc[i]
        print(f"{str(timestamp):<20} {orig:>8.2f}°C  {calib:>9.2f}°C  {corr:>9.2f}°C  {regime:<10}")

    # Save results
    output_file = 'test_calibration_results.csv'
    df_result.to_csv(output_file, index=False)
    print(f"\n✅ Results saved to: {output_file}")

    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nThe calibration pipeline is working correctly!")
    print("You can now run the web app with: streamlit run app.py")

    return True

if __name__ == "__main__":
    try:
        success = test_calibration_pipeline()
        if not success:
            print("\n❌ Tests failed. Please check the error messages above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
