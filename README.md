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

## Convert Countries

```bash
exiobase-meta convert-country --value "DE" --to ISO3
```

```bash
exiobase-meta convert-country --value "United States" --to EXIO3
```

## Python API

```python
from exiobase_meta import read_exio3_classification, convert_country

classification = read_exio3_classification(with_ranges=True)
products = classification.get_table("products")
print(classification.table_names)
iso3 = convert_country("Germany", to="ISO3")
```

## Spyder Note

If Spyder cannot import `exiobase_meta`, add this once at the top of your session:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))
```
