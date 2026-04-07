from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PACKAGE_ROOT / "data"


def sanitize_key(value: str) -> str:
    key = str(value).strip().replace(".", "_")
    key = re.sub(r"[^0-9A-Za-z_]+", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    if not key:
        key = "blank"
    if key[0].isdigit():
        key = f"_{key}"
    return key


def read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet_name)
