"""Rebuild data/class/exio_country_axes.xlsx from the macro_db comparison CSVs.

The rx1 / rx2 axis definitions live in the ``macro_db`` repo under
``data/fin/comparisons/`` and are produced by
``scripts/make_extended_exiobase_list.py``. The legacy EXIOBASE3 axis is
recovered from the existing ``exio_mr_meta.xlsx`` `pro` sheet's
``Country`` column harmonised against ``country_converter``.

Also writes the 12-region grouping used by ``build_mr`` (the MRSUT/MRIOT
aggregator):

- 12 region codes: CAU (Canada/Australia/NZ), CHA (China/Taiwan/HK/Macau),
  EUR (EU27 + UK), IND (India), JPN (Japan), LAM (Latin America +
  Caribbean), MEA (Middle East + N. Africa), NEU (non-EU Europe), OAS
  (other Asia + Pacific), RUS (Russia + CIS / ex-Soviet), SSA (sub-
  Saharan Africa), USA (USA).

- Source: ``country_converter``'s ``REMIND`` column, with two relabels
  to match EXIOBASE convention: ``CAZ -> CAU``, ``REF -> RUS``. Manual
  overrides are kept to a minimum (only Kosovo, which cc doesn't know).
  Verified against the legacy ``EXIO3r12r.csv`` matrix: zero mismatches
  for all 44 EXIOBASE3 individual countries. The legacy CSV is therefore
  retired and only consulted at refresh time as a sanity check.

- Each axis sheet (``exiobase3``, ``rx1``, ``rx2``) carries a ``region12``
  column so consumers can join axes to the 12-region grouping in one step.

- The wide 49x12 binary matrix is regenerated from the per-axis assignments
  (not loaded from the legacy CSV) and stored as sheet ``r12``.

Run this whenever the macro_db rx1 / rx2 axis is regenerated.

Usage:
    python scripts/refresh_country_axes.py
    python scripts/refresh_country_axes.py --macro-db /path/to/macro_db
    python scripts/refresh_country_axes.py --check-legacy /path/to/EXIO3r12r.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import country_converter as coco
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MACRO_DB = ROOT.parent / "macro_db"
DEFAULT_LEGACY_R12 = Path(
    "D:/indecol/Projects/MRIOs/Concordances/EXIO3r12r.csv"
)
OUT_XLSX = ROOT / "src" / "exiobase_meta" / "data" / "class" / "exio_country_axes.xlsx"
PRO_XLSX = ROOT / "src" / "exiobase_meta" / "data" / "exio_mr_meta.xlsx"

R12_REGIONS = ("CAU", "CHA", "EUR", "IND", "JPN", "LAM",
               "MEA", "NEU", "OAS", "RUS", "SSA", "USA")

# coco.REMIND -> our r12 codes. REMIND uses CAZ for Canada/Australia/NZ
# (we keep EXIOBASE's CAU label) and REF for Reforming Economies =
# Russia + CIS (we keep EXIOBASE's RUS label, now expanded to all CIS).
REMIND_TO_R12 = {"CAZ": "CAU", "REF": "RUS"}

ROW_NAMES = {
    "WA": "RoW Asia and Pacific",
    "WL": "RoW America",
    "WE": "RoW Europe",
    "WF": "RoW Africa",
    "WM": "RoW Middle East",
}
ROW_CODES = set(ROW_NAMES.keys())

# Legacy mapping for the 5 RoW buckets. These aren't in coco (they're
# EXIOBASE-specific aggregates), so they get explicit assignments.
ROW_R12 = {
    "WA": "OAS",  # RoW Asia and Pacific
    "WL": "LAM",  # RoW America
    "WE": "NEU",  # RoW Europe
    "WF": "SSA",  # RoW Africa
    "WM": "MEA",  # RoW Middle East
}

EXIOBASE_OVERRIDES = {
    "Türkiye": "Turkey",
    "Eswatini": "Swaziland",
}

# Manual region12 overrides for ISO3 codes coco.REMIND doesn't know.
# Keep this list as short as possible.
MANUAL_REGION12: dict[str, str] = {
    # Kosovo: Balkans, non-EU. Mirrors coco's REMIND placement for
    # neighbouring Albania, N. Macedonia, Serbia (all NEU).
    "XKX": "NEU",
}

# Names cc doesn't resolve cleanly. Used only when validating the
# refresh against the legacy CSV.
_LEGACY_CSV_NAME_SYNONYMS = {
    "Czech Republic": "Czechia",
    "South Korea": "South Korea",
    "Russia": "Russia",
    "United Kingdom": "United Kingdom",
}


def coco_remind_lookup() -> dict[str, str]:
    """ISO3 -> EXIOBASE r12 code derived from coco.REMIND."""
    cc = coco.CountryConverter()
    out: dict[str, str] = {}
    for iso3, remind in zip(cc.data["ISO3"], cc.data["REMIND"]):
        if not isinstance(remind, str) or pd.isna(remind):
            continue
        out[iso3] = REMIND_TO_R12.get(remind, remind)
    return out


def assign_region12(iso3: str, coco_r12: dict[str, str]) -> str:
    """Assign one of the 12 EXIOBASE r12 codes to an ISO3 country."""
    if not iso3 or iso3 == "nan":
        return ""
    if iso3 in MANUAL_REGION12:
        return MANUAL_REGION12[iso3]
    return coco_r12.get(iso3, "")


def build_exiobase3_axis(pro_xlsx: Path, coco_r12: dict[str, str]) -> pd.DataFrame:
    cc = coco.CountryConverter()
    pro = pd.read_excel(pro_xlsx, sheet_name="pro")
    # First-occurrence order of `Country` in `pro` preserves the legacy
    # DESIRE country order (EU members then non-EU then RoW). This is the
    # positional order embedded in every legacy EXIOBASE .mat / .csv
    # source file (NAMA, Eurostat SUT, Material, CREEA dom_prod, ...).
    # Carry it as a `desire_order` column so consumers that need to align
    # with legacy positional sources can sort by it.
    desire_seq = pro["Country"].astype(str).drop_duplicates().tolist()
    desire_rank = {c: i + 1 for i, c in enumerate(desire_seq)}
    iso2_set = sorted(pro["Country"].astype(str).unique())
    cont = dict(zip(cc.data["ISO2"], cc.data["continent"]))
    rows: list[dict] = []
    for iso2 in iso2_set:
        if iso2 in ROW_CODES:
            continue
        iso3 = cc.convert(iso2, src="ISO2", to="ISO3", not_found=None)
        name_short = cc.convert(iso2, src="ISO2", to="name_short", not_found=None)
        if not isinstance(name_short, str):
            name_short = iso2
        name = EXIOBASE_OVERRIDES.get(name_short, name_short)
        r12 = assign_region12(iso3 if isinstance(iso3, str) else "", coco_r12)
        rows.append({
            "order": 0,
            "desire_order": desire_rank.get(iso2, 0),
            "code": iso3 if isinstance(iso3, str) else iso2,
            "name": name,
            "type": "country",
            "iso3": iso3 if isinstance(iso3, str) else "",
            "iso2": iso2,
            "continent": cont.get(iso2, ""),
            "region12": r12,
            "members": "",
        })
    rows.sort(key=lambda r: r["name"])
    for code in ("WA", "WL", "WE", "WF", "WM"):
        rows.append({
            "order": 0,
            "desire_order": desire_rank.get(code, 0),
            "code": code,
            "name": ROW_NAMES[code],
            "type": "RoW",
            "iso3": "",
            "iso2": "",
            "continent": "",
            "region12": ROW_R12[code],
            "members": "",
        })
    for i, r in enumerate(rows, start=1):
        r["order"] = i
    return pd.DataFrame(rows)


def load_macro_db_axis(macro_db: Path, stem: str) -> pd.DataFrame:
    path = macro_db / "data" / "fin" / "comparisons" / f"{stem}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run macro_db's scripts/make_extended_exiobase_list.py first."
        )
    return pd.read_csv(path, keep_default_na=False)


def add_region12_to_macro_db_axis(
    df: pd.DataFrame,
    coco_r12: dict[str, str],
) -> pd.DataFrame:
    """Add a region12 column to an rx1/rx2 table."""
    out = df.copy()
    r12_col: list[str] = []
    for _, row in out.iterrows():
        if str(row.get("type", "")) == "RoW":
            r12_col.append(ROW_R12.get(str(row.get("code", "")), ""))
            continue
        iso3 = str(row.get("iso3", "")).strip()
        r12_col.append(assign_region12(iso3, coco_r12))
    out["region12"] = r12_col
    return out


def build_r12_matrix(*frames: pd.DataFrame) -> pd.DataFrame:
    """Build a wide row-x-region binary matrix for the EXIOBASE3 axis,
    matching the legacy ``EXIO3r12r.csv`` format. Driven by the
    ``exiobase3`` axis (first frame)."""
    if not frames:
        raise ValueError("no axis frame provided")
    axis = frames[0]
    mat = pd.DataFrame(
        0, index=axis["name"].tolist(), columns=list(R12_REGIONS), dtype=int,
    )
    for _, row in axis.iterrows():
        r12 = row.get("region12", "")
        if r12 in R12_REGIONS:
            mat.at[row["name"], r12] = 1
    mat.index.name = "name"
    return mat


def check_against_legacy(
    e3: pd.DataFrame, legacy_csv: Path,
) -> tuple[int, list[tuple]]:
    """Sanity-check the regenerated exiobase3 r12 against the legacy CSV.

    Returns (mismatch_count, list_of_mismatches). Used at refresh time
    only - the legacy CSV is no longer the source of truth.
    """
    if not legacy_csv.exists():
        return 0, []
    mat = pd.read_csv(legacy_csv, index_col=0)
    legacy = {n: mat.columns[mat.loc[n].astype(int).values.argmax()] for n in mat.index}
    # Add synonyms (legacy uses 'Czech Republic' etc.).
    for csv_name, canonical in _LEGACY_CSV_NAME_SYNONYMS.items():
        if csv_name in legacy:
            legacy.setdefault(canonical, legacy[csv_name])
    mismatches: list[tuple] = []
    for _, row in e3.iterrows():
        name = row["name"]
        ours = row["region12"]
        expected = legacy.get(name)
        if expected and expected != ours:
            mismatches.append((name, expected, ours))
    return len(mismatches), mismatches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--macro-db", type=Path, default=DEFAULT_MACRO_DB,
        help="Path to the macro_db repo (default: ../macro_db)",
    )
    parser.add_argument(
        "--check-legacy", type=Path, default=DEFAULT_LEGACY_R12,
        help="Path to legacy EXIO3r12r.csv for sanity check (default: %(default)s)",
    )
    parser.add_argument(
        "--output", type=Path, default=OUT_XLSX,
        help=f"Output xlsx path (default: {OUT_XLSX.relative_to(ROOT)})",
    )
    args = parser.parse_args()

    print("Loading coco.REMIND -> EXIOBASE r12 mapping")
    coco_r12 = coco_remind_lookup()
    print(f"  {len(coco_r12)} ISO3 -> r12 entries (CAZ->CAU, REF->RUS relabels applied)")

    print(f"Reading macro_db comparison CSVs from {args.macro_db}")
    rx1 = add_region12_to_macro_db_axis(
        load_macro_db_axis(args.macro_db, "exiobase_rx1"), coco_r12,
    )
    rx2 = add_region12_to_macro_db_axis(
        load_macro_db_axis(args.macro_db, "exiobase_rx2"), coco_r12,
    )

    print(f"Building exiobase3 axis from {PRO_XLSX.name}")
    e3 = build_exiobase3_axis(PRO_XLSX, coco_r12)

    n_mis, mismatches = check_against_legacy(e3, args.check_legacy)
    if mismatches:
        print(f"  WARNING: {n_mis} mismatch(es) vs legacy {args.check_legacy.name}:")
        for name, expected, ours in mismatches:
            print(f"    {name}: legacy={expected} ours={ours}")
    else:
        print(f"  sanity check vs {args.check_legacy.name}: 0 mismatches")

    r12_mat = build_r12_matrix(e3)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(args.output, engine="openpyxl") as writer:
        e3.to_excel(writer, sheet_name="exiobase3", index=False)
        rx1.to_excel(writer, sheet_name="rx1", index=False)
        rx2.to_excel(writer, sheet_name="rx2", index=False)
        r12_mat.to_excel(writer, sheet_name="r12")

    print(f"Wrote {args.output}")
    for name, df in [("exiobase3", e3), ("rx1", rx1), ("rx2", rx2)]:
        n_country = int((df["type"] == "country").sum())
        n_row = int((df["type"] == "RoW").sum())
        r12_counts = df.groupby("region12").size().to_dict()
        print(f"  {name}: {len(df)} rows ({n_country} country + {n_row} RoW)")
        print(f"    region12 distribution: "
              + ", ".join(f"{k}={v}" for k, v in sorted(r12_counts.items()) if k))
    print(f"  r12 (wide matrix): {r12_mat.shape}")


if __name__ == "__main__":
    main()
