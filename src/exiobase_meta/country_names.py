"""Canonical EXIOBASE country naming.

This module is the single source of truth for how a country is *named* in
EXIOBASE. The convention is:

    country_converter ``name_short``  ->  apply ``EXIOBASE_OVERRIDES``

Every repo that writes a country label onto a dataset, or joins two datasets
on a country label, must go through this module. Do not re-declare either
dict locally: three separate copies existed before 2026-08-06 and had drifted
(``00-class`` and ``03-trade`` carried only 2 of the 6 overrides), so
``03-trade`` emitted ``Laos`` / ``Congo Republic`` / ``Cote d'Ivoire`` /
``Cabo Verde`` where ``02-macro_db`` published ``Lao PDR`` / ``Congo`` /
``Ivory Coast`` / ``Cape Verde`` and those four countries silently failed to
join.

``COCO_NAME_PRE_CONVERT`` handles the other direction: raw source spellings
that ``country_converter`` itself does not recognise, applied *before* the
conversion.
"""

from __future__ import annotations

from collections.abc import Iterable

# ---------------------------------------------------------------------------
# Raw source spellings country_converter does not recognise. Applied BEFORE
# the cc conversion, not after.
# ---------------------------------------------------------------------------
COCO_NAME_PRE_CONVERT: dict[str, str] = {
    "D.R. of the Congo": "DR Congo",
    "D.R. Congo": "DR Congo",
    "Dem. Rep. Congo": "DR Congo",
}

# ---------------------------------------------------------------------------
# EXIOBASE-specific overrides applied AFTER cc conversion, keyed by cc's
# ``name_short``. Update this dict when the EXIOBASE classification uses a
# different name convention from cc.
# ---------------------------------------------------------------------------
EXIOBASE_OVERRIDES: dict[str, str] = {
    "Türkiye": "Turkey",          # EXIOBASE pre-dates the 2022 UN rename
    "Laos": "Lao PDR",            # EXIOBASE uses 'Lao PDR'
    "Congo Republic": "Congo",    # EXIOBASE uses 'Congo'
    "Côte d'Ivoire": "Ivory Coast",
    "Cabo Verde": "Cape Verde",   # EXIOBASE uses older English name
    "Eswatini": "Swaziland",      # EXIOBASE pre-dates the 2018 rename
}


def to_exiobase_name(name_short: str) -> str:
    """Apply the EXIOBASE override to one ``country_converter`` name_short."""
    return EXIOBASE_OVERRIDES.get(name_short, name_short)


def to_exiobase_names(names: Iterable[str]) -> list[str]:
    """Apply the EXIOBASE overrides to a sequence of cc ``name_short`` values."""
    return [EXIOBASE_OVERRIDES.get(n, n) for n in names]
