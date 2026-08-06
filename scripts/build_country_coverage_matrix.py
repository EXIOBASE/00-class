"""Build a country coverage matrix across major economic databases.

One row per country (by ISO3 where defined; aggregate regions kept separately).
Columns indicate membership/coverage in each database with the country's
identifier or label inside that database (or empty if absent).

Databases covered:
- EXIOBASE3        (cc.EXIO3 - 49 entries: 44 individual + 5 RoW)
- FAO              (cc.FAOcode - 247 entries)
- IEA              (cc.IEA - 44 reporting countries + non-OECD aggregates)
- OECD             (cc.OECD - 38 members)
- UN               (cc.UNmember - 193 members)
- WIOD             (cc.WIOD - 43 countries + RoW; legacy MRIO)
- Eora             (cc.Eora - 190+ countries)
- IMAGE/MESSAGE/REMIND (integrated assessment model regions, from cc)
- G7, G20, EU27, EFTA, BASIC, BRIC (cc memberships)
- OECD ICIO        (parsed from local v2025 files - 81 countries + RoW)
- FIGARO           (parsed from local v2025 files - 49 countries + RoW)
- GTAP 11          (113 regions from Classifications/GTAP7113r.txt)
- GLORIA           (164 regions from GLORIA_EXIO/Country_codes_link_FAO_MRIO.xlsx)

Step 1 of 3 in the rx1 / rx2 country-axis derivation:

    build_country_coverage_matrix.py   -> country_coverage_matrix.csv   (this)
    extended_exiobase_country_list.py  -> extended_exiobase_candidates.csv
    make_extended_exiobase_list.py     -> exiobase_rx{1,2}.csv
    refresh_country_axes.py            -> class/exio_country_axes.xlsx  (canonical)

Output: <paths.axis_work_dir>/country_coverage_matrix.{csv,xlsx}

Moved here from 02-macro_db on 2026-08-06: this is classification work, and
it needs nothing from macro_db but paths to external data.
"""

from __future__ import annotations

from pathlib import Path

import country_converter as coco
import pandas as pd
from io_utils.config import get_path, load_config

ROOT = Path(__file__).resolve().parents[1]
_CFG = load_config(repo_root=ROOT)

# Country-axis tables live IN this repo (class/country_axes/): they are
# METADATA, not data - small, hand-reviewed, and their history is the point,
# so git owns them and there is exactly one canonical copy. Nothing writes
# them into the shared data tree. paths.axis_work_dir may override for an
# out-of-tree experiment; it is unset by default.
OUT_DIR = get_path(_CFG, "paths.axis_work_dir") or (ROOT / "class" / "country_axes")
ICIO_DIR = get_path(_CFG, "paths.icio_dir")
FIGARO_FILE = get_path(_CFG, "paths.figaro_supply_file")
GTAP_FILE = get_path(_CFG, "paths.gtap_regions_file")
GLORIA_FILE = get_path(_CFG, "paths.gloria_country_link_file")


def _load_icio_countries() -> set[str]:
    """Return ICIO ISO3 country codes from a v2025 file."""
    fp = ICIO_DIR / "2022_SML.csv"
    cols = pd.read_csv(fp, nrows=0).columns.tolist()
    countries: set[str] = set()
    drop = {"V1", "HFCE", "GGFC", "NPISH", "GFCF", "INVNT", "DPABR"}
    for c in cols:
        if "_" not in c:
            continue
        iso, _, _ = c.partition("_")
        if iso and iso not in drop:
            countries.add(iso)
    return countries


def _load_figaro_countries() -> set[str]:
    """Return FIGARO ISO2 country codes (plus 'FIGW1' RoW sentinel)."""
    cols = pd.read_csv(FIGARO_FILE, nrows=0).columns.tolist()
    countries: set[str] = set()
    drop = {"rowLabels", "FD", "HFCE", "GGFC", "GFCF", "INV", "NPISH", "P3", "P5"}
    for c in cols:
        if "_" not in c:
            continue
        cc, _, _ = c.partition("_")
        if cc and cc not in drop:
            countries.add(cc)
    return countries


def _load_gtap() -> pd.DataFrame:
    """Return GTAP 11 regions as DataFrame[gtap_name, gtap_code]."""
    df = pd.read_csv(
        GTAP_FILE, sep="\t", header=None, names=["gtap_name", "gtap_code", "iso3"],
    )
    return df


def _load_gloria() -> pd.DataFrame:
    """Return GLORIA regions as DataFrame[fao_id, fao_name, gloria_acronym, gloria_name]."""
    df = pd.read_excel(GLORIA_FILE)
    return df.rename(columns={
        "FAOID": "fao_id",
        "CountryFAO": "fao_name",
        "Region_acronyms": "gloria_acronym",
        "Region_names": "gloria_name",
    })[["fao_id", "fao_name", "gloria_acronym", "gloria_name"]]


def build_matrix() -> pd.DataFrame:
    cc = coco.CountryConverter()
    cc_data = cc.data.copy()

    icio_iso3 = _load_icio_countries()
    figaro_iso2 = _load_figaro_countries()
    gtap_df = _load_gtap()
    gloria_df = _load_gloria()

    # Map FIGARO ISO2 -> ISO3 via cc to join. FIGW1/FIGW2 are FIGARO's
    # rest-of-world labels; we skip them for individual-country matching.
    figaro_iso3: set[str] = set()
    for code in figaro_iso2:
        if code in ("FIGW1", "FIGW2"):
            continue
        iso3 = cc.convert(code, src="ISO2", to="ISO3", not_found=None)
        if isinstance(iso3, str) and iso3 != "not found" and iso3:
            figaro_iso3.add(iso3)

    # Map GTAP ISO3-or-pseudo to actual ISO3 where possible
    gtap_iso3 = set(gtap_df["iso3"].dropna().tolist())
    # GLORIA: use the gloria_acronym (usually ISO3)
    gloria_iso3 = set(
        gloria_df["gloria_acronym"].dropna().unique().tolist()
    )

    # Build the matrix on cc.data (250 entities) - one row per cc-known country
    df = cc_data[[
        "ISO3", "ISO2", "name_short",
        "EXIO3", "EXIO3_3L",
        "FAOcode",
        "IEA",
        "OECD",
        "UNmember",
        "EU27", "G7", "G20", "BASIC", "BRIC",
        "WIOD",
        "Eora",
        "IMAGE", "MESSAGE", "REMIND",
        "continent",
    ]].copy()

    # Filter sentinel "RoW" / bucket codes so the matrix only marks
    # individual-country membership. cc.data assigns every country a
    # bucket label for WIOD ("RoW" for non-WIOD members) and EXIO3
    # (WA/WE/WF/WL/WM for non-EXIOBASE3 members). For coverage counting,
    # we want individual-country presence only.
    exio3_row_buckets = {"WA", "WE", "WF", "WL", "WM"}
    df.loc[df["EXIO3"].isin(exio3_row_buckets), "EXIO3"] = pd.NA
    df.loc[df["WIOD"] == "RoW", "WIOD"] = pd.NA
    # IMAGE/MESSAGE/REMIND aggregate regions are similar but we keep them
    # since they're the canonical regional buckets for those models.

    # ICIO column (ISO3 yes/no -> mark 1 if present)
    df["OECD_ICIO"] = df["ISO3"].apply(lambda i: i if i in icio_iso3 else "")
    # FIGARO
    df["FIGARO"] = df["ISO3"].apply(lambda i: i if i in figaro_iso3 else "")
    # GTAP
    df["GTAP11"] = df["ISO3"].apply(
        lambda i: gtap_df[gtap_df["iso3"] == i]["gtap_name"].iloc[0]
        if i in gtap_iso3 else ""
    )
    # GLORIA
    df["GLORIA"] = df["ISO3"].apply(lambda i: i if i in gloria_iso3 else "")

    # Coverage count: how many major MRIO/DB databases cover this country
    db_cols = ["EXIO3", "FAOcode", "IEA", "OECD", "WIOD", "Eora",
               "OECD_ICIO", "FIGARO", "GTAP11", "GLORIA"]
    df["n_databases"] = df[db_cols].apply(
        lambda r: sum(1 for v in r if pd.notna(v) and str(v).strip() not in ("", "nan")),
        axis=1,
    )

    # Cleanup: replace NaN with empty string for string-typed columns
    # (skip numeric columns like FAOcode/n_databases).
    for c in df.columns:
        dt = str(df[c].dtype).lower()
        if "int" in dt or "float" in dt:
            continue
        df[c] = df[c].astype(str).replace(
            {"<NA>": "", "nan": "", "None": "", "NaN": ""}
        )

    # Sort by coverage descending then name
    df = df.sort_values(["n_databases", "name_short"], ascending=[False, True])

    return df


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = build_matrix()
    csv_path = OUT_DIR / "country_coverage_matrix.csv"
    xlsx_path = OUT_DIR / "country_coverage_matrix.xlsx"
    df.to_csv(csv_path, index=False)
    try:
        df.to_excel(xlsx_path, index=False)
    except Exception as exc:  # noqa: BLE001 - xlsx is a convenience copy; the CSV is the output
        print(f"xlsx export failed: {exc}")

    print(f"Wrote {len(df)} rows to {csv_path}")
    print()
    print("Quick stats by database:")
    db_cols = ["EXIO3", "FAOcode", "IEA", "OECD", "EU27", "G7", "G20",
               "WIOD", "Eora", "OECD_ICIO", "FIGARO", "GTAP11", "GLORIA",
               "BASIC", "BRIC", "UNmember"]
    for c in db_cols:
        col = df[c].astype(str).str.strip()
        n = (col.notna() & (col != "") & (col != "<NA>")).sum()
        print(f"  {c:<14}: {n:>4} countries")

    print()
    print("Top 25 by total database coverage:")
    print(df[["name_short", "ISO3", "n_databases"] + ["EXIO3", "OECD_ICIO", "FIGARO", "GTAP11", "GLORIA"]].head(25).to_string(index=False))


if __name__ == "__main__":
    main()
