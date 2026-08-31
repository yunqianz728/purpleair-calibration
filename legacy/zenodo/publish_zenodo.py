#!/usr/bin/env python3
"""
Publish Zenodo Deposition (Fix ORCID and publish)
==================================================

This script fixes the metadata and publishes the existing deposition.
All files have already been uploaded.

Usage:
    python publish_zenodo.py 18485026
"""

import os
import sys
import requests

ZENODO_API_URL = "https://zenodo.org/api/deposit/depositions"

# Fixed metadata WITHOUT invalid ORCID identifiers
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
                "affiliation": "University of California, Berkeley"
            },
            {
                "name": "Liang, Lu",
                "affiliation": "University of California, Berkeley"
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
    """Get Zenodo access token from environment"""
    token = os.getenv('ZENODO_ACCESS_TOKEN')
    if not token:
        token = input("Enter your Zenodo access token: ").strip()
    return token


def update_metadata(deposition_id, token):
    """Update metadata for the deposition"""
    print(f"\n📋 Updating metadata for deposition {deposition_id}...")

    url = f"{ZENODO_API_URL}/{deposition_id}"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": token}

    response = requests.put(
        url,
        json=METADATA,
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        print(f"❌ Failed to update metadata: {response.text}")
        return False

    print("✅ Metadata updated successfully (ORCID removed)")
    return True


def publish_deposition(deposition_id, token):
    """Publish the deposition"""
    print(f"\n🚀 Publishing deposition {deposition_id}...")

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
    if len(sys.argv) < 2:
        print("\n❌ Error: Deposition ID required")
        print(f"\nUsage: python {sys.argv[0]} <deposition_id>")
        print(f"\nExample: python {sys.argv[0]} 18485026")
        sys.exit(1)

    deposition_id = sys.argv[1]

    token = get_access_token()
    if not token:
        print("\n❌ Access token required")
        sys.exit(1)

    # Update metadata (remove invalid ORCID)
    if not update_metadata(deposition_id, token):
        sys.exit(1)

    # Publish
    published = publish_deposition(deposition_id, token)

    if published:
        # Save record ID
        record_id = published.get('record_id')
        with open('ZENODO_RECORD_ID.txt', 'w') as f:
            f.write(f"{record_id}\n")
        print(f"✅ Record ID saved to: ZENODO_RECORD_ID.txt")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
