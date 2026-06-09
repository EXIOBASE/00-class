from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parent

# Classifications live at the top level of the 00-class repo (``class/``) so a
# human opening the repo finds them immediately, rather than buried under the
# package. ``DATA_ROOT`` resolves to that repo root in the
# normal editable (``pip install -e .``) layout. The packaged ``data/``
# directory is kept only as a fallback for the unusual case of the package
# being installed without the surrounding repo.
REPO_ROOT = PACKAGE_ROOT.parents[1]
DATA_ROOT = REPO_ROOT if (REPO_ROOT / "class").is_dir() else PACKAGE_ROOT / "data"


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
