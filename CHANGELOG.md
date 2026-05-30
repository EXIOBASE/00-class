# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- `scripts/refresh_country_axes.py` no longer hard-codes the absolute path to
  the legacy `EXIO3r12r.csv` sanity-check matrix. The default now comes from
  `paths.legacy_r12_csv` in a new repo-root `config.yaml` (override per machine
  with `config.local.yaml`). The `--check-legacy` CLI flag still overrides it.
