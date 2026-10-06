"""Download and normalize the UCI Phishing Websites dataset.

The legacy UCI ``/ml/machine-learning-databases`` endpoint is no longer
reliable.  This script uses UCI's current static ZIP archive instead.
"""
from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile
import sys
import urllib.request

import pandas as pd
from scipy.io import arff


UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/327/phishing+websites.zip"


def fetch_uci_phishing() -> Path:
    """Download the UCI data and save it as ``data/phishing_websites_uci.csv``."""
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = data_dir / "phishing_websites_uci.csv"

    if dataset_path.exists():
        print(f"Dataset already exists: {dataset_path}")
        return dataset_path

    try:
        print(f"Downloading UCI Phishing Websites dataset from {UCI_ZIP_URL}...")
        with urllib.request.urlopen(UCI_ZIP_URL, timeout=60) as response:
            archive = response.read()

        with ZipFile(BytesIO(archive)) as zip_file:
            arff_name = next(
                name
                for name in zip_file.namelist()
                if name.lower() == "training dataset.arff"
            )
            arff_text = zip_file.read(arff_name).decode("utf-8")
            raw_data, _ = arff.loadarff(StringIO(arff_text))

        df = pd.DataFrame(raw_data)
        # scipy returns ARFF nominal values as bytes; retain the original -1/0/1 values.
        for column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        df = df.dropna().rename(columns={df.columns[-1]: "Result"})
        # UCI's result is 1 for phishing and -1 for legitimate.  Normalise to 0/1.
        df["Result"] = (df["Result"] == 1).astype(int)
        df.to_csv(dataset_path, index=False)

        print(f"Dataset downloaded: {len(df)} rows, {len(df.columns)} columns")
        print(f"Target distribution: {df['Result'].value_counts().to_dict()}")
        print(f"Saved to: {dataset_path}")
        return dataset_path
    except Exception as error:
        print(f"Could not download the dataset: {error}", file=sys.stderr)
        print(
            "Download it manually from https://archive.ics.uci.edu/dataset/327/phishing+websites "
            "and save a normalized CSV as data/phishing_websites_uci.csv.",
            file=sys.stderr,
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    fetch_uci_phishing()
