"""Guard rails for ``class/exio_mr_meta.xlsx``.

``exio_mr_meta.xlsx`` is a fixed-order multi-region view kept for downstream
IOT builders (e.g. ``water_extensions``'s ``lib/iot_format.py``). It
denormalises the product / industry / final-demand axes across the 49
EXIOBASE3 regions, so it necessarily repeats the sector and region
names / codes that are owned canonically elsewhere:

- product / industry / final-demand names+codes -> ``exio3class.xlsx``
- country order -> the ``exiobase3`` axis of ``exio_country_axes.xlsx``

Keeping a denormalised copy is acceptable (a fixed ordering is convenient for
the legacy IOT layout), but only if it cannot silently drift from the truth.
These tests fail the moment the copy disagrees with the canonical sources, so
the duplication is always verified rather than trusted.
"""

import pandas as pd
import pytest

from exiobase_meta.io import DATA_ROOT

MR = DATA_ROOT / "class" / "exio_mr_meta.xlsx"
CLS = DATA_ROOT / "class" / "exio3class.xlsx"
AX = DATA_ROOT / "class" / "exio_country_axes.xlsx"

# The sector identity columns shared by both representations.
KEY = ["Name", "CodeNr", "CodeTxt"]


def _mr_single_region(sheet: str) -> pd.DataFrame:
    """One region's slice of an mr_meta axis sheet (every region repeats it)."""
    df = pd.read_excel(MR, sheet_name=sheet)
    first = df["Country"].iloc[0]
    return df.loc[df["Country"] == first, KEY].reset_index(drop=True)


def _class_axis(sheet: str) -> pd.DataFrame:
    return pd.read_excel(CLS, sheet_name=sheet)[KEY].reset_index(drop=True)


@pytest.mark.parametrize(
    "mr_sheet,class_sheet",
    [("pro", "products"), ("ind", "industries"), ("FD", "finaldemand")],
)
def test_mr_meta_axis_matches_exio3class(mr_sheet: str, class_sheet: str) -> None:
    # Each region's slice of mr_meta must equal the canonical exio3class axis,
    # name for name and code for code, in order.
    pd.testing.assert_frame_equal(
        _mr_single_region(mr_sheet), _class_axis(class_sheet)
    )


def test_mr_meta_country_order_matches_exiobase3_axis() -> None:
    # The country order embedded in mr_meta (first-occurrence order of the
    # `Country` column) must equal the legacy DESIRE order owned by the
    # exiobase3 axis (its desire_order column).
    pro = pd.read_excel(MR, sheet_name="pro")
    mr_order = pro["Country"].astype(str).drop_duplicates().tolist()

    e3 = pd.read_excel(AX, sheet_name="exiobase3").sort_values("desire_order")
    ax_order = [
        str(r.iso2)
        if str(r.type) == "country" and str(r.iso2) not in ("", "nan")
        else str(r.code)
        for r in e3.itertuples()
    ]
    assert mr_order == ax_order
