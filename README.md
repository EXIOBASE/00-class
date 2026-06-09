# exiobase-meta

EXIOBASE metadata readers with country conversion via `country_converter`.

## Design

- This repo is the central, human-discoverable home of the EXIOBASE
  **classifications**. The source files live at the **top level**, not buried
  in the Python package:
  - `class/` - classifications and structural metadata
    - `exio3class.xlsx` - product / industry / extension classifications
    - `exio_country_axes.xlsx` - country axes (`exiobase3` / `rx1` / `rx2`);
      the `exiobase3` sheet's `desire_order` column is the single source of
      truth for the legacy EXIOBASE3 country order. This file is also the
      **canonical** home of the `rx1` / `rx2` classifications: their selection
      is computed by `02-macro_db`'s analysis and published here by
      `refresh_country_axes.py`; consumers (including macro_db's own runtime)
      read them back from here via `read_country_axis`
    - `region12.csv` - the 12-region grouping (single source of truth)
    - `EXIOBASE20p_EXIOBASE20i_codes.txt` - authoritative product-industry
      structure (the binary 200 x 163 matrix; which industry produces each
      product)
- Each file is the single source of truth for the order it defines (country
  order, sector order, region grouping). Names and other derived columns are
  computed at refresh time (via `country_converter`) rather than stored, so the
  same fact is never held in two places.
- The `exiobase_meta` reader functions resolve these via `DATA_ROOT` (the repo
  root), so consuming repos read them through the package API rather than from
  hardcoded paths.
- Country conversion uses `country_converter` (CoCo)

### Scope: classifications, not concordances

This repo owns the **classifications** (the vocabularies: product/industry/
country/region lists) and the authoritative product-industry structure.
**Concordances** (mappings between classifications: NACE/HS/COICOP/FAO ->
EXIOBASE, aggregations, NSI bridges, and the published `exiobase3p__exiobase3i`
table) live in the sibling `00-concordances-public` repo. That repo *derives*
its product-industry concordance from `exiobase_meta.read_pi_concordance()`, so
the matrix here is the single upstream source and there is deliberately no
`concordances/` folder in this repo.

## Install

```bash
pip install -e .
```

## Read Classifications

```bash
exiobase-meta read-classification
```

```bash
exiobase-meta read-classification --with-ranges
```

## Read Country Axes

Three EXIOBASE country axes live in
`class/exio_country_axes.xlsx`:

- **`exiobase3`** (49): 44 EXIOBASE3 countries + 5 RoW buckets
  (WA/WL/WE/WF/WM). The legacy EXIOBASE3 country axis.
- **`rx1`** (152): 147 individual countries + 5 RoW buckets.
  Strict TIER_A intersection of macro_db (UN MAA >=15y) + IEA WBAL +
  FAO Production Crops/Livestock.
- **`rx2`** (159): `rx1` plus 7 selected near-miss countries
  (DR Congo, Sudan, Sao Tome, Greenland, South Sudan, Kosovo, Curacao).

```bash
exiobase-meta read-country-axis --name rx2
exiobase-meta read-country-axis --name rx1 --format csv
```

Each axis carries a `region12` column mapping every country / RoW
bucket to one of the 12 EXIOBASE aggregate regions (`build_mr`
consumes this for the MRSUT -> MRSUT-agg aggregation):

```
CAU  Canada + Australia + New Zealand   (coco REMIND "CAZ")
CHA  China + Taiwan + Hong Kong + Macau
EUR  EU27 + UK
IND  India
JPN  Japan
LAM  Latin America + Caribbean
MEA  Middle East + North Africa
NEU  Non-EU Europe (Norway, Switzerland, Turkey, Balkans, ...)
OAS  Other Asia + Pacific
RUS  Russia + CIS / ex-Soviet states    (coco REMIND "REF")
SSA  Sub-Saharan Africa
USA  USA
```

The 12-region grouping is not hard-coded anywhere. It lives in one
CSV, `class/region12.csv` (columns `region12`, `name`,
`remind_source`), which is the single source of truth read by both the
library and `scripts/refresh_country_axes.py`. The actual country to
region links are made by `country_converter`: the `region12` column is
derived directly from cc's `REMIND` column, joined on `remind_source`,
with two relabels encoded in the CSV:
- `CAZ -> CAU` (preserve EXIOBASE label)
- `REF -> RUS` (preserve EXIOBASE label; this expands the legacy
  Russia-only RUS region to all REF countries when rx1 / rx2 adds them)

```python
from exiobase_meta import read_region12, region12_codes, remind_to_r12
read_region12()        # the 12-region classification table
region12_codes()       # ('CAU', 'CHA', ..., 'USA') derived from the CSV
remind_to_r12()        # {'CAZ': 'CAU', 'REF': 'RUS', 'EUR': 'EUR', ...}
```

Manual overrides are kept to a minimum (only Kosovo, which cc does
not yet ship). The legacy MATLAB CSV
`D:\indecol\Projects\MRIOs\Concordances\EXIO3r12r.csv` is retired as a
source of truth - it is checked at refresh time only and matches
the regenerated EXIOBASE3 axis with 0 mismatches.

The wide 49x12 binary matrix (legacy MATLAB format) is regenerated
from the EXIOBASE3 axis and stored as sheet `r12`:

```python
from exiobase_meta import read_r12_matrix, read_country_axis
mat = read_r12_matrix()         # 49 x 12 binary matrix (legacy format)
rx2 = read_country_axis("rx2")
rx2.region12()                  # Series: axis code -> r12 region code
rx2.region12_groups()           # {region: [axis codes]}
```

The axes workbook is regenerated from the upstream `macro_db` comparison
CSVs plus the legacy r12 CSV by:

```bash
python scripts/refresh_country_axes.py            # defaults to ../macro_db
python scripts/refresh_country_axes.py --macro-db /path/to/macro_db
```

## Convert Countries

```bash
exiobase-meta convert-country --value "DE" --to ISO3
```

```bash
exiobase-meta convert-country --value "United States" --to EXIO3
```

## Python API

```python
from exiobase_meta import (
    read_exio3_classification,
    read_country_axis,
    read_all_country_axes,
    read_r12_matrix,
    convert_country,
)

classification = read_exio3_classification(with_ranges=True)
products = classification.get_table("products")
print(classification.table_names)

# Country axes
rx2 = read_country_axis("rx2")
print(rx2.n, rx2.names[:5])
print(rx2.row_members("WA"))   # ISO3 list pooled into RoW Asia and Pacific
print(rx2.region12_groups()["EUR"])   # ISO3 codes in the EUR r12 region
axes = read_all_country_axes()   # dict keyed by name

# 12-region aggregation (build_mr consumes this)
r12_mat = read_r12_matrix()    # legacy 49x12 binary matrix

iso3 = convert_country("Germany", to="ISO3")
```

## Spyder Note

If Spyder cannot import `exiobase_meta`, add this once at the top of your session:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))
```
