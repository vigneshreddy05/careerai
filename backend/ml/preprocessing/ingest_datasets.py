"""
Dataset Ingestion Script for CareerAI
Downloads the two approved candidate datasets:
1. Primary: opensporks/resumes (Hugging Face mirror of LiveCareer dataset)
2. Supplementary: Gaurav Dutta's UpdatedResumeDataSet (Tech role dataset)

Preserves raw files separately under backend/ml/datasets/raw/
"""

import os
import sys
from pathlib import Path
import httpx

# Dataset Sources
OPENSPORKS_URL = "https://huggingface.co/datasets/opensporks/resumes/resolve/main/Resume/Resume.csv"
GAURAV_DUTTA_URL = "https://raw.githubusercontent.com/611noorsaeed/Resume-Screening-App/main/UpdatedResumeDataSet.csv"

# Destination Directories
BASE_DIR = Path(__file__).resolve().parent.parent / "datasets" / "raw"
OPENSPORKS_DEST = BASE_DIR / "opensporks" / "Resume.csv"
GAURAV_DUTTA_DEST = BASE_DIR / "gaurav_dutta" / "UpdatedResumeDataSet.csv"


def download_file(url: str, dest_path: Path, description: str):
    """Download a file with streaming progress and save to dest_path."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {description} from:\n  {url}")

    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        with client.stream("GET", url) as response:
            if response.status_code != 200:
                raise RuntimeError(f"Failed to download {description}: HTTP {response.status_code}")

            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            with open(dest_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = (downloaded / total) * 100
                        print(f"\r  Progress: {downloaded / (1024*1024):.2f} MB / {total / (1024*1024):.2f} MB ({percent:.1f}%)", end="", flush=True)
                    else:
                        print(f"\r  Downloaded: {downloaded / (1024*1024):.2f} MB", end="", flush=True)

    print(f"\nSaved to: {dest_path} ({dest_path.stat().st_size / (1024*1024):.2f} MB)\n")


def main():
    print("=" * 60)
    print("CareerAI Dataset Ingestion Pipeline")
    print("=" * 60)

    try:
        # 1. Primary Dataset: opensporks/resumes
        if not OPENSPORKS_DEST.exists() or OPENSPORKS_DEST.stat().st_size == 0:
            download_file(OPENSPORKS_URL, OPENSPORKS_DEST, "opensporks/resumes (Primary)")
        else:
            print(f"Primary dataset already exists: {OPENSPORKS_DEST} ({OPENSPORKS_DEST.stat().st_size / (1024*1024):.2f} MB)")

        # 2. Supplementary Dataset: Gaurav Dutta
        if not GAURAV_DUTTA_DEST.exists() or GAURAV_DUTTA_DEST.stat().st_size == 0:
            download_file(GAURAV_DUTTA_URL, GAURAV_DUTTA_DEST, "Gaurav Dutta UpdatedResumeDataSet (Supplementary)")
        else:
            print(f"Supplementary dataset already exists: {GAURAV_DUTTA_DEST} ({GAURAV_DUTTA_DEST.stat().st_size / (1024*1024):.2f} MB)")

        print("Dataset ingestion complete.")
    except Exception as exc:
        print(f"\nIngestion Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
