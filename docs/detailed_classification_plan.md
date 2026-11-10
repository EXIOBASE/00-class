# Plan: a detailed EXIOBASE product and industry classification

Status: draft plan, 2026-11-10. Nothing has been built yet.

## 1. Goal

Build a new product and industry classification that is much more detailed
than EXIOBASE 3 (200 products, 163 industries). It should:

- carry the finest detail our data sources actually provide: FAO items,
  physical production volumes, IEA energy products and flows, and the most
  detailed national SUTs;
- be anchored on the international standards: ISIC / NACE for industries
  and CPC / CPA for products, with HS reachable through CPC;
- be ready for ISIC Rev 5 / NACE Rev 2.1 / CPC 3.0 now, rather than
  retrofitted later;
- nest cleanly into EXIOBASE 3, so every old result can be reproduced by
  aggregation.

## 2. What we have today (surveyed 2026-11-10)

### 2.1 Reference classifications

| Classification | Status | Size (counted from files) | Local copy |
|---|---|---|---|
| ISIC Rev 4 | in force | 419 classes | `D:\indecol\data\suts\processed\concordances\STRUCTURE_ISIC_Rev4.csv` |
| ISIC Rev 5 | adopted; UN publication in copyediting; structure, explanatory notes (xlsx dated 19 Aug 2026) and errata published | 22 sections, 87 divisions, 258 groups, 463 classes | session scratch download only; official Rev4-Rev5 table also at `D:\indecol\data\suts\raw\_concordances\global\unsd_isic4_to_isic5_correspondence.xlsx` |
| ISIC Rev4 to Rev5 | official UNSD, 17 Jan 2025, class level | 605 rows; 116 Rev 4 classes split, 54 Rev 5 classes are merges; most changes in section G (112 rows) | as above |
| CPC 2.1 | in force | 2,887 subclasses | `STRUCTURE_CPC_2.1.csv` (same folder) |
| CPC 3.0 | endorsed by UNSC March 2025; structure file dated 30 Jun 2025 | 2,877 subclasses | not held; no correspondence to CPC 2.1, HS or ISIC 5 published yet |
| NACE Rev 2.1 / CPA 2.2 | official (NACE 2.1 adopted 2023, CPA 2.2 applies from 2025) | not counted | not held; NACE 2 to 2.1 tables are on Eurostat ShowVoc |
| NACE Rev 2, CPA 2002 / 2008 | legacy | not counted | `STRUCTURE_NACE_Rev2.csv`; `D:\indecol\Projects\MRIOs\Classifications\Unprocessed\` |

Open point: I have not confirmed from an official Eurostat source when
national accounts switch to NACE Rev 2.1. This needs checking against
Delegated Regulation 2023/137 Article 2.

### 2.2 Detail by domain

**Agriculture, food, forestry, fish (FAO).** FAOSTAT carries CPC 2.1 codes
on every item: QCL production 312 items, SUA 485 items (primary plus
processed, the finest list), detailed trade 572 items, forestry 104 items
(no CPC column). FishStat gives ISSCAAP groups and species. Current EXIOBASE
mapping (`01-fao_balance/aux_data/Primary_production.csv`) covers only 183
primary items plus 43 processed items. For example, 94 items collapse into
`p01.d Vegetables, fruit, nuts`. There is no commodity tree or extraction
rate file, only a `Factor` column in `FAOSTAT_items.csv`.

**Energy (IEA).** The repos use 66 IEA products and 108 flows
(`energy-extensions/sources/concordances/IEA_internal.xlsx`) with matrix
concordances to the 200 products and 163 industries. WBAL v2025 only has 19
aggregate products. The detailed WBIG files (`D:\data\00-sources\iea\world_energy_balances\v2025\`)
have not been scanned, and `WBIG2.zip` is 22 bytes (broken). Known gaps:
- coal grades are merged;
- biofuels are spread over 20-60 non-energy products;
- municipal and industrial waste, renewable and not, are merged into waste treatment;
- bio-jet is merged into kerosene jet;
- other recovered gases are lumped with gas works gas;
- coke ovens, patent fuel, BKB and charcoal are one industry;
- CHP is not its own industry;
- no hydrogen, ammonia or e-fuels;
- four WBAL flows have no concordance (EFFELE, EFFELEHEAT, IRONSTL_SECTOR, LIQUEFAC).

**Mining, metals, minerals, chemicals (production volumes).** `01-production_volumes`
has a controlled vocabulary of 188 (commodity, sub_type) pairs, for example
steel by route and copper by ore, primary refined and secondary refined. It
also has 1,834 PRODCOM 8-digit codes linked through
`final/exio/classification_reference.csv`, which derive 452 CPA 2008 6-digit
codes. This feeds 39 of the 200 EXIOBASE products. Outside the EU/EFTA,
detail is mostly ISIC 2-digit (UNIDO). There is no HS, CPC or ISIC bridge.

**SUT / IO detail.** The most detailed full tables we hold:

| Table | Products | Industries |
|---|---|---|
| StatCan SUT 2022 | 473 | 220 |
| Japan basic 2020 | 445 | 391 |
| BEA 1997 benchmark | about 490 (by industry) | |
| BEA detail 2017 | 406 | 406 |
| Korea 2020 | 380 | 278 |
| Taiwan 2021 | 484 (input side only) | 163 |

The Japan production file `kokunai_seisan.xlsx` has 3,719 commodity rows.
National to ISIC 4 / CPC 2.1 / NACE 2 chains already exist in
`D:\indecol\data\suts\processed\concordances\`, flagged official, chained or
derived.

**Existing concordances to EXIOBASE.** These are in `00-concordances(-public)`:
HS1996, CPA2002, NACE2, NAICS2017, ISIC3, COICOP and FAO to EXIOBASE, all
hand-made. There are also third-party ENCORE ISIC 4 and ISIC 5 to
EXIOBASE-industry tables and about 40 NSI bridges. None of these carry
sub-EXIOBASE detail.

## 3. Design principles

1. **Two axes, both standard-anchored.**
   - The industry axis is built on ISIC Rev 5 classes (463), carrying the
     equivalent ISIC Rev 4 and NACE Rev 2.1 codes.
   - The product axis is built on CPC subclasses, carrying CPA 2.2 and,
     through CPC, HS.
   - Every node of the new tree is defined as a set of standard codes. It is
     never defined only by a name.
2. **Pivot on CPC 2.1 now, carry CPC 3.0 as a column.** FAO, HS and
   ISIC 4 already have official links to CPC 2.1, while CPC 3.0 has no
   published correspondences yet. Fill in CPC 3.0 when UNSD releases the
   CPC 2.1 to 3.0 table, and switch the pivot then.
3. **ISIC Rev 5 is the industry backbone from day one.** The official
   Rev 4 to Rev 5 table already exists, so we use it rather than waiting.
   Where Rev 4 classes split (116 cases), record the split explicitly so data
   that only exists in Rev 4 can still be allocated.
4. **Go below the standard only where it matters and data exists.** Split
   below ISIC class or CPC subclass only for technology or route
   differences that change environmental intensity. Examples are
   electricity by technology, steel by route (BOF / EAF / DRI), primary and
   secondary aluminium and copper, clinker and cement, and coke ovens versus
   patent fuel / BKB. Each such split must have at least one data source
   behind it.
5. **Every leaf has a data anchor and a tier.**
   - A: global physical data (FAO, IEA, USGS / BGS).
   - B: regional data (PRODCOM, a few national SUTs).
   - C: SUT-only for a handful of countries.
   - D: no data, so the leaf is split by proxy.

   The tier is stored, so later users know how much to trust each leaf.
6. **Strict nesting into EXIOBASE 3.** Every new product maps to exactly one
   of the 200 products, and every new industry to exactly one of the 163.
   Where an EXIOBASE 3 code cuts across the new tree (for example `Anthracite`
   receiving all hard coal), record the n:1 explicitly and flag it.
7. **Partition tests.** The product leaves must partition the full CPC
   subclass list, with each subclass in exactly one leaf. The industry
   leaves must partition the ISIC 5 classes, each in one leaf or explicitly
   split. Tests enforce this, in the same style as
   `tests/test_meta_consistency.py`.
8. **Repo boundary unchanged.** The new vocabularies and the new
   product-industry structure live here in `00-class`. The mappings from
   source codes (FAO, IEA, PRODCOM, USGS / BGS, national SUT, HS) to the new
   leaves live in `00-concordances-public`.

## 4. Building the detail, domain by domain

| Domain | Leaf source | Likely depth | Notes |
|---|---|---|---|
| Crops, livestock, processed food | FAO SUA (485) and QCL (312) items, already CPC 2.1 coded | close to FAO item level for primary; processed items grouped where SUA is too fine to have economic data | needs a commodity tree (primary to processed) for the industry side; FishStat ISSCAAP for fish; forestry needs a CPC mapping built |
| Energy products | IEA product list (66 now; check WBIG v2025 for hydrogen, ammonia, e-fuels) | IEA product level, with CPC / HS attached | separate bio and fossil fractions (gasoline, diesel, jet); separate waste renewable / non-renewable |
| Energy industries | IEA transformation and own-use flows plus electricity by technology | split coke ovens, patent fuel / BKB, blast furnace, gas works, refineries, petrochemical feedstock, liquefaction / GTL, CHP vs electricity-only vs heat-only | the industry side is where IEA adds most value |
| Mining and metals | PV (commodity, sub_type) vocabulary (188 pairs), USGS / BGS | ore, concentrate, primary refined, secondary refined, by metal | the same metal at different stages becomes different products |
| Chemicals, non-metallic minerals, basic materials | PRODCOM 8-digit (1,834 linked) to CPA 6-digit (452) | CPA 6-digit, or grouped PRODCOM where environmentally distinct (for example ammonia, chlorine, ethylene, clinker) | need a PRODCOM / CPA to CPC 2.1 bridge |
| Other manufacturing and services | union of StatCan 473, Japan 445, BEA 406, Korea 380 through their existing ISIC 4 / CPC 2.1 chains | roughly ISIC Rev 5 class level, merged where no data source separates classes | services detail is limited by SUT data, not by standards |

## 5. Workplan

**Phase 0: reference data (small, can start now).**
- Store ISIC 5 structure, notes and errata; CPC 3.0 structure and notes; the
  Rev4-Rev5 table; NACE 2.1, CPA 2.2 and the NACE 2 to 2.1 / CPA 2.1 to 2.2
  tables from ShowVoc; CPC 2.1 to HS 2022.
- Load them as tidy `STRUCTURE_*` files with a reader in `exiobase_meta`.
- Confirm the NACE 2.1 national accounts timing.

**Phase 1: source inventories.**
- Extract one tidy code list per source: FAO SUA / QCL / trade / forestry /
  FishStat items; IEA WBIG products and flows (rescan, and fix the broken
  WBIG2 download); PV commodity / sub_type; PRODCOM 8-digit; StatCan, Japan,
  BEA and Korea product and industry lists.
- Record, for each code, its CPC 2.1 / ISIC 4 link where official links
  exist, and its country and year coverage.

**Phase 2: backbone.**
- Industry tree: ISIC 5 classes with ISIC 4 and NACE 2.1 equivalents.
- Product tree: the CPC 2.1 subclasses grouped into candidate leaves, with
  CPC 3.0, CPA and HS columns.
- Load the existing ENCORE ISIC 5 to EXIOBASE table as a cross-check only.

**Phase 3: detail layers.**
- Add the domain splits from section 4.
- For each candidate leaf, compute coverage: which sources, how many
  countries (against rx1 / rx2), which years, and the data tier.

**Phase 4: selection.** Merge candidate leaves that have no separating data
(tier D with no environmental reason to keep them). Produce v0.1 counts and
review.

**Phase 5: structure and compatibility.**
- The product-industry (supply) structure matrix, the successor of
  `EXIOBASE20p_EXIOBASE20i_codes.txt`.
- New to EXIOBASE 3 maps for products and industries.
- Partition and nesting tests.

**Phase 6: concordances (in `00-concordances-public`).**
- Map every source code system to the new leaves: FAO, IEA products / flows,
  PV, PRODCOM, HS, and the national SUTs.

## 6. Decisions

### 6.1 Decided (Richard, 2026-11-10)

1. **Size is set by data coverage.** There is no ceiling. A leaf exists if a
   data source separates it (phase 4 selection rule).
2. **One principal product per industry is the default, but multi-product
   industries are allowed** where the technology is genuinely joint, as in
   SUTs. Refineries are the obvious case. The structure matrix (phase 5) is
   therefore a supply-pattern matrix, not a 1:1 diagonal.
3. **Go to NACE Rev 2.1 detail, while still nesting into EXIOBASE 3.** See
   section 6.3 for how.

4. **Technology splits are separate industries that make the same product**
   (SUT style), for example BOF and EAF steel both supplying basic steel.
   Products are split only where EXIOBASE 3 already splits them (electricity
   by technology) or where the products are physically different (ore,
   concentrate, refined metal).
5. **Code labels.** Industries are labelled by their NACE Rev 2.1 code and
   products by their CPA 2.2 code, each plus a suffix for our own
   sub-splits. ISIC Rev 5, ISIC Rev 4 and CPC 2.1 / 3.0 are carried as
   columns.

### 6.2 Still open

6. **CPC pivot timing.** The recommendation is to pivot on CPC 2.1 now and
   switch to 3.0 once UNSD publishes its correspondence tables.

### 6.3 Nesting into EXIOBASE 3 while using NACE Rev 2.1 detail

EXIOBASE 3 is coded on NACE Rev 1.1 / CPA 2002 (for example `p40.11.a
Electricity by coal`, where 40.11 is the NACE 1.1 class), with its own
splits. NACE Rev 2.1 classes do not nest inside NACE 1.1 classes, nor the
other way round.

The solution is to make the leaves the **common refinement** of the two
trees. A leaf is the finest unit such that it belongs to exactly one
EXIOBASE 3 code **and** exactly one NACE 2.1 / ISIC 5 class. Then both trees
are exact aggregations of the leaves:

- Where a new class straddles two EXIOBASE 3 codes, it becomes two leaves.
- Where an EXIOBASE 3 code straddles two new classes, it also becomes two
  leaves.

Leaves are defined on the product side, at CPC subclass level, or at HS 6
digit where a subclass itself straddles. The cut is therefore always
expressed in standard codes. Industries are then defined by their principal
product(s).

Worked example, electricity:
- ISIC Rev 4 3510 breaks down into Rev 5 3511 (non-renewable generation),
  3512 (renewable generation), 3513 (transmission and distribution) and
  3540 (brokers for electricity and gas). 3540 also takes a split-off from
  3520 (gas).
- EXIOBASE 3 `p40.11.a-l` (by technology), `p40.12` (transmission) and
  `p40.13` (distribution and trade) then refine cleanly. Coal, gas, oil and
  nuclear fall under 3511. Hydro, wind, solar, tide and geothermal fall
  under 3512.
- `p40.11.g Electricity by biomass and waste` straddles 3511 and 3512, so it
  becomes two leaves: biomass and renewable waste (3512), and non-renewable
  waste (3511).
- Brokerage (3540) becomes a leaf under `p40.13` (and under the gas trade
  code for the gas part).

This makes the *classification* nest perfectly. The remaining imperfection
is in the *data*. Sources published in NACE 2 / ISIC 4 or NACE 1.1 cannot
always be split into the new leaves directly, so the source to leaf
concordances (phase 6) carry allocation shares where needed. That mirrors
how the official ISIC 4 to 5 table flags splits and transfers (116 Rev 4
classes split).

### 6.4 Classification timeline (checked 2026-11-10)

| Standard | Status |
|---|---|
| ISIC Rev 5 | Adopted. The final UN publication is in copyediting. |
| CPC Ver. 3.0 | UNSC approved it in March 2025. Correspondences to CPC 2.1, HS and ISIC 5 are still in progress. |
| NACE Rev 2.1 | Applies from 1 Jan 2025, with derogations. A UNSD/Eurostat slide lists national accounts for 2029. A 2025 UNSD deck says full EU rollout in 2030. Exact Article 2 wording not yet confirmed on EUR-Lex. |
| CPA 2.2 | Applies to European statistics from 2025. |
| HS 2028 | Enters into force 1 Jan 2028 (delayed from 2027). 5,852 subheadings, 299 sets of amendments. |

Implication: EU SUTs in NACE 2.1 should start to appear around the 2029
benchmark revision. Until then almost all monetary data is NACE 2 / ISIC 4,
so the ISIC 4 to 5 bridge and allocation shares are needed for years.

## 7. Sources consulted

- UNSD economic classifications page (ISIC Rev 5, CPC 3.0 downloads):
  https://unstats.un.org/unsd/classifications/Econ
- CPC Ver. 3.0: https://unstats.un.org/unsd/classifications/cpc/version3
- Eurostat NACE transition: https://ec.europa.eu/eurostat/web/nace/transition
- Eurostat news, CPA 2.2 official:
  https://ec.europa.eu/eurostat/web/products-eurostat-news/w/wdn-20241220-1
- Local surveys of 01-fao_balance, 01-production_volumes, 01-SUT_raw_data,
  00-concordances(-public), energy-extensions and D:\data\00-sources
  (2026-11-10).
