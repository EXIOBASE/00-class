from __future__ import annotations

from collections.abc import Sequence

import country_converter as coco


_CC = coco.CountryConverter()


def convert_country(value: str, to: str = "ISO3", not_found: str = "not found") -> str:
    return str(_CC.convert(names=value, to=to, not_found=not_found))


def convert_countries(values: Sequence[str], to: str = "ISO3", not_found: str = "not found") -> list[str]:
    result = _CC.convert(names=list(values), to=to, not_found=not_found)
    if isinstance(result, list):
        return [str(v) for v in result]
    return [str(result)]
