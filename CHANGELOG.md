# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `read_pi_concordance()`: reader for the binary product-to-industry
  concordance (200 x 163), now shipped as package data under
  `data/concordances/EXIOBASE20p_EXIOBASE20i_codes.txt`. `exiobase_meta`
  is the canonical owner of this concordance; consuming repos (e.g.
  `io_utils`) read it from here instead of a hardcoded `class/` path.

### Changed

- `scripts/refresh_country_axes.py` no longer hard-codes the absolute path to
  the legacy `EXIO3r12r.csv` sanity-check matrix. The default now comes from
  `paths.legacy_r12_csv` in a new repo-root `config.yaml` (override per machine
  with `config.local.yaml`). The `--check-legacy` CLI flag still overrides it.
