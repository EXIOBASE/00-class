"""Rebuild class/exio_country_axes.xlsx from the macro_db comparison CSVs.

``exio_country_axes.xlsx`` is the **canonical** home of the rx1 / rx2 country
classifications. The rx1 / rx2 *selections* (and their coverage flags) are
computed by the ``macro_db`` analysis (``scripts/make_extended_exiobase_list.py``,
output under ``data/fin/comparisons/``); this script consumes that analysis,
adds the ``region12`` grouping, and publishes the canonical axis here. macro_db's
runtime then reads the axis back from here via ``exiobase_meta.read_country_axis``
rather than from its own comparison CSV. The legacy EXIOBASE3 axis order is
preserved from the existing ``exio_country_axes.xlsx`` `exiobase3` sheet (its
``desire_order`` column is the single source of truth for the legacy DESIRE
country order); only the derived columns are re-harmonised against
``country_converter``.

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
import sys
from pathlib import Path

import country_converter as coco
import pandas as pd
from io_utils.config import get_path, load_config

ROOT = Path(__file__).resolve().parents[1]
# Make the in-tree package importable when run as a plain script so the
# region12 classification has exactly one reader, shared with the library.
sys.path.insert(0, str(ROOT / "src"))
from exiobase_meta.country_axes import (  # noqa: E402
    read_region12,
    region12_codes,
    remind_to_r12,
)

DEFAULT_MACRO_DB = ROOT.parent / "02-macro_db"
# Absolute path comes from config.yaml at the repo root (config.local.yaml
# overrides per machine); the --check-legacy CLI flag still overrides it.
_CFG = load_config(repo_root=ROOT)
DEFAULT_LEGACY_R12 = get_path(_CFG, "paths.legacy_r12_csv")
OUT_XLSX = ROOT / "class" / "exio_country_axes.xlsx"

# The 12 region codes and the coco.REMIND -> region12 relabels are NOT
# hard-coded here. They are read from the single source of truth,
# class/region12.csv, via region12_codes() and remind_to_r12().

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
    """ISO3 -> EXIOBASE r12 code derived from coco.REMIND.

    The REMIND -> region12 relabels (CAZ -> CAU, REF -> RUS) come from
    class/region12.csv, not a hard-coded dict.
    """
    cc = coco.CountryConverter()
    relabel = remind_to_r12()
    out: dict[str, str] = {}
    for iso3, remind in zip(cc.data["ISO3"], cc.data["REMIND"]):
        if not isinstance(remind, str) or pd.isna(remind):
            continue
        out[iso3] = relabel.get(remind, remind)
    return out


def assign_region12(iso3: str, coco_r12: dict[str, str]) -> str:
    """Assign one of the 12 EXIOBASE r12 codes to an ISO3 country."""
    if not iso3 or iso3 == "nan":
        return ""
    if iso3 in MANUAL_REGION12:
        return MANUAL_REGION12[iso3]
    return coco_r12.get(iso3, "")


def build_exiobase3_axis(axis_xlsx: Path, coco_r12: dict[str, str]) -> pd.DataFrame:
    cc = coco.CountryConverter()
    # The legacy DESIRE country order (EU members then non-EU then RoW, the
    # positional order embedded in every legacy EXIOBASE .mat / .csv source
    # file) is the single source of truth held in the `desire_order` column of
    # the existing `exiobase3` sheet. We preserve that order and country set and
    # re-derive only the volatile columns (name, iso3, region12) via
    # country_converter, so the ordering lives in exactly one place.
    prev = pd.read_excel(axis_xlsx, sheet_name="exiobase3").sort_values("desire_order")
    order_codes = [
        (str(r.iso2) if str(r.type) == "country" and str(r.iso2) not in ("", "nan")
         else str(r.code))
        for r in prev.itertuples()
    ]
    desire_rank = {c: i + 1 for i, c in enumerate(order_codes)}
    iso2_set = sorted(set(order_codes))
    # NB: continent is deliberately NOT stored. It is derived metadata, not part
    # of the country classification, and storing it froze a silent error (coco's
    # ISO2 column holds regexes like ``^GR$|^EL$``, so a dict-zip lookup of "GR"
    # returned NaN, leaving Greece / UK with no continent). Derive it on demand
    # with ``cc.convert(code, src="ISO2", to="continent")`` if ever needed.
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
    """Add a region12 column to an rx1/rx2 table.

    Drops ``continent`` (derived metadata that isn't part of the
    classification; see ``build_exiobase3_axis``).
    """
    out = df.copy().drop(columns=["continent"], errors="ignore")
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
    regions = region12_codes()
    mat = pd.DataFrame(
        0, index=axis["name"].tolist(), columns=list(regions), dtype=int,
    )
    for _, row in axis.iterrows():
        r12 = row.get("region12", "")
        if r12 in regions:
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

    region12 = read_region12()
    print(f"Region12 classification: {len(region12)} regions from region12.csv "
          f"({', '.join(region12['region12'])})")

    print("Loading coco.REMIND -> EXIOBASE r12 mapping")
    coco_r12 = coco_remind_lookup()
    relabels = {k: v for k, v in remind_to_r12().items() if k != v}
    print(f"  {len(coco_r12)} ISO3 -> r12 entries "
          f"(relabels from region12.csv: {relabels})")

    print(f"Reading macro_db comparison CSVs from {args.macro_db}")
    rx1 = add_region12_to_macro_db_axis(
        load_macro_db_axis(args.macro_db, "exiobase_rx1"), coco_r12,
    )
    rx2 = add_region12_to_macro_db_axis(
        load_macro_db_axis(args.macro_db, "exiobase_rx2"), coco_r12,
    )

    print(f"Building exiobase3 axis (preserving order from {OUT_XLSX.name})")
    e3 = build_exiobase3_axis(OUT_XLSX, coco_r12)

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
