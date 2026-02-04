#!/usr/bin/env python3
"""
Automated Zenodo Upload Script for ERA5 Data
=============================================

This script uploads all ERA5 NetCDF files to Zenodo with proper metadata.

Usage:
    python upload_to_zenodo.py

Prerequisites:
    pip install requests tqdm

Author: Yunqian Zhang, Lu Liang
"""

import os
import sys
import json
import requests
from pathlib import Path
from tqdm import tqdm

# Configuration
ERA5_DATA_DIR = "/Users/yunqianzhang/Desktop/PA/气象数据"
ZENODO_API_URL = "https://zenodo.org/api/deposit/depositions"

# Metadata for the dataset
METADATA = {
    "metadata": {
        "title": "ERA5 Reanalysis Data for PurpleAir Temperature Calibration (2022-2024)",
        "upload_type": "dataset",
        "description": (
            "Hourly ERA5 meteorological reanalysis data for the continental United States "
            "(CONUS) from June 2022 to December 2024. This dataset supports the "
            "PurpleAir temperature sensor calibration project.\n\n"

            "<strong>Variables included:</strong>\n"
            "• sshf: Surface sensible heat flux (J/m²)\n"
            "• ssrd: Surface solar radiation downwards (J/m²)\n"
            "• strd: Surface thermal radiation downwards (J/m²)\n"
            "• tp: Total precipitation (m)\n"
            "• u10: 10m U wind component (m/s)\n"
            "• v10: 10m V wind component (m/s)\n\n"

            "<strong>Coverage:</strong>\n"
            "• Spatial: CONUS (24°N-50°N, 235°E-293°E / -125°W to -67°W)\n"
            "• Temporal: June 2022 - December 2024\n"
            "• Resolution: 0.25° × 0.25°, hourly\n\n"

            "<strong>Related publication:</strong>\n"
            "Zhang, Y., Rong, Y., & Liang, L. (2025). Nationwide Calibration of "
            "PurpleAir Temperature Sensors for Heat Exposure Research.\n\n"

            "<strong>Data source:</strong>\n"
            "ERA5 from Copernicus Climate Data Store (https://cds.climate.copernicus.eu/)\n\n"

            "<strong>File format:</strong>\n"
            "NetCDF4 files, one file per month (YYYY-MM.nc)\n"
            "Total: 31 files, ~47 GB"
        ),
        "creators": [
            {
                "name": "Zhang, Yunqian",
                "affiliation": "University of California, Berkeley",
                "orcid": "0000-0002-XXXX-XXXX"  # Replace with real ORCID
            },
            {
                "name": "Liang, Lu",
                "affiliation": "University of California, Berkeley",
                "orcid": "0000-0002-XXXX-XXXX"  # Replace with real ORCID
            }
        ],
        "keywords": [
            "ERA5",
            "meteorological data",
            "PurpleAir",
            "temperature calibration",
            "reanalysis",
            "CONUS",
            "climate data",
            "sensor calibration"
        ],
        "related_identifiers": [
            {
                "identifier": "10.5281/zenodo.18463819",
                "relation": "isSupplementTo",
                "scheme": "doi"
            }
        ],
        "license": "CC-BY-4.0",
        "access_right": "open"
    }
}


def get_access_token():
    """Get Zenodo access token from user or environment"""
    token = os.getenv('ZENODO_ACCESS_TOKEN')

    if not token:
        print("\n" + "="*70)
        print("Zenodo Access Token Required")
        print("="*70)
        print("\nTo upload to Zenodo, you need an access token.")
        print("\nSteps to get your token:")
        print("1. Go to: https://zenodo.org/account/settings/applications/tokens/new/")
        print("2. Create a new token with 'deposit:write' scope")
        print("3. Copy the token and paste it here\n")
        print("Alternatively, set environment variable:")
        print("  export ZENODO_ACCESS_TOKEN='your-token-here'\n")

        token = input("Enter your Zenodo access token: ").strip()

    return token


def create_deposition(token):
    """Create a new Zenodo deposition"""
    print("\n📝 Creating new Zenodo deposition...")

    headers = {"Content-Type": "application/json"}
    params = {"access_token": token}

    response = requests.post(
        ZENODO_API_URL,
        json={},
        headers=headers,
        params=params
    )

    if response.status_code != 201:
        print(f"❌ Failed to create deposition: {response.text}")
        sys.exit(1)

    deposition = response.json()
    deposition_id = deposition['id']

    print(f"✅ Created deposition ID: {deposition_id}")
    return deposition


def upload_file(deposition, token, file_path):
    """Upload a single file to Zenodo deposition"""
    filename = file_path.name
    bucket_url = deposition['links']['bucket']

    print(f"\n📤 Uploading: {filename}")

    with open(file_path, 'rb') as f:
        # Get file size
        file_size = file_path.stat().st_size

        # Upload with progress bar
        with tqdm(total=file_size, unit='B', unit_scale=True, desc=filename) as pbar:
            def read_in_chunks(file_obj, chunk_size=8192):
                while True:
                    data = file_obj.read(chunk_size)
                    if not data:
                        break
                    pbar.update(len(data))
                    yield data

            # Create a custom file-like object that tracks progress
            class ProgressFileWrapper:
                def __init__(self, f, pbar):
                    self.f = f
                    self.pbar = pbar

                def read(self, size=-1):
                    data = self.f.read(size)
                    if data:
                        self.pbar.update(len(data))
                    return data

            f.seek(0)  # Reset file pointer
            response = requests.put(
                f"{bucket_url}/{filename}",
                data=ProgressFileWrapper(f, pbar),
                params={"access_token": token}
            )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to upload {filename}: {response.text}")
        return False

    print(f"✅ Uploaded: {filename}")
    return True


def add_metadata(deposition_id, token, metadata):
    """Add metadata to the deposition"""
    print("\n📋 Adding metadata...")

    url = f"{ZENODO_API_URL}/{deposition_id}"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": token}

    response = requests.put(
        url,
        json=metadata,
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        print(f"❌ Failed to add metadata: {response.text}")
        return False

    print("✅ Metadata added successfully")
    return True


def publish_deposition(deposition_id, token):
    """Publish the deposition"""
    print("\n🚀 Publishing deposition...")

    url = f"{ZENODO_API_URL}/{deposition_id}/actions/publish"
    params = {"access_token": token}

    response = requests.post(url, params=params)

    if response.status_code != 202:
        print(f"❌ Failed to publish: {response.text}")
        return None

    published = response.json()
    doi = published.get('doi')
    record_id = published.get('record_id')

    print(f"\n{'='*70}")
    print("🎉 SUCCESS! Dataset published to Zenodo")
    print(f"{'='*70}")
    print(f"\n✅ DOI: {doi}")
    print(f"✅ Record ID: {record_id}")
    print(f"✅ URL: https://zenodo.org/record/{record_id}")
    print(f"\n📝 Next steps:")
    print(f"1. Update app/utils/zenodo_downloader.py:")
    print(f"   ZENODO_RECORD_ID = \"{record_id}\"")
    print(f"\n2. Test download:")
    print(f"   python app/utils/zenodo_downloader.py")
    print(f"\n3. Deploy to Streamlit Cloud with secret:")
    print(f"   ZENODO_RECORD_ID = \"{record_id}\"")
    print(f"{'='*70}\n")

    return published


def main():
    print("\n" + "="*70)
    print("Zenodo ERA5 Data Upload Script")
    print("="*70)

    # Check if ERA5 data directory exists
    data_dir = Path(ERA5_DATA_DIR)
    if not data_dir.exists():
        print(f"\n❌ Error: ERA5 data directory not found: {data_dir}")
        sys.exit(1)

    # Get list of NetCDF files
    nc_files = sorted(data_dir.glob("*.nc"))
    if not nc_files:
        print(f"\n❌ Error: No .nc files found in {data_dir}")
        sys.exit(1)

    print(f"\n📁 Found {len(nc_files)} NetCDF files")
    total_size = sum(f.stat().st_size for f in nc_files)
    print(f"📊 Total size: {total_size / (1024**3):.2f} GB")

    # Show file list
    print(f"\nFiles to upload:")
    for f in nc_files[:3]:
        print(f"  • {f.name}")
    if len(nc_files) > 6:
        print(f"  • ...")
    for f in nc_files[-3:]:
        print(f"  • {f.name}")

    # Confirm upload
    print(f"\n⚠️  This will upload {total_size / (1024**3):.2f} GB to Zenodo.")
    print(f"⚠️  This may take 2-3 hours depending on your internet speed.")

    confirm = input("\nProceed with upload? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("\n❌ Upload cancelled.")
        sys.exit(0)

    # Get access token
    token = get_access_token()
    if not token:
        print("\n❌ Access token required. Exiting.")
        sys.exit(1)

    # Create deposition
    deposition = create_deposition(token)
    deposition_id = deposition['id']

    # Upload files
    print(f"\n{'='*70}")
    print(f"Uploading {len(nc_files)} files to Zenodo")
    print(f"{'='*70}")

    failed_files = []
    for i, file_path in enumerate(nc_files, 1):
        print(f"\n[{i}/{len(nc_files)}]")
        success = upload_file(deposition, token, file_path)
        if not success:
            failed_files.append(file_path.name)

    if failed_files:
        print(f"\n⚠️  {len(failed_files)} files failed to upload:")
        for f in failed_files:
            print(f"  • {f}")

        retry = input("\nDo you want to publish anyway? (yes/no): ").strip().lower()
        if retry not in ['yes', 'y']:
            print("\n❌ Upload incomplete. Deposition not published.")
            print(f"   Deposition ID: {deposition_id}")
            print(f"   You can continue uploading later or delete this deposition.")
            sys.exit(1)

    # Add metadata
    add_metadata(deposition_id, token, METADATA)

    # Publish
    published = publish_deposition(deposition_id, token)

    if published:
        # Save record ID to file for easy access
        record_id = published.get('record_id')
        with open('ZENODO_RECORD_ID.txt', 'w') as f:
            f.write(f"{record_id}\n")
        print(f"✅ Record ID saved to: ZENODO_RECORD_ID.txt")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
