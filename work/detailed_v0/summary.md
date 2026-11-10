# Detailed EXIOBASE classification, draft v0

Status: DRAFT v0, 2026-11-10. Built by `scripts/build.py` (with `refs.py`, `nace_isic.py`). Not committed.
Plan: `docs/detailed_classification_plan.md` (sections 3, 4, 6).

## Files

| File | Rows | Content |
|---|---|---|
| `industries_v0.csv` | 733 | industry leaves, NACE Rev 2.1 based codes |
| `products_v0.csv` | 1,397 | product leaves, CPA 2.2 based codes (14 CPC-coded, prefix `c`) |

Revision after review: the first pass had 785 industry and 1,415 product leaves (153 exio3-boundary
industry splits). The boundary rule below reduced this to 733 / 1,397 (66 exio3-boundary splits).

## Reference data used (and where it came from)

- NACE Rev 2.1 structure: Eurostat SDMX codelist `ESTAT/NACE_R2_1` (dissemination API, TSV),
  651 classes (sections A-V).
- CPA 2.2 structure: Eurostat SDMX codelist `ESTAT/CPA2_2`.
- NACE 2.1 to NACE 2, CPA 2.2 to CPA 2.1, CPA 2.2 to HS 2022: Eurostat ShowVoc download service
  (projects "NACE 2.1" and "CPA 2.2").
- These downloads are in the session scratchpad (`...\scratchpad\dl_nace\`), not in the repo. Phase 0
  of the plan should store them properly.
- ISIC Rev 5 structure, ISIC 4 to 5 official table (UNSD, 17 Jan 2025), CPC 3.0 structure: scratchpad `dl\`.
- `D:\indecol\data\suts\processed\concordances\`: ISIC4 to NACE2, ISIC4 to CPC 2.1, CPC 2.1 to HS 2017,
  CPC 2.1 structure.
- EXIOBASE: `class/exio3class.xlsx`; `00-concordances/concordances/` nace2, hs1996 and fao to
  exiobase3p, exiobase3p to exiobase3i, ENCORE isic5 to exiobase3i.
- Domain: FAO SUA + QCL item code lists, `01-fao_balance/aux_data/Primary_production.csv`,
  `energy-extensions` IEA_internal.xlsx and IEA_products_MRIO_products.xlsx, PV `commodity_to_exio.csv`
  and `classification_reference.csv`.

## Counts

### Industry leaves by NACE 2.1 section and tier

| Section | A | B | C | D | Total |
|---|---|---|---|---|---|
| A | 31 | 0 | 0 | 16 | 47 |
| B | 18 | 2 | 0 | 0 | 20 |
| C | 68 | 190 | 0 | 0 | 258 |
| D | 24 | 0 | 0 | 7 | 31 |
| E | 10 | 0 | 2 | 23 | 35 |
| F | 0 | 0 | 1 | 25 | 26 |
| G | 0 | 0 | 0 | 83 | 83 |
| H | 0 | 0 | 0 | 30 | 30 |
| I | 0 | 0 | 0 | 11 | 11 |
| J | 0 | 0 | 0 | 15 | 15 |
| K | 0 | 0 | 0 | 9 | 9 |
| L | 0 | 0 | 0 | 20 | 20 |
| M | 0 | 0 | 0 | 5 | 5 |
| N | 0 | 0 | 1 | 21 | 22 |
| O | 0 | 0 | 0 | 32 | 32 |
| P | 0 | 0 | 0 | 9 | 9 |
| Q | 0 | 0 | 0 | 12 | 12 |
| R | 0 | 0 | 0 | 20 | 20 |
| S | 0 | 0 | 1 | 19 | 20 |
| T | 0 | 0 | 0 | 24 | 24 |
| U | 0 | 0 | 1 | 2 | 3 |
| V | 0 | 0 | 1 | 0 | 1 |
| Total | 151 | 192 | 7 | 383 | 733 |

Split reasons: technology 25, route 16, product-stage 5, exio3-boundary 66, none 621.

EXIO3 industry mapping basis: official_chain 525, manual 176, encore 16, ambiguous 16.
All 163 EXIO3 industries and all 200 EXIO3 products are reached by at least one leaf.

### Product leaves by domain and tier

| Domain | A | B | D | Total |
|---|---|---|---|---|
| FAO (crops, livestock, processed food) | 308 | 0 | 0 | 308 |
| IEA (energy carriers, electricity by technology, gas, heat) | 62 | 0 | 9 | 71 |
| PV (ores, minerals, metal stages and routes) | 70 | 5 | 0 | 75 |
| PRODCOM-derived CPA 6-digit (divisions 20, 23, 24) | 85 | 209 | 0 | 294 |
| Waste and secondary materials (EXIO3 p90, .w, p37) | 10 | 6 | 20 | 36 |
| Generic (CPA 2.2 class, coarse) | 0 | 236 | 377 | 613 |
| Total | 535 | 456 | 406 | 1,397 |

Product leaves by section of their code: A 185, B 62, C 724, D 31, E 39, F-V 361 (one or a few per
class), CPC-coded 14. Products with no EXIO3 product (ambiguous): 31 (30 generic, 1 electricity storage).

## Rules used (codes are generated only by these rules)

1. Industry code = NACE 2.1 class (`dd.dd`). If a class has more than one leaf, every leaf gets a
   lowercase suffix `.a, .b, ...`, contiguous, in build order (deliberate splits first).
2. Product code = lowest CPA 2.2 node containing all CPA subcategories of the leaf (subcategory,
   category or class). If several leaves share a node, suffixes `.a, .b, ...` (residual leaves last).
   If a leaf has no CPA link, code = `c` + CPC 2.1 code. Products without a CPA subcategory (refinery
   feedstocks, other hydrocarbons, bottles for re-use, manure treatment, EXIO3 .w products) take the
   CPA class as base plus a suffix.
3. NACE 2.1 to ISIC 5: exact title match (305 classes), NACE group title equals an ISIC 5 class title
   (120), single ISIC 5 class in the group, NACE2-ISIC4-ISIC5 chain, else a manual assignment (about
   110 classes, `ISIC5_MANUAL` in build.py). 37 leaves sit in NACE 2.1 classes that span several
   ISIC 5 classes; `isic5_class` is then a semicolon list. No official NACE 2.1 to ISIC 5 table was
   among the files fetched, so this column is derived.
4. isic4_classes: official ISIC 4 to 5 rows of the ISIC 5 class, restricted to ISIC 4 classes that also
   reach the NACE 2.1 class through NACE 2.1 to NACE 2 and ISIC 4 to NACE 2.
5. official_chain: NACE 2.1 class to NACE 2 (Eurostat) to EXIO3 product (`nace2_exiobase3p.csv`, class
   or group rows) to EXIO3 industry (`exiobase3p_exiobase3i.csv`). EXIO3 `.w` industries and
   i37/i37.w.1 are dropped from chain sets and placed explicitly. Within a class, CPA subcategories
   are assigned by CPA 2.2 to HS 2022 to the EXIO3 HS 1996 map by 6-digit code identity (HS version
   changes ignored).
6. Boundary rule (review fix): a class is split by EXIO3 industry only if (a) some of its products map
   to an EXIO3 product whose industry differs from the class's dominant EXIO3 industry, (b) that
   industry is in the class's NACE 2 chain set, and (c) for generic and PRODCOM products, the minor
   mapping covers at least 2 CPA subcategories and at least 20% of the class. FAO, IEA and PV products
   count as separating data without the size test. Otherwise the class is one leaf mapped to its
   dominant EXIO3 industry (weighted by FAO items or CPA subcategories) and minor mappings go to
   `notes`. The same rule governs product splits of CPA classes.
7. manual: domain splits (FAO, IEA, PV), EXIO3 .w placements, waste treatment, and service or mixed
   classes in `MANUAL_P` (e.g. agents 46.1x to p51). encore: no chain result, unique ENCORE ISIC 5
   target. ambiguous: neither.
8. FAO leaves: SUA and QCL item lists (union, 506 items with CPC, FAO aggregates `F....` excluded),
   grouped by CPC 2.1 subclass and EXIO3 product (308 leaves). EXIO3 product from
   `Primary_production.csv`, then a manual CPC-prefix rule for livestock and slaughter by-products,
   then `fao_exiobase3p.csv` name match, then the HS chain. CPA via CPC 2.1 to HS 2017 to CPA 2.2
   (6-digit identity), restricted to CPA divisions 01-03 for primary CPC items.
9. cpc21: FAO CPC for FAO leaves; otherwise CPA to HS to CPC 2.1, shown as one code, up to three
   codes, or their common CPC node; services via the official ISIC 4 to CPC 2.1 table. cpc30: filled
   only where the CPC 2.1 subclass code exists in CPC 3.0 with an identical title (720 products); a
   heuristic, not a correspondence.
10. Anchors and tier: FAO, IEA, PV give tier A; PRODCOM gives B. Generic leaves in sections B and C get
    PRODCOM by rule (PRODCOM extends CPA B-C), not checked code by code. Other generic leaves get
    SUT-64; tier C only if the leaf is the only one in its division, else D. SUT-detailed anchors have
    not been assessed (no leaf carries them yet).

## Deliberate splits

- Electricity: 35.11 coal, gas, oil, non-renewable waste (each electricity-only and CHP), nuclear,
  other sources; 35.12 hydro, wind, solar PV, solar thermal, tide, geothermal, biomass and renewable
  waste (electricity-only and CHP). Mapped to i40.11.a-l; the biomass and waste straddle is split by
  ISIC5 3511/3512. 35.13 transmission (i40.12), 35.14 distribution and 35.15 trade (i40.13), 35.40
  brokers split electricity / gas. Heat-only plants are 35.30; CHP leaves supply electricity and heat.
- Fuels: 19.10 coke ovens; 19.20 refineries (multi-product), patent fuel plants and BKB plants (mapped
  to i10 as in EXIO3), coal liquefaction / GTL (i11.c); 35.21 gas works, biogas, recovered gases;
  20.14 charcoal; 20.51 liquid biofuels.
- Steel 24.10: BOF, OHF, EAF (i27.a.w), ferro-alloys. DRI is not separated in the PV data, so no leaf.
- Non-ferrous 24.41, 24.43, 24.44, 24.45: primary vs secondary (i27.x / i27.x.w); 24.42 alumina
  refining, primary smelting, secondary aluminium. 07.29 ores split by the six EXIO3 ore codes.
- Cement 23.51: clinker, grinding, ash re-processing (i26.d.w). Fertilisers 20.15: N, P/K/compound,
  ammonia.

## Pending

- NACE 2.1 and CPA 2.2 were fetched (see above); the NACE 2.1 to ISIC 5 link is derived, not official.
- CPC 2.1 to CPC 3.0: no official table; `cpc30` heuristic only.
- Partition tests (plan principle 7) not implemented; product leaves are not checked to partition
  CPC 2.1 subclasses.
- FAOSTAT forestry and FishStat not integrated; divisions 02 and 03 are coarse CPA leaves.
- IEA WBIG detailed products (hydrogen, ammonia, e-fuels) not scanned.
- SUT-detailed coverage (StatCan, Japan, BEA, Korea) not assessed.

## Top 10 open issues

1. 16 industry leaves have no EXIO3 map (01.50, 01.61, 01.63, 01.70, 09.10, 09.90, 33.13, 33.20,
   35.16, 38.11, 38.12, 38.33, 39.00, 64.21, 79.90, 82.40); EXIO3 has no counterpart for several.
2. NACE 2.1 to ISIC 5 is derived; about 110 manual assignments and 37 multi-ISIC5 classes need
   checking against explanatory notes or an official table.
3. HS 2022 to HS 1996 is code identity only; manufacturing product maps rely on it.
4. By-product supply: recovered gases supplied by 35.21 (EXIO3-consistent) but physically from coke
   ovens and steelworks; gas coke and coal tar listed with gas works / coke ovens (EXIO3: i23.2);
   NGL from 06.20.
5. Route products (secondary steel and non-ferrous metals) share CPA codes with the primary route;
   downstream semis and rolled products all map to the primary EXIO3 code.
6. Waste: incineration split into 38.22 (energy recovery) and 38.31 (without); biogas under 38.22,
   composting under 38.23; overlap with electricity from waste (i40.11.g); hazardous vs
   non-hazardous (ISIC5 3821/3822) not separated.
7. EXIO3 n:1 straddles kept and flagged: bio-jet kerosene into p23.20.d, peat products into p10.h,
   PV gypsum (NACE chain p14.1 used instead of PV p26.d), PV ammonia into p24.d.
8. 14 FAO leaves have no CPA link (CPC-coded, e.g. raw milk); placed via the ISIC4-CPC table or the
   EXIO3 chain; raw milk of sheep and goats folds into the 01.45 leaf mapped to i01.l.
9. Manual placement of EXIO3 .w industries (i20.w in 16.21, i26.a.w in 23.13, i45.w in 38.21,
   manure treatment in 01.62).
10. Tier D dominates services (383 industry leaves); generic service products sit at NACE class
    level without a verified data source below the division.

## Options A and B (added 2026-11-10, scripts/options.py)

Build order: `python -I scripts/build.py && python -I scripts/options.py`.

- Option A keeps every leaf: 734 industry leaves, 1,398 product leaves.
- Option B merges tier D leaves to (NACE division x EXIOBASE 3 code), giving 497 industry and 1,159 product leaves. Columns `option_b_code` and `option_b_name` record the merged leaf for every row; unmerged rows carry their own code.
- Construction (41-43), transport and storage (49-53) and data processing / hosting (63) keep full detail in both options, at Richard's request.
- Building construction 41.00 is split into residential (41.00.a, CPA 41.00.1 and 41.00.3) and non-residential (41.00.b, CPA 41.00.2 and 41.00.4).
- A tier now means the data that separates a leaf from its siblings. Rail and road passenger classes are tier D even though IEA covers the mode totals. Air passenger and freight are tier A (World Bank WDI), road freight tier B (Eurostat road_go_ta_tott), water tier B (OECD maritime, UNCTAD fleet), pipeline tier A (IEA), buildings and civil engineering tier C (detailed SUTs), data processing and hosting 63.10 tier C (ABS IOPC 59210020, BEA 518200).
- Candidate sources not held: Eurostat rail_pa_total / rail_go_total, ITF transport statistics, Eurostat STS and SBS for construction, IEA data-centre electricity estimates.
- `refs/` holds the reference downloads (NACE 2.1, CPA 2.2, ISIC 5, CPC 3.0 and correspondences) so the build no longer depends on a session scratchpad.

## Tier upgrades from sources fetched 2026-11-10

Sources (all under D:\data\00-sources, fetched by scripts/fetch_sources.py): Eurostat rail_pa_total, rail_go_total, sts_copr_a, sbs_ovw_act (NACE Rev 2 class level, 2021-2024), sbs_na_con_r2, sbs_na_1a_se_r2; ITF DF_TRENDSFREIGHT, DF_STPASS, DF_STFREIGHT; Ireland CSO MEC02 (data-centre electricity). IEA Energy and AI data needs an IEA account and is MANUAL.

- Eurostat SBS rule: a NACE 2.1 class is tier B if it is the main destination of a NACE Rev 2 class that SBS reports for at least 20 countries (main destination = same code, else the only class fed, else the only non-prefixed correspondence row). Sub-splits (e.g. 41.00.a/b) are never upgraded by SBS.
- Physical upgrades: rail freight 49.20 (ITF 54 countries, Eurostat), road freight 49.41 (ITF 53), inland freight 50.40 (ITF 30) to tier B. Rail passenger-km (ITF 50, Eurostat 38) is attached to 49.11/49.12 but does not separate heavy from other passenger rail.
- sts_copr_a gives buildings vs civil engineering as indices only, so it supports trends, not levels.
- Still tier D among the kept sectors: 43.23, 43.35, 43.42, 43.50, 43.60, 43.91, 49.12, 49.32, 49.33, 49.34, 52.25, 52.26, 52.31, 52.32, 53.10, 53.20, 53.30 (NACE 2.1 classes carved out of shared NACE Rev 2 classes, or SBS coverage under 20 countries).
