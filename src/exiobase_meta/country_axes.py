"""Read EXIOBASE country axes (exiobase3, rx1, rx2).

A country axis is a canonical ordering of countries / RoW buckets used as
a row/column dimension in EXIOBASE-shape datasets. Each row of an axis
table identifies a country (or RoW aggregate) with at minimum an
``order``, ``code``, ``name``, ``type`` and ``region12`` column.

Three axes are bundled:

- **exiobase3** (49 entries): the legacy EXIOBASE3 axis - 44 individual
  countries + 5 RoW buckets (WA/WL/WE/WF/WM). Sourced from the existing
  ``exio_mr_meta.xlsx`` `pro` sheet and harmonised against
  ``country_converter`` for names / ISO codes.

- **rx1** (152 entries): extended axis built from the largest data-coverage
  intersection across macro_db (UN SNA Main Aggregates >=15y), IEA Energy
  Balances, and FAO Production Crops/Livestock. 147 individual countries +
  the same 5 RoW buckets. Strict TIER_A definition.

- **rx2** (159 entries): rx1 plus 7 promoted countries (DR Congo, Sudan,
  Sao Tome, Greenland, South Sudan, Kosovo, Curacao) that fall just short
  of strict TIER_A but are present in at least one of {ICIO, FAO, IEA} and
  have strong UN historic coverage.

Each axis also carries a ``region12`` column with the 12-region grouping
used by the EXIOBASE MRSUT/MRIOT aggregator (``build_mr``). The 12 codes
are sourced from ``country_converter``'s ``REMIND`` column with two
relabels: ``CAZ -> CAU`` and ``REF -> RUS`` (preserving EXIOBASE labels).
Verified zero mismatches against the legacy
``D:\\indecol\\Projects\\MRIOs\\Concordances\\EXIO3r12r.csv`` matrix for
all 44 EXIOBASE3 individual countries. The wide 49x12 binary matrix is
also provided as the ``r12`` sheet of ``exio_country_axes.xlsx``.

See ``data/fin/comparisons/`` in the ``macro_db`` repository for the
candidate matrix and selection criteria, and the macro_db AGENTS.md
"Extended EXIOBASE country axes" section for rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .io import DATA_ROOT, read_excel


AXIS_NAMES = ("exiobase3", "rx1", "rx2")

# The 12-region grouping is NOT hard-coded here. It lives in the bundled
# CSV ``data/class/region12.csv`` (the single source of truth) and the
# country -> region links are made by ``country_converter`` via that
# file's ``remind_source`` column. Use ``region12_codes()`` /
# ``read_region12()`` / ``remind_to_r12()`` below. ``R12_REGIONS`` is kept
# as a lazily-derived module attribute for backward compatibility (see
# ``__getattr__``).


@lru_cache(maxsize=2)
def _read_region12_cached(path: str) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False)


def read_region12(data_root: Path | None = None) -> pd.DataFrame:
    """Read the fixed 12-region classification CSV.

    Columns
    -------
    region12 : str
        The EXIOBASE r12 region code (e.g. ``CAU``, ``CHA``).
    name : str
        Human-readable region name.
    remind_source : str
        The ``country_converter`` ``REMIND`` code that maps onto this
        region. Encodes the two EXIOBASE relabels (``CAZ`` -> ``CAU``,
        ``REF`` -> ``RUS``); the other ten map to themselves.

    This CSV is the single source of truth for the grouping; the actual
    country -> region assignment is performed by ``country_converter``
    joined on ``remind_source`` (see ``remind_to_r12``).
    """
    data_root = data_root or DATA_ROOT
    path = data_root / "class" / "region12.csv"
    if not path.exists():
        raise FileNotFoundError(f"region12 classification CSV not found: {path}")
    return _read_region12_cached(str(path)).copy()


def region12_codes(data_root: Path | None = None) -> tuple[str, ...]:
    """The 12 EXIOBASE region codes, in the CSV's (canonical) order."""
    return tuple(read_region12(data_root)["region12"].astype(str))


def remind_to_r12(data_root: Path | None = None) -> dict[str, str]:
    """``country_converter`` ``REMIND`` code -> EXIOBASE ``region12`` code."""
    df = read_region12(data_root)
    return {str(r): str(c) for r, c in zip(df["remind_source"], df["region12"])}


def __getattr__(name: str):
    # PEP 562: keep ``R12_REGIONS`` importable without reading the CSV at
    # import time. It is derived from the CSV, never hard-coded.
    if name == "R12_REGIONS":
        return region12_codes()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Supported axis orderings. ``canonical`` (default) returns rows in the
# ``order`` column's sequence (alphabetical by name for exiobase3).
# ``desire_legacy`` re-sorts by the ``desire_order`` column to recover
# the legacy DESIRE positional order (EU members then non-EU then RoW)
# embedded in legacy EXIOBASE .mat / .csv source files (NAMA, Eurostat
# SUT, Material, CREEA dom_prod). Only meaningful for the ``exiobase3``
# axis; rx1 / rx2 do not have a legacy positional analogue and request
# of ``desire_legacy`` on them is rejected.
AXIS_ORDERS = ("canonical", "desire_legacy")


@dataclass
class CountryAxis:
    """A single country-axis classification.

    Attributes
    ----------
    name : str
        Axis identifier ("exiobase3", "rx1", "rx2").
    table : pandas.DataFrame
        One row per axis entry. Columns include ``order``, ``code``,
        ``name``, ``type`` (``country`` or ``RoW``), ``iso3``, ``iso2``,
        ``continent``, ``members`` (comma-separated ISO3s for RoW rows).
        rx1 / rx2 carry additional flag columns inherited from the
        candidate matrix (``in_macro_db_historic``, ``in_IEA``, ...).
    """

    name: str
    table: pd.DataFrame

    @property
    def n(self) -> int:
        return len(self.table)

    @property
    def codes(self) -> list[str]:
        """The canonical code column (ISO3 for individuals, WA/WL/.. for RoW)."""
        return self.table["code"].astype(str).tolist()

    @property
    def names(self) -> list[str]:
        """Display names in axis order."""
        return self.table["name"].astype(str).tolist()

    @property
    def individual_countries(self) -> pd.DataFrame:
        return self.table[self.table["type"] == "country"]

    @property
    def row_buckets(self) -> pd.DataFrame:
        return self.table[self.table["type"] == "RoW"]

    def row_members(self, code: str) -> list[str]:
        """Return the ISO3 list pooled into a RoW bucket (e.g. 'WA')."""
        sub = self.table[self.table["code"] == code]
        if sub.empty:
            raise KeyError(f"RoW code {code!r} not in axis {self.name!r}")
        raw = sub.iloc[0].get("members", "")
        if pd.isna(raw):
            return []
        return [m for m in str(raw).split(",") if m]

    def region12(self) -> pd.Series:
        """Per-row 12-region (r12) code, indexed by axis ``code`` column."""
        return self.table.set_index("code")["region12"].astype(str)

    def region12_groups(self) -> dict[str, list[str]]:
        """Map each r12 region code to the list of axis codes assigned to it."""
        s = self.region12()
        return {r: s.index[s == r].tolist() for r in region12_codes() if (s == r).any()}


@lru_cache(maxsize=8)
def _read_axis_cached(path: str, sheet_name: str) -> pd.DataFrame:
    return read_excel(Path(path), sheet_name)


def read_country_axis(
    name: str,
    data_root: Path | None = None,
    use_cache: bool = True,
    order: str = "canonical",
) -> CountryAxis:
    """Read one country axis by name (``exiobase3`` / ``rx1`` / ``rx2``).

    Parameters
    ----------
    name : str
        Axis identifier: ``"exiobase3"``, ``"rx1"``, or ``"rx2"``.
    data_root : Path, optional
        Override the bundled data directory (mostly for tests).
    use_cache : bool, default True
        If True, cache the underlying Excel read.
    order : str, default ``"canonical"``
        Row ordering. ``"canonical"`` returns rows in the workbook's
        ``order`` column sequence (alphabetical by name for exiobase3).
        ``"desire_legacy"`` re-sorts by the ``desire_order`` column to
        recover the legacy DESIRE positional order. The ``desire_legacy``
        order is the column / row ordering used by every legacy
        EXIOBASE .mat / .csv source file. Only the ``exiobase3`` axis
        supports it; passing it for ``rx1`` / ``rx2`` raises.
    """
    if name not in AXIS_NAMES:
        raise ValueError(
            f"Unknown country axis {name!r}; expected one of {AXIS_NAMES}",
        )
    if order not in AXIS_ORDERS:
        raise ValueError(
            f"Unknown axis order {order!r}; expected one of {AXIS_ORDERS}",
        )
    data_root = data_root or DATA_ROOT
    path = data_root / "class" / "exio_country_axes.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Country-axes workbook not found: {path}")
    reader = _read_axis_cached if use_cache else _read_axis_cached.__wrapped__
    table = reader(str(path), name)
    if order == "desire_legacy":
        if name != "exiobase3":
            raise ValueError(
                f"desire_legacy order is only defined for the exiobase3 axis; "
                f"got {name!r}. rx1 / rx2 have no legacy positional analogue.",
            )
        if "desire_order" not in table.columns:
            raise ValueError(
                "exiobase3 axis is missing the 'desire_order' column. "
                "Re-run scripts/refresh_country_axes.py to regenerate the "
                "workbook.",
            )
        table = table.sort_values("desire_order", kind="stable").reset_index(drop=True)
    return CountryAxis(name=name, table=table)


def read_all_country_axes(
    data_root: Path | None = None,
    use_cache: bool = True,
    order: str = "canonical",
) -> dict[str, CountryAxis]:
    """Load all three axes at once. Keyed by axis name.

    The ``order`` argument applies only to ``exiobase3`` (the only axis
    with a ``desire_order`` column); rx1 / rx2 always come back canonical.
    """
    out: dict[str, CountryAxis] = {}
    for n in AXIS_NAMES:
        out[n] = read_country_axis(
            n, data_root, use_cache,
            order=order if n == "exiobase3" else "canonical",
        )
    return out


def read_r12_matrix(
    data_root: Path | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Read the wide 49-row legacy EXIOBASE3 -> 12-region binary matrix.

    Rows: EXIOBASE3 entry names (44 individual countries + 5 RoW
    buckets). Columns: the 12 region codes (``R12_REGIONS``). Values:
    1 if the row belongs to that column's region, else 0.

    This is the format expected by the legacy MATLAB
    ``build_agg_msut_generic.m`` (the ``Gr.data`` matrix). The
    individual-country r12 assignments are also surfaced on the
    ``exiobase3`` / ``rx1`` / ``rx2`` axes via their ``region12`` column;
    use ``CountryAxis.region12()`` for that.
    """
    data_root = data_root or DATA_ROOT
    path = data_root / "class" / "exio_country_axes.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Country-axes workbook not found: {path}")
    reader = _read_axis_cached if use_cache else _read_axis_cached.__wrapped__
    df = reader(str(path), "r12")
    # The first column carries the row name (set in the writer); make it index.
    if "name" in df.columns:
        df = df.set_index("name")
    elif df.columns[0] in df.columns:
        df = df.set_index(df.columns[0])
    return df
