# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `read_pi_concordance()`: reader for the binary product-to-industry matrix
  (200 x 163), the authoritative EXIOBASE product-industry structure.
  `exiobase_meta` is the canonical source; `io_utils` reads it through this
  function and `00-concordances-public` derives its published
  `exiobase3p__exiobase3i` concordance from it.

### Changed

- Classifications now live at the **top level** of the repo instead of being
  buried under `src/exiobase_meta/data/`, so they are easy for a human to find.
  The readers resolve them via `DATA_ROOT` (now the repo root); their public
  APIs are unchanged, so consumers (`io_utils`, `00-concordances-public`) are
  unaffected. This assumes the editable (`pip install -e .`) monorepo layout;
  building a standalone wheel would need a step to vendor these files back into
  the package.
  - `class/` - `exio3class.xlsx`, `exio_country_axes.xlsx`, `region12.csv`,
    and `EXIOBASE20p_EXIOBASE20i_codes.txt` (the product-industry structure
    matrix)
- Removed the bundled `exio_mr_meta.xlsx` (1.1 MB multi-region SUT metadata).
  It duplicated information already held elsewhere: its single-region product /
  industry axes are identical to `exio3class.xlsx`, and the only thing
  `refresh_country_axes.py` actually used from it was the legacy EXIOBASE3
  country order, which already lives in the `desire_order` column of the
  `exiobase3` sheet of `exio_country_axes.xlsx`. The refresh script now
  preserves the order from that sheet (re-deriving only the volatile columns),
  so the ordering has exactly one home. The rebuilt `exiobase3` axis is
  identical to the previous one.
- Dropped the `continent` column from `exio_country_axes.xlsx` (all sheets) and
  from `refresh_country_axes.py`. It was derived metadata, not part of the
  classification, read by no consumer, and silently wrong: `country_converter`
  stores its `ISO2` column as regexes (e.g. `^GR$|^EL$`), so the old
  `dict(zip(ISO2, continent))` lookup returned `NaN` for every country with an
  alternate code, leaving Greece and the UK with no continent. Derive continent
  on demand from `code` via `country_converter` if needed. `iso3` and
  `region12` stay (consumed by `build_mr`).
- Made `exio_country_axes.xlsx` the **canonical** home of the rx1 / rx2 country
  classifications. `02-macro_db` computes the selection (the published axis is
  built from its analysis by `refresh_country_axes.py`), but its runtime
  (`config.py`, `pipeline_gross_output.py`) now reads the rx2 axis back from
  here via `exiobase_meta.read_country_axis("rx2")` instead of its own
  `data/fin/comparisons/exiobase_rx2.csv`, so there is one source of truth.
  `exiobase_meta` was added as a dependency of `02-macro_db`; its 100 tests pass
  unchanged. Also fixed `refresh_country_axes.py`'s default macro_db path
  (`../macro_db` -> `../02-macro_db`).
- Defined the repo boundary: this repo owns **classifications**;
  **concordances** live in `00-concordances-public`. Accordingly the
  product-industry matrix moved from a `concordances/` folder into `class/` as
  classification metadata, and there is no longer a `concordances/` folder here.
  The stray duplicate copy that previously sat alongside the package data was
  removed.
- `scripts/refresh_country_axes.py` no longer hard-codes the absolute path to
  the legacy `EXIO3r12r.csv` sanity-check matrix. The default now comes from
  `paths.legacy_r12_csv` in a new repo-root `config.yaml` (override per machine
  with `config.local.yaml`). The `--check-legacy` CLI flag still overrides it.
