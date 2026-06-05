"""Concordance readers (shipped with the package as data).

The product-to-industry concordance is canonical EXIOBASE classification
metadata, so it lives here rather than being read from a hardcoded path
in a consuming repo. See AGENTS.md "Classifications and country axes".
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from .io import DATA_ROOT

_PI_CONCORDANCE_FILE = "EXIOBASE20p_EXIOBASE20i_codes.txt"


@lru_cache(maxsize=2)
def read_pi_concordance(data_root: Path | None = None) -> pd.DataFrame:
    """Binary product-to-industry concordance (200 x 163, 0/1 matrix).

    Rows are product codes, columns are industry codes; every row sums to
    1 (each product maps to exactly one industry). Returned as float, with
    ``index.name = "product"`` and ``columns.name = "industry"`` in the
    file's native order (product / industry CodeNr order).
    """
    root = data_root or DATA_ROOT
    path = root / "concordances" / _PI_CONCORDANCE_FILE
    if not path.exists():
        raise FileNotFoundError(f"p->i concordance not found: {path}")
    df = pd.read_csv(path, sep="\t", index_col=0)
    df.index.name = "product"
    df.columns.name = "industry"
    return df.astype(float)
