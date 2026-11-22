"""
Download script for all-MiniLM-L6-v2 Sentence-BERT model.
Saves weights, tokenizer, and config files locally to:
backend/ml/saved_models/all-MiniLM-L6-v2/
"""

import os
import sys
import time
from pathlib import Path

from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TARGET_DIR = Path("backend/ml/saved_models/all-MiniLM-L6-v2").resolve()


def download_and_save():
    print(f"Target directory: {TARGET_DIR}")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading tokenizer from {MODEL_NAME}...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.save_pretrained(str(TARGET_DIR))
    print(f"Tokenizer saved in {time.time() - t0:.2f}s")

    print(f"Downloading model from {MODEL_NAME}...")
    t1 = time.time()
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.save_pretrained(str(TARGET_DIR))
    print(f"Model saved in {time.time() - t1:.2f}s")

    # Verify files and report sizes
    total_bytes = 0
    print("\nSaved files:")
    for f in TARGET_DIR.iterdir():
        if f.is_file():
            size = f.stat().st_size
            total_bytes += size
            print(f"  - {f.name}: {size / (1024 * 1024):.2f} MB")

    print(f"\nTotal model size on disk: {total_bytes / (1024 * 1024):.2f} MB")
    print("Download and local storage complete.")


if __name__ == "__main__":
    download_and_save()
