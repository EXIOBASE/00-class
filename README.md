# exiobase-meta

Excel-first EXIOBASE metadata readers with country conversion via `country_converter`.

## Design

- Only Excel source files are bundled under `src/exiobase_meta/data/` (`.xlsx` and `.xls`).
- Country conversion uses `country_converter` (CoCo)

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

Three EXIOBASE country axes are bundled under
`data/class/exio_country_axes.xlsx`:

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

The `region12` column is derived directly from `country_converter`'s
`REMIND` column with two relabels:
- `CAZ -> CAU` (preserve EXIOBASE label)
- `REF -> RUS` (preserve EXIOBASE label; this expands the legacy
  Russia-only RUS region to all REF countries when rx1 / rx2 adds them)

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
