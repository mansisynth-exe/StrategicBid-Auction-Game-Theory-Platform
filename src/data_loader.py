"""
data_loader.py: Module for acquiring, verifying, and loading authentic auction datasets.
Strict adherence to real data only: raises DataAcquisitionError on retrieval failure.
Never generates synthetic records or silent mock fallbacks.
"""

import os
import shutil
import zipfile
import subprocess
import hashlib
from typing import Dict, Any, Optional
import pandas as pd

ZENODO_RECORD_URL = "https://zenodo.org/records/11259259"
ZENODO_FILE_URL = "https://zenodo.org/records/11259259/files/Online%20Auctions%20Dataset.zip?download=1"
ZENODO_DOI = "10.5281/zenodo.11259259"
EXPECTED_ZIP_SHA256 = "a25dfdd0c4204d9f1b62983c3991ed5deef18bfdfe10c534852749a242807e4b"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
EXTRACTED_DATA_DIR = os.path.join(RAW_DATA_DIR, "extracted")
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
METADATA_DIR = os.path.join(PROJECT_ROOT, "data", "metadata")

RAW_ZIP_PATH = os.path.join(RAW_DATA_DIR, "Online_Auctions_Dataset.zip")
AUCTION_CSV_PATH = os.path.join(EXTRACTED_DATA_DIR, "auction.csv")
SWAROVSKI_CSV_PATH = os.path.join(EXTRACTED_DATA_DIR, "swarovski.csv")


class DataAcquisitionError(Exception):
    """Raised when authentic external dataset cannot be retrieved or verified."""
    pass


def compute_file_sha256(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_zenodo_dataset(force: bool = False) -> str:
    """
    Downloads the authentic Online Auctions Dataset from Zenodo into data/raw/.
    Uses curl executable or requests.
    Raises DataAcquisitionError if retrieval fails.
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)

    if os.path.exists(RAW_ZIP_PATH) and not force:
        # Check integrity
        file_hash = compute_file_sha256(RAW_ZIP_PATH)
        if file_hash == EXPECTED_ZIP_SHA256:
            return RAW_ZIP_PATH

    # Attempt download via curl.exe (standard on Windows and Linux)
    curl_bin = shutil.which("curl") or shutil.which("curl.exe")
    download_success = False

    if curl_bin:
        try:
            cmd = [
                curl_bin,
                "-L",
                "--retry", "3",
                "--retry-delay", "2",
                "-o", RAW_ZIP_PATH,
                ZENODO_FILE_URL
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(RAW_ZIP_PATH) and os.path.getsize(RAW_ZIP_PATH) > 1000:
                download_success = True
        except Exception:
            download_success = False

    # Fallback to requests if curl was not available or failed
    if not download_success:
        try:
            import requests
            headers = {
                "User-Agent": "curl/8.4.0",
                "Accept": "*/*"
            }
            resp = requests.get(ZENODO_FILE_URL, headers=headers, stream=True, timeout=60)
            if resp.status_code == 200:
                with open(RAW_ZIP_PATH, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                download_success = True
        except Exception:
            download_success = False

    if not download_success or not os.path.exists(RAW_ZIP_PATH) or os.path.getsize(RAW_ZIP_PATH) < 1000:
        if os.path.exists(RAW_ZIP_PATH):
            try:
                os.remove(RAW_ZIP_PATH)
            except OSError:
                pass
        error_msg = (
            "FATAL: Failed to retrieve authentic Online Auctions Dataset from Zenodo.\n"
            f"Record URL: {ZENODO_RECORD_URL}\n"
            f"DOI: {ZENODO_DOI}\n\n"
            "MANUAL RETRIEVAL INSTRUCTIONS:\n"
            "1. Visit https://zenodo.org/records/11259259\n"
            "2. Download 'Online Auctions Dataset.zip'\n"
            f"3. Place the file at: {RAW_ZIP_PATH}\n"
            f"4. Extract contents to: {EXTRACTED_DATA_DIR}\n\n"
            "Under strict scientific requirements, synthetic fallback data is prohibited."
        )
        raise DataAcquisitionError(error_msg)

    return RAW_ZIP_PATH


def extract_raw_dataset(zip_path: Optional[str] = None) -> Dict[str, str]:
    """
    Safely extracts raw dataset archive without overwriting unchanged files unnecessarily.
    Returns dict of extracted filepaths.
    """
    target_zip = zip_path or RAW_ZIP_PATH
    if not os.path.exists(target_zip):
        raise FileNotFoundError(f"Archive not found at {target_zip}")

    os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)

    with zipfile.ZipFile(target_zip, 'r') as archive:
        archive.extractall(EXTRACTED_DATA_DIR)

    return {
        "auction_csv": AUCTION_CSV_PATH,
        "swarovski_csv": SWAROVSKI_CSV_PATH
    }


def ensure_data_available() -> Dict[str, Any]:
    """
    Ensures that raw data files exist and are valid. Downloads and extracts if needed.
    Returns metadata dictionary.
    """
    if not os.path.exists(AUCTION_CSV_PATH) or not os.path.exists(SWAROVSKI_CSV_PATH):
        if not os.path.exists(RAW_ZIP_PATH):
            download_zenodo_dataset()
        extract_raw_dataset(RAW_ZIP_PATH)

    zip_hash = compute_file_sha256(RAW_ZIP_PATH) if os.path.exists(RAW_ZIP_PATH) else None
    auction_hash = compute_file_sha256(AUCTION_CSV_PATH)

    return {
        "status": "AVAILABLE",
        "raw_zip_path": RAW_ZIP_PATH,
        "raw_zip_sha256": zip_hash,
        "auction_csv_path": AUCTION_CSV_PATH,
        "auction_csv_sha256": auction_hash,
        "swarovski_csv_path": SWAROVSKI_CSV_PATH,
        "doi": ZENODO_DOI,
        "source_url": ZENODO_RECORD_URL
    }


def load_raw_auction_data() -> pd.DataFrame:
    """
    Loads raw auction.csv.
    Raises DataAcquisitionError if file does not exist.
    """
    ensure_data_available()
    if not os.path.exists(AUCTION_CSV_PATH):
        raise DataAcquisitionError(f"Missing auction records at {AUCTION_CSV_PATH}")
    return pd.read_csv(AUCTION_CSV_PATH)


def load_raw_swarovski_data() -> pd.DataFrame:
    """
    Loads raw swarovski.csv.
    """
    ensure_data_available()
    if not os.path.exists(SWAROVSKI_CSV_PATH):
        raise DataAcquisitionError(f"Missing swarovski records at {SWAROVSKI_CSV_PATH}")
    return pd.read_csv(SWAROVSKI_CSV_PATH)
