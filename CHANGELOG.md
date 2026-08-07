# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **`exiobase_meta.country_names`: the canonical EXIOBASE country-naming
  convention** (`EXIOBASE_OVERRIDES`, `COCO_NAME_PRE_CONVERT`, plus
  `to_exiobase_name` / `to_exiobase_names` helpers), exported from the
  package root. This repo is the classification authority, but the naming
  convention had been living in `02-macro_db` and was copy-pasted into two
  other repos. The copies drifted: this repo's `refresh_country_axes.py` and
  `03-trade` both carried only 2 of the 6 overrides, so `03-trade` emitted
  `Laos` / `Congo Republic` / `Côte d'Ivoire` / `Cabo Verde` where macro_db
  published `Lao PDR` / `Congo` / `Ivory Coast` / `Cape Verde`, and those
  four countries silently failed to join. All three repos now import the one
  dict; none redeclare it.

- **The rx1/rx2 country-axis derivation moved here from `02-macro_db`**
  (2026-08-06). Deriving a country classification is this repo's job, and
  the previous arrangement also risked inverting the dependency, since
  macro_db depends on `exiobase_meta` and not the reverse. New scripts:
  `build_country_coverage_matrix.py` (comparator matrix),
  `extended_exiobase_country_list.py` (candidates + TIER_A/B/C),
  `make_extended_exiobase_list.py` (rx1 / rx2 selection). Together with the
  existing `refresh_country_axes.py` publish step, the chain now lives here
  end to end apart from one measurement step.

  `02-macro_db/scripts/count_data_coverage.py` stays in macro_db: measuring
  UN SNA / Rev 3 / Rev 4 / IMF WEO year coverage needs its parsers. It is a
  declared handoff, read via `paths.macro_db_coverage_csv`.

  The derivation tables (`country_coverage_matrix`,
  `extended_exiobase_candidates`, `exiobase_rx1`, `exiobase_rx2`) live
  in-repo at `class/country_axes/`, git-versioned beside the classifications
  they feed, and the published artefact is `class/exio_country_axes.xlsx`.
  They spent part of 2026-08-06 in the shared data tree under a
  `paths.axis_work_dir` key and were brought back the same day: they are
  metadata, not data, and being a derivation output does not change that
  (see 00-workflow/data_layout.yaml "METADATA IS NOT DATA"). The scripts
  resolve the location relative to the repo root; `paths.axis_work_dir` is
  gone from config.yaml and honoured only as an out-of-tree override.
  Verified behaviour-preserving: all four intermediate CSVs are
  byte-identical to macro_db's last build and the published xlsx reproduces
  exactly.

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
- Moved `exio_mr_meta.xlsx` (1.1 MB multi-region SUT metadata) to `class/`.
  This is the meta file downstream IOT builders consume (e.g.
  `water_extensions`'s `lib/iot_format.py` reads its `pro` / `ind` / `FD`
  sheets); **downstream `exio_meta_file` paths must point at
  `00-class/class/exio_mr_meta.xlsx`**. It denormalises the product / industry /
  final-demand axes across the 49 regions, so it repeats names / codes owned
  canonically by `exio3class.xlsx` and the `exiobase3` country order. That
  duplication is now guarded by `tests/test_meta_consistency.py`, which fails
  if the copy drifts from the canonical sources. `refresh_country_axes.py` no
  longer reads `exio_mr_meta.xlsx` (it takes the country order from the
  `desire_order` column of the `exiobase3` sheet instead).
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
