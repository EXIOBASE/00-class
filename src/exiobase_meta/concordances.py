"""Product-to-industry structure reader.

The binary product-to-industry matrix is the **authoritative EXIOBASE
product/industry structure** (which industry is the characteristic producer
of each product), so it is classification metadata and lives under
``class/`` alongside the other classifications, read via ``DATA_ROOT`` (see
``io.py``).

This is the canonical source: ``io_utils`` reads it through
``read_pi_concordance`` and the ``00-concordances-public`` repo *derives* its
published ``exiobase3p__exiobase3i`` concordance from it. The published
concordance form (tidy / wide CSV, with names and weights) belongs in that
concordances repo, not here.
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
    path = root / "class" / _PI_CONCORDANCE_FILE
    if not path.exists():
        raise FileNotFoundError(f"p->i structure not found: {path}")
    df = pd.read_csv(path, sep="\t", index_col=0)
    df.index.name = "product"
    df.columns.name = "industry"
    return df.astype(float)
