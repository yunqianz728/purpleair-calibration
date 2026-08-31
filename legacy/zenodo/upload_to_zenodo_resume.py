#!/usr/bin/env python3
"""
Resume Zenodo Upload - Continue uploading remaining files
==========================================================

This script continues uploading to an existing Zenodo deposition.
Use this if your previous upload was interrupted.

Usage:
    python upload_to_zenodo_resume.py <deposition_id>

Example:
    python upload_to_zenodo_resume.py 18485026

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
                "orcid": "0000-0002-XXXX-XXXX"
            },
            {
                "name": "Liang, Lu",
                "affiliation": "University of California, Berkeley",
                "orcid": "0000-0002-XXXX-XXXX"
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

        token = input("Enter your Zenodo access token: ").strip()

    return token


def get_deposition(deposition_id, token):
    """Get existing deposition details"""
    print(f"\n📋 Retrieving deposition {deposition_id}...")

    url = f"{ZENODO_API_URL}/{deposition_id}"
    params = {"access_token": token}

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"❌ Failed to get deposition: {response.text}")
        sys.exit(1)

    deposition = response.json()
    print(f"✅ Found deposition: {deposition.get('title', 'Untitled')}")

    return deposition


def get_uploaded_files(deposition):
    """Get list of already uploaded files"""
    files = deposition.get('files', [])
    uploaded_filenames = [f['filename'] for f in files]

    print(f"\n📂 Already uploaded: {len(uploaded_filenames)} files")
    if uploaded_filenames:
        for filename in uploaded_filenames:
            print(f"  ✅ {filename}")

    return uploaded_filenames


def upload_file(deposition, token, file_path):
    """Upload a single file to Zenodo deposition"""
    filename = file_path.name
    bucket_url = deposition['links']['bucket']

    print(f"\n📤 Uploading: {filename}")

    # Get file size
    file_size = file_path.stat().st_size

    # Create a custom file-like object that tracks progress
    class ProgressFileWrapper:
        def __init__(self, file_path, pbar):
            self.file_path = file_path
            self.pbar = pbar
            self.f = None

        def __enter__(self):
            self.f = open(self.file_path, 'rb')
            return self

        def __exit__(self, *args):
            if self.f:
                self.f.close()

        def read(self, size=-1):
            data = self.f.read(size)
            if data:
                self.pbar.update(len(data))
            return data

        def __len__(self):
            return file_size

    # Upload with progress bar
    with tqdm(total=file_size, unit='B', unit_scale=True, desc=filename) as pbar:
        with ProgressFileWrapper(file_path, pbar) as file_wrapper:
            response = requests.put(
                f"{bucket_url}/{filename}",
                data=file_wrapper,
                headers={"Authorization": f"Bearer {token}"}
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
    print(f"1. Update .streamlit/secrets.toml:")
    print(f"   ZENODO_RECORD_ID = \"{record_id}\"")
    print(f"\n2. Test the app locally:")
    print(f"   streamlit run app/app.py")
    print(f"\n3. Deploy to Streamlit Cloud")
    print(f"{'='*70}\n")

    return published


def main():
    print("\n" + "="*70)
    print("Resume Zenodo Upload")
    print("="*70)

    # Get deposition ID from command line
    if len(sys.argv) < 2:
        print("\n❌ Error: Deposition ID required")
        print(f"\nUsage: python {sys.argv[0]} <deposition_id>")
        print(f"\nExample: python {sys.argv[0]} 18485026")
        sys.exit(1)

    deposition_id = sys.argv[1]

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

    print(f"\n📁 Found {len(nc_files)} NetCDF files locally")

    # Get access token
    token = get_access_token()
    if not token:
        print("\n❌ Access token required. Exiting.")
        sys.exit(1)

    # Get existing deposition
    deposition = get_deposition(deposition_id, token)

    # Get already uploaded files
    uploaded_filenames = get_uploaded_files(deposition)

    # Find files that still need to be uploaded
    remaining_files = [f for f in nc_files if f.name not in uploaded_filenames]

    if not remaining_files:
        print("\n✅ All files already uploaded!")
        print("\nProceed to add metadata and publish? (yes/no): ", end='')
        confirm = input().strip().lower()
        if confirm in ['yes', 'y']:
            add_metadata(deposition_id, token, METADATA)
            published = publish_deposition(deposition_id, token)

            if published:
                record_id = published.get('record_id')
                with open('ZENODO_RECORD_ID.txt', 'w') as f:
                    f.write(f"{record_id}\n")
                print(f"✅ Record ID saved to: ZENODO_RECORD_ID.txt")
        sys.exit(0)

    # Show remaining files
    print(f"\n📤 Need to upload: {len(remaining_files)} files")
    remaining_size = sum(f.stat().st_size for f in remaining_files)
    print(f"📊 Remaining size: {remaining_size / (1024**3):.2f} GB")

    print(f"\nFiles to upload:")
    for f in remaining_files[:5]:
        print(f"  • {f.name}")
    if len(remaining_files) > 5:
        print(f"  • ... and {len(remaining_files) - 5} more")

    # Confirm upload
    print(f"\n⚠️  This will upload {remaining_size / (1024**3):.2f} GB to Zenodo.")
    print(f"⚠️  Estimated time: {len(remaining_files) * 5} - {len(remaining_files) * 10} minutes")

    confirm = input("\nProceed with upload? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("\n❌ Upload cancelled.")
        sys.exit(0)

    # Upload remaining files
    print(f"\n{'='*70}")
    print(f"Uploading {len(remaining_files)} remaining files")
    print(f"{'='*70}")

    failed_files = []
    for i, file_path in enumerate(remaining_files, 1):
        print(f"\n[{len(uploaded_filenames) + i}/{len(nc_files)}]")
        success = upload_file(deposition, token, file_path)
        if not success:
            failed_files.append(file_path.name)

    if failed_files:
        print(f"\n⚠️  {len(failed_files)} files failed to upload:")
        for f in failed_files:
            print(f"  • {f}")

        print(f"\n❌ Upload incomplete. Please retry:")
        print(f"   python {sys.argv[0]} {deposition_id}")
        sys.exit(1)

    # Add metadata
    add_metadata(deposition_id, token, METADATA)

    # Publish
    published = publish_deposition(deposition_id, token)

    if published:
        # Save record ID to file
        record_id = published.get('record_id')
        with open('ZENODO_RECORD_ID.txt', 'w') as f:
            f.write(f"{record_id}\n")
        print(f"✅ Record ID saved to: ZENODO_RECORD_ID.txt")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user.")
        print(f"\nYou can resume later by running:")
        if len(sys.argv) >= 2:
            print(f"   python {sys.argv[0]} {sys.argv[1]}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
