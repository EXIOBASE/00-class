# Data coverage by country (snapshot 2026-11-10)

`coverage_by_country.csv` is the data behind the coverage dashboard
(https://claude.ai/artifact/SfxaGbzmTNcDTfw8UuALyW): one row per rx2 country
with FAO crop and livestock items, production-volume commodity pairs
(2018-2022), IEA, OECD ICIO, FIGARO and Eurostat A*64 membership, and the
most detailed national SUT/IOT held locally.

- `coverage_base.py` computes the FAO, production-volume and MRIO columns
  (`python -I coverage_base.py <out_dir>`, writes `cov_base.csv`).
- `national_tables.py` adds the national-table columns from a hand-curated
  list (`python -I national_tables.py <out_dir>`).
- `sut_assess_A.csv` and `sut_assess_B.csv` hold the product and industry
  counts of the national tables under `D:/indecol/data/suts/raw`, counted from
  the files on 2026-11-10 (method column says counted or stated_in_doc).
  These counts, plus Australia (ABS IOPC 914 x 115) and the edits for
  Estonia and Slovenia, were merged into `coverage_by_country.csv` by hand in
  that session; `national_tables.py` alone reproduces the earlier, unassessed
  version.
