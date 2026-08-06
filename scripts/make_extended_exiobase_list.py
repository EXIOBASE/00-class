"""Produce the canonical country list for an expanded EXIOBASE.

Takes the output of extended_exiobase_country_list.py and produces two
country lists ready to use as the EXIOBASE country axis:

  - exiobase_rx1.csv:
      TIER_A only (macro_db historic + IEA + FAO). 147 individual
      countries + 5 RoW buckets.

  - exiobase_rx2.csv:
      TIER_A + 7 selected near-miss countries:
        COD (DR Congo)    - in ICIO + FAO + macro_db, missing IEA
        SDN (Sudan)       - in IEA + macro_db, missing FAO
        STP (Sao Tome)    - in ICIO + FAO + macro_db, missing IEA
        GRL (Greenland)   - in IEA + macro_db, missing FAO
        SSD (South Sudan) - in IEA + macro_db, missing FAO
        XKX (Kosovo)      - in IEA + macro_db, missing FAO
        CUW (Curacao)     - in IEA + macro_db, missing FAO
      154 individual countries + 5 RoW buckets.

Outputs: <paths.axis_work_dir>/exiobase_rx{1,2}.{csv,xlsx}

Step 3 of 3 in the rx1 / rx2 derivation (``refresh_country_axes.py`` then
publishes the canonical ``class/exio_country_axes.xlsx`` from these).
Moved here from 02-macro_db on 2026-08-06: pure selection logic over the
candidates table, needs nothing from macro_db.

Columns:
  order                  : sequential index for stable axis ordering
  code                   : ISO3 for individual countries; 'WA'/'WL'/'WE'/'WF'/'WM' for RoW
  name                   : EXIOBASE-canonical country name (applies EXIOBASE_OVERRIDES)
  type                   : 'country' or 'RoW'
  iso3                   : ISO3 (blank for RoW)
  iso2                   : ISO2 (blank for RoW)
  continent              : Africa / Americas / Asia / Europe / Oceania (blank for RoW)
  exiobase3_current      : 1 if already in current EXIOBASE3 (44 countries)
  in_macro_db_historic   : 1/0 - has >=15y UN SNA Main Aggregates summary VA
  in_macro_db_nowcast    : 1/0 - has >=15y IMF WEO NGDPD (needed for projections)
  in_IEA, in_FAO         : 1/0 source-data coverage flags
  in_ICIO, in_FIGARO, in_GLORIA, in_GTAP, in_BACI  : DB compatibility flags
  n_mrio                 : count out of 6 comparator databases
  un_summary_years       : years of UN SNA Main Aggregates VA data
  imf_weo_years          : years of IMF WEO NGDPD data
  members                : for RoW rows: comma-separated ISO3 of member countries
"""

from __future__ import annotations

from pathlib import Path

import country_converter as coco
import pandas as pd
from io_utils.config import get_path, load_config

from exiobase_meta import EXIOBASE_OVERRIDES

ROOT = Path(__file__).resolve().parents[1]
_CFG = load_config(repo_root=ROOT)

# Country-axis tables live IN this repo (class/country_axes/): they are
# METADATA, not data - small, hand-reviewed, and their history is the point,
# so git owns them and there is exactly one canonical copy. Nothing writes
# them into the shared data tree. paths.axis_work_dir may override for an
# out-of-tree experiment; it is unset by default.
OUT_DIR = get_path(_CFG, "paths.axis_work_dir") or (ROOT / "class" / "country_axes")
ROW_NAMES = {
    "WA": "RoW Asia and Pacific",
    "WL": "RoW America",
    "WE": "RoW Europe",
    "WF": "RoW Africa",
    "WM": "RoW Middle East",
}

# Near-miss countries promoted in the '_plus' variant. They have macro_db
# historic + at least one of (IEA, FAO, ICIO), and are useful EXIOBASE
# additions even though they miss one of the strict TIER_A pillars.
PLUS_PROMOTIONS = ["COD", "SDN", "STP", "GRL", "SSD", "XKX", "CUW"]


def _write_list(src: pd.DataFrame, tier_a_iso3: set[str], stem: str) -> None:
    """Build and write one country list given the TIER_A ISO3 set to use."""
    selected = src[src["ISO3"].isin(tier_a_iso3)].copy()
    e3 = selected[selected["in_current_EXIOBASE3"] == 1].sort_values("exiobase_name")
    new_candidates = selected[selected["in_current_EXIOBASE3"] == 0].sort_values(
        ["continent", "exiobase_name"]
    )

    rows: list[dict] = []
    for i, r in enumerate(pd.concat([e3, new_candidates]).itertuples(), start=1):
        rows.append({
            "order": i,
            "code": r.ISO3,
            "name": r.exiobase_name,
            "type": "country",
            "iso3": r.ISO3,
            "iso2": r.ISO2,
            "continent": r.continent,
            "exiobase3_current": int(r.in_current_EXIOBASE3),
            "in_macro_db_historic": int(r.in_macro_db_historic),
            "in_macro_db_nowcast": int(r.in_macro_db_nowcast),
            "in_IEA": int(r.in_IEA),
            "in_FAO": int(r.in_FAO),
            "in_ICIO": int(r.in_ICIO),
            "in_FIGARO": int(r.in_FIGARO),
            "in_GLORIA": int(r.in_GLORIA),
            "in_GTAP": int(r.in_GTAP),
            "in_BACI": int(r.in_BACI),
            "n_mrio": int(r.n_mrio),
            "un_summary_years": int(r.un_summary_years),
            "imf_weo_years": int(r.imf_weo_years),
            "members": "",
        })

    next_order = len(rows) + 1
    for row_code, row_name in ROW_NAMES.items():
        members_df = src[
            (src["raw_exio3_code"] == row_code)
            & ~src["ISO3"].isin(tier_a_iso3)
        ].sort_values("exiobase_name")
        member_iso3s = members_df["ISO3"].tolist()
        rows.append({
            "order": next_order,
            "code": row_code,
            "name": row_name,
            "type": "RoW",
            "iso3": "",
            "iso2": "",
            "continent": "",
            "exiobase3_current": 1,
            "in_macro_db_historic": 1,
            "in_macro_db_nowcast": 1,
            "in_IEA": 1,
            "in_FAO": 1,
            "in_ICIO": 0,
            "in_FIGARO": 0,
            "in_GLORIA": 0,
            "in_GTAP": 0,
            "in_BACI": 0,
            "n_mrio": 0,
            "un_summary_years": 0,
            "imf_weo_years": 0,
            "members": ",".join(member_iso3s),
        })
        next_order += 1

    out = pd.DataFrame(rows)
    csv = OUT_DIR / f"{stem}.csv"
    xlsx = OUT_DIR / f"{stem}.xlsx"
    out.to_csv(csv, index=False)
    try:
        out.to_excel(xlsx, index=False)
    except Exception as exc:  # noqa: BLE001 - xlsx is a convenience copy; the CSV is the output
        print(f"xlsx export failed: {exc}")

    countries = out[out["type"] == "country"]
    rows_only = out[out["type"] == "RoW"]
    total_row_members = rows_only["members"].apply(
        lambda s: len(s.split(",")) if s else 0
    ).sum()
    print(f"Wrote {len(out)} rows to {csv}")
    print(f"  Individual countries: {len(countries)} "
          f"(EXIOBASE3: {countries['exiobase3_current'].sum()}, "
          f"new: {(countries['exiobase3_current'] == 0).sum()})")
    print(f"  RoW buckets: {len(rows_only)} pooling {total_row_members} countries")
    for _, r in rows_only.iterrows():
        n = len(r["members"].split(",")) if r["members"] else 0
        print(f"    {r['code']} {r['name']:<25} {n:>3} members")
    print()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src = pd.read_csv(
        OUT_DIR / "extended_exiobase_candidates.csv", keep_default_na=False,
    )
    cc = coco.CountryConverter()

    # Apply EXIOBASE_OVERRIDES to names for canonical EXIOBASE output
    src["exiobase_name"] = src["name_short"].apply(
        lambda n: EXIOBASE_OVERRIDES.get(n, n)
    )
    # cc.data has EXIO3 codes for every country (the RoW bucket assignment).
    # The matrix earlier removed those; recompute here.
    iso_to_exio3 = dict(zip(cc.data["ISO3"], cc.data["EXIO3"]))
    iso_to_exio3_3l = dict(zip(cc.data["ISO3"], cc.data["EXIO3_3L"]))
    src["raw_exio3_code"] = src["ISO3"].map(iso_to_exio3)
    src["raw_exio3_3l"] = src["ISO3"].map(iso_to_exio3_3l)

    tier_a_iso3 = set(
        src[src["TIER"] == "TIER_A_full_coverage"]["ISO3"].tolist()
    )

    print("=== exiobase_rx1 (strict TIER_A) ===")
    _write_list(src, tier_a_iso3, "exiobase_rx1")

    plus_iso3 = tier_a_iso3 | set(PLUS_PROMOTIONS)
    missing = set(PLUS_PROMOTIONS) - set(src["ISO3"])
    if missing:
        print(f"WARNING: plus promotions not in candidates: {sorted(missing)}")
    print(f"=== exiobase_rx2 (+{len(PLUS_PROMOTIONS)} promotions: "
          f"{', '.join(PLUS_PROMOTIONS)}) ===")
    _write_list(src, plus_iso3, "exiobase_rx2")

    # Annotate the candidates CSV with rx1 / rx2 membership flags so the
    # candidate table records the axis assignments alongside the raw flags.
    src_full = pd.read_csv(
        OUT_DIR / "extended_exiobase_candidates.csv", keep_default_na=False,
    )
    src_full["in_rx1"] = src_full["ISO3"].isin(tier_a_iso3).astype(int)
    src_full["in_rx2"] = src_full["ISO3"].isin(plus_iso3).astype(int)
    src_full.to_csv(OUT_DIR / "extended_exiobase_candidates.csv", index=False)
    try:
        src_full.to_excel(
            OUT_DIR / "extended_exiobase_candidates.xlsx", index=False,
        )
    except Exception as exc:  # noqa: BLE001 - xlsx is a convenience copy; the CSV is the output
        print(f"candidates xlsx update failed: {exc}")
    print(f"Updated candidates CSV with in_rx1 ({src_full['in_rx1'].sum()}) "
          f"and in_rx2 ({src_full['in_rx2'].sum()}) columns.")


if __name__ == "__main__":
    main()
