"""Build the candidate country list for an expanded EXIOBASE.

Finds the largest set of INDIVIDUAL COUNTRIES that have actual data in
the data sources EXIOBASE will need to feed:

  - macro_db (UN SNA Main Aggregates summary VA + IMF WEO)
  - IEA Energy Balances (per `world_energy_balances` v2025)
  - FAO Production / Trade (per `fao/data/Production_*` CSVs)

And cross-checks against MRIO / trade databases for compatibility:

  - OECD ICIO 2025
  - Eurostat FIGARO 2025
  - GLORIA
  - GTAP 11
  - BACI (CEPII bilateral trade, HS96; vintage pinned in config.yaml)

macro_db coverage is split into two flags:

  - in_macro_db_historic : >=15 years of UN SNA Main Aggregates summary VA
  - in_macro_db_nowcast  : >=15 years of IMF WEO NGDPD

Historic is the load-bearing criterion (drives TIER_A); nowcast is optional
(needed only for projection years). Countries with strong UN history but
no IMF WEO (Cuba, North Korea, etc.) qualify for TIER_A.

Output: <paths.axis_work_dir>/extended_exiobase_candidates.csv
Highlights three tiers:
  TIER_A : all 3 essential sources (macro_db + IEA + FAO) covered
  TIER_B : 2 of 3 essential sources covered
  TIER_C : 1 of 3 essential sources covered (probably RoW-bucket material)

The current EXIOBASE3 (44 countries) is flagged as a subset for reference.

Step 2 of 3 in the rx1 / rx2 derivation. Moved here from 02-macro_db on
2026-08-06. The IEA / FAO / BACI reads are all straight off external files;
the only macro_db input is the published per-country coverage table
(``paths.macro_db_coverage_csv``), which macro_db owns because only its
parsers can measure UN SNA / WEO year coverage.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import country_converter as coco
import pandas as pd
from io_utils.config import get_path, load_config

from exiobase_meta import read_country_axis

ROOT = Path(__file__).resolve().parents[1]
_CFG = load_config(repo_root=ROOT)

# Country-axis tables live IN this repo (class/country_axes/): they are
# METADATA, not data - small, hand-reviewed, and their history is the point,
# so git owns them and there is exactly one canonical copy. Nothing writes
# them into the shared data tree. paths.axis_work_dir may override for an
# out-of-tree experiment; it is unset by default.
OUT_DIR = get_path(_CFG, "paths.axis_work_dir") or (ROOT / "class" / "country_axes")
BACI_FILE = get_path(_CFG, "paths.baci_file")
FAO_FILE = get_path(_CFG, "paths.fao_production_csv")
IEA_FILE = get_path(_CFG, "paths.iea_wbal_file")
MACRO_DB_COVERAGE_CSV = get_path(_CFG, "paths.macro_db_coverage_csv")

# IEA country codes that are aggregates/regions (drop from individual list)
_IEA_AGGREGATES = {
    "AFRICA_UN", "AMERICAS_UN", "ASEAN", "ASIA_UN", "EUROPE_UN", "OCEANIA",
    "WORLD", "WORLDAV", "WORLDMAR", "OECDAM", "OECDEUR", "OECDPAC",
    "OECDTOT", "NMOECD", "MEMOECD", "ESTONIANC", "MEMBERIA",
    "TOTASOCEAN", "NONOECDAM", "NONOECDAS", "NONOECDEU", "TOTAFRICA",
    "MIDDLEEAST", "EU28", "EU27_2020", "G7", "G20", "OPEC", "G7_OECDPLUS",
    "WBALANCE", "NMIBA", "IBNET",
}

# Manual ISO3 mapping for IEA codes that cc doesn't recognise
_IEA_TO_ISO3: dict[str, str] = {
    "BOSNIAHERZ": "BIH",
    "BRUNEI": "BRN",
    "BURKINAFASO": "BFA",
    "CDIVOIRE": "CIV",
    "CONGOREP": "COG",
    "COSTARIC": "CRI",
    "DOMINICANR": "DOM",
    "DRCONGO": "COD",
    "EQGUINEA": "GNQ",
    "ELSALVADOR": "SLV",
    "GUATEMALA": "GTM",
    "HAITI": "HTI",
    "HONDURAS": "HND",
    "HONGKONG": "HKG",
    "IRAN": "IRN",
    "KOREA": "KOR",
    "KOREADPR": "PRK",
    "KOSOVO": "XKX",
    "KYRGYZSTAN": "KGZ",
    "LAOS": "LAO",
    "MOLDOVA": "MDA",
    "MOROCCO": "MAR",
    "MOZAMBIQUE": "MOZ",
    "MYANMAR": "MMR",
    "NETHLAND": "NLD",
    "NIGER": "NER",
    "PHILIPPINES": "PHL",
    "RUSSIA": "RUS",
    "SAUDIARABI": "SAU",
    "SINGAPORE": "SGP",
    "SLOVAK": "SVK",
    "SLOVENIA": "SVN",
    "SOUTHAFRIC": "ZAF",
    "SSUDAN": "SSD",
    "SRILANKA": "LKA",
    "SYRIA": "SYR",
    "TAIPEI": "TWN",
    "TANZANIA": "TZA",
    "TRINIDAD": "TTO",
    "TURKIYE": "TUR",
    "TURKMENIST": "TKM",
    "UAE": "ARE",
    "UK": "GBR",
    "USA": "USA",
    "UZBEKISTAN": "UZB",
    "VENEZUELA": "VEN",
    "VIETNAM": "VNM",
    "YEMEN": "YEM",
}


def get_iea_countries() -> set[str]:
    """Return ISO3 codes of individual IEA WBAL countries."""
    countries: set[str] = set()
    with zipfile.ZipFile(IEA_FILE) as zf, zf.open("WORLDBAL.TXT") as f:
        for raw in f:
            line = raw.decode("latin-1", errors="replace")
            code = line[:30].strip()
            if code and code not in _IEA_AGGREGATES:
                countries.add(code)
    # Convert codes to ISO3
    cc = coco.CountryConverter()
    iso3: set[str] = set()
    unmatched: list[str] = []
    for code in countries:
        if code in _IEA_TO_ISO3:
            iso3.add(_IEA_TO_ISO3[code])
            continue
        title = code.title()  # title-case helps cc recognise it
        res = cc.convert(title, src="regex", to="ISO3", not_found=None)
        if res and res != "not found" and not isinstance(res, list):
            iso3.add(res)
        else:
            unmatched.append(code)
    if unmatched:
        print(f"  [IEA] unmatched codes: {sorted(unmatched)}")
    return iso3


def get_fao_countries(min_years: int = 15) -> set[str]:
    """Return ISO3 codes of individual FAO Production reporters with >=min_years.

    Uses utf-8 encoding (FAO 2025 vintage). Filter for regional aggregates
    matches whole-word "Africa", "Asia" etc., so "South Africa" is kept.
    """
    df = pd.read_csv(
        FAO_FILE, encoding="utf-8",
        usecols=["Area Code", "Area Code (M49)", "Area"]
        + [f"Y{y}" for y in range(2000, 2024)],
    )
    year_cols = [c for c in df.columns if c.startswith("Y")]
    years_per_area = (
        df.groupby("Area")[year_cols]
        .apply(lambda g: g.notna().any(axis=0).sum())
    )
    qualifying = set(years_per_area[years_per_area >= min_years].index.tolist())
    cc = coco.CountryConverter()
    # FAO Area Codes >= 5000 are regional aggregates; <5000 are individual
    # countries/territories. Use that as the primary filter; cross-check
    # with cc.convert for unrecognised entries.
    area_codes = df.set_index("Area")["Area Code"].to_dict()
    # Manual mappings for FAO names cc doesn't resolve cleanly
    manual_mapping = {
        "China, Taiwan Province of": "TWN",
        "China, mainland": "CHN",
        "China, Hong Kong SAR": "HKG",
        "China, Macao SAR": "MAC",
        "United Kingdom of Great Britain and Northern Ireland": "GBR",
        "Türkiye": "TUR",
    }
    iso3: set[str] = set()
    unmatched: list[str] = []
    for area in qualifying:
        code = area_codes.get(area)
        if code is not None and code >= 5000:
            continue  # regional aggregate
        if area in manual_mapping:
            iso3.add(manual_mapping[area])
            continue
        res = cc.convert(area, to="ISO3", not_found=None)
        if res and res != "not found" and not isinstance(res, list):
            iso3.add(res)
        else:
            unmatched.append(area)
    if unmatched:
        print(f"  [FAO] unmatched areas: {sorted(unmatched)[:15]} (and "
              f"{max(0, len(unmatched)-15)} more)")
    return iso3


def get_macro_db_countries(min_years: int = 15) -> tuple[set[str], set[str]]:
    """Return (historic, nowcast) ISO3 sets.

    historic: countries with >=min_years of UN SNA Main Aggregates summary VA
    nowcast : countries with >=min_years of IMF WEO NGDPD

    Historic is the load-bearing flag; nowcast extends to projection years.

    Read from the coverage table macro_db publishes. We deliberately do NOT
    fall back to recomputing this from macro_db's output parquet: that would
    make this repo import macro_db and invert the dependency (macro_db
    depends on exiobase_meta, not the other way round).
    """
    fp = MACRO_DB_COVERAGE_CSV
    if not fp.exists():
        raise FileNotFoundError(
            f"Missing macro_db coverage table {fp}. Produce it by running "
            "02-macro_db/scripts/count_data_coverage.py, which needs "
            "country_coverage_matrix.csv from step 1 of this chain."
        )
    df = pd.read_csv(fp)
    historic = set(
        df[df["un_summary_years"] >= min_years]["ISO3"].dropna().tolist()
    )
    nowcast = set(
        df[df["imf_weo_years"] >= min_years]["ISO3"].dropna().tolist()
    )
    return historic, nowcast


def get_baci_countries(min_years: int = 15) -> set[str]:
    """ISO3 codes of BACI exporters with finite trade in >=min_years years."""
    if not BACI_FILE.exists():
        print(f"  [BACI] file not found: {BACI_FILE}")
        return set()
    years_per_code: dict[int, int] = {}
    iso3_lookup: dict[int, str] = {}
    with zipfile.ZipFile(BACI_FILE) as zf:
        # Vintage-agnostic: the codes file is country_codes_V<rel>.csv.
        codes_name = next(
            n for n in zf.namelist() if n.startswith("country_codes_")
        )
        with zf.open(codes_name) as f:
            cc_df = pd.read_csv(f)
        iso3_lookup = dict(
            zip(cc_df["country_code"], cc_df["country_iso3"].astype(str))
        )
        year_files = sorted(
            n for n in zf.namelist() if n.startswith("BACI_HS96_Y")
        )
        for name in year_files:
            with zf.open(name) as f:
                df = pd.read_csv(f, usecols=["i", "v"])
            exporters = df[df["v"] > 0]["i"].unique()
            for code in exporters:
                years_per_code[code] = years_per_code.get(code, 0) + 1
    iso3: set[str] = set()
    for code, n_years in years_per_code.items():
        if n_years < min_years:
            continue
        iso = iso3_lookup.get(code, "")
        if iso and iso.lower() not in ("nan", "n/a"):
            iso3.add(iso)
    return iso3


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading IEA country list...")
    iea = get_iea_countries()
    print(f"  -> {len(iea)} individual countries")

    print("Loading FAO Production reporters (>=15y)...")
    fao = get_fao_countries(min_years=15)
    print(f"  -> {len(fao)} countries")

    print("Loading macro_db coverage (UN MAA / WEO >=15y)...")
    macro_db_hist, macro_db_now = get_macro_db_countries(min_years=15)
    print(f"  -> {len(macro_db_hist)} historic (UN MAA), "
          f"{len(macro_db_now)} nowcast (IMF WEO)")

    print("Loading BACI exporter coverage (>=15y)...")
    baci = get_baci_countries(min_years=15)
    print(f"  -> {len(baci)} countries")

    # TIER_A driven by HISTORIC data only (nowcast is bonus, not required)
    essential = macro_db_hist & iea & fao
    print(f"\nHistoric MacroDB intersect IEA intersect FAO = {len(essential)} countries")

    # Build the full membership table. Use keep_default_na=False so empty
    # strings in the CSV stay as "" instead of becoming NaN (which would
    # corrupt the "in this database" boolean checks below).
    base = pd.read_csv(MACRO_DB_COVERAGE_CSV, keep_default_na=False)
    # Restrict to rows with ISO3 (drop tiny territories without ISO3)
    base = base[base["ISO3"].astype(str).str.strip() != ""].copy()

    base["in_macro_db_historic"] = base["ISO3"].isin(macro_db_hist).astype(int)
    base["in_macro_db_nowcast"] = base["ISO3"].isin(macro_db_now).astype(int)
    base["in_IEA"] = base["ISO3"].isin(iea).astype(int)
    base["in_FAO"] = base["ISO3"].isin(fao).astype(int)
    base["in_BACI"] = base["ISO3"].isin(baci).astype(int)
    # Already have OECD_ICIO, FIGARO, GTAP11, GLORIA, EXIO3 columns
    def _present(s: pd.Series) -> pd.Series:
        return (
            (s.astype(str).str.strip() != "")
            & (s.astype(str).str.strip().str.lower() != "nan")
        ).astype(int)

    base["in_ICIO"] = _present(base["OECD_ICIO"])
    base["in_FIGARO"] = _present(base["FIGARO"])
    base["in_GLORIA"] = _present(base["GLORIA"])
    base["in_GTAP"] = _present(base["GTAP11"])
    base["in_EXIO3"] = _present(base["EXIO3"])

    # Tier classification based on the 3 essential HISTORIC sources
    essential_cols = ["in_macro_db_historic", "in_IEA", "in_FAO"]
    base["n_essential"] = base[essential_cols].sum(axis=1)
    base["TIER"] = base["n_essential"].map({
        3: "TIER_A_full_coverage",
        2: "TIER_B_partial_coverage",
        1: "TIER_C_minimal_coverage",
        0: "absent",
    })

    # Total MRIO coverage (Eora dropped; BACI added as a trade comparator)
    mrio_cols = ["in_ICIO", "in_FIGARO", "in_GLORIA", "in_GTAP",
                 "in_EXIO3", "in_BACI"]
    base["n_mrio"] = base[mrio_cols].sum(axis=1)

    # Build the candidates table sorted by quality
    out_cols = [
        "ISO3", "ISO2", "name_short", "continent", "TIER",
        "n_essential", "n_mrio",
        "in_macro_db_historic", "in_macro_db_nowcast",
        "in_IEA", "in_FAO",
        "in_EXIO3", "in_ICIO", "in_FIGARO", "in_GLORIA", "in_GTAP", "in_BACI",
        "un_summary_years", "imf_weo_years",
        "un_rev4_detail_years", "fao_rfb_years",
        "EXIO3", "EXIO3_3L",  # current EXIOBASE3 bucket assignment
    ]
    base = base[out_cols].sort_values(
        ["n_essential", "n_mrio", "name_short"],
        ascending=[False, False, True],
    )

    # EXIOBASE3 membership straight off the published axis, which already
    # carries ISO3 per country. The previous macro_db version round-tripped
    # names through cc and then patched up EXIOBASE_OVERRIDES collisions by
    # hand; reading the axis skips that entirely.
    e3 = read_country_axis("exiobase3").table
    e3_iso3 = {
        str(v).strip() for v in e3.loc[e3["type"] == "country", "iso3"]
        if str(v).strip()
    }
    base["in_current_EXIOBASE3"] = base["ISO3"].isin(e3_iso3).astype(int)

    csv = OUT_DIR / "extended_exiobase_candidates.csv"
    xlsx = OUT_DIR / "extended_exiobase_candidates.xlsx"
    base.to_csv(csv, index=False)
    try:
        base.to_excel(xlsx, index=False)
    except Exception as exc:  # noqa: BLE001 - xlsx is a convenience copy; the CSV is the output
        print(f"xlsx write failed: {exc}")

    print(f"\nWrote {len(base)} rows to {csv}\n")

    # Summary
    tier_counts = base["TIER"].value_counts()
    print("Tier breakdown:")
    for t in ["TIER_A_full_coverage", "TIER_B_partial_coverage",
              "TIER_C_minimal_coverage", "absent"]:
        if t in tier_counts.index:
            print(f"  {t:<32}: {tier_counts[t]:>3} countries")

    # TIER_A list
    tier_a = base[base["TIER"] == "TIER_A_full_coverage"]
    print(f"\nTIER_A (macro_db + IEA + FAO, n={len(tier_a)}):")
    not_e3 = tier_a[tier_a["in_current_EXIOBASE3"] == 0]
    in_e3 = tier_a[tier_a["in_current_EXIOBASE3"] == 1]
    print(f"  Already in EXIOBASE3 ({len(in_e3)} of 44):")
    print(f"    {sorted(in_e3['name_short'].tolist())}")
    print(f"\n  Candidates NOT yet in EXIOBASE3 ({len(not_e3)} extras):")
    for _, r in not_e3.iterrows():
        print(f"    {r['name_short']:<32} ({r['ISO3']:<3}, current RoW={r['EXIO3']})")


if __name__ == "__main__":
    main()
