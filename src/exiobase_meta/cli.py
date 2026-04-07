"""Command-line interface for exiobase-meta.

Provides commands to read exio3 classification data from Excel and to
convert country names/codes via country_converter.
"""

from __future__ import annotations

import argparse
import json

from .classifications import read_exio3_classification
from .country_conversion import convert_country


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="exiobase-meta")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cls = sub.add_parser("read-classification", help="Read exio3 classification sheets from Excel")
    p_cls.add_argument("--with-ranges", action="store_true", help="Also read supply/use range blocks")

    p_country = sub.add_parser("convert-country", help="Convert country name/code using country_converter")
    p_country.add_argument("--value", required=True, help="Input country name or code")
    p_country.add_argument("--to", default="ISO3", help="Target classification (e.g., ISO2, ISO3, EXIO3)")
    p_country.add_argument("--not-found", default="not found", help="Fallback value when conversion fails")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.cmd == "read-classification":
        bundle = read_exio3_classification(with_ranges=args.with_ranges)
        payload = {
            "tables": {name: int(df.shape[0]) for name, df in bundle.tables.items()},
            "ranges": None if bundle.ranges is None else {name: len(values) for name, values in bundle.ranges.items()},
        }
        print(json.dumps(payload, indent=2))
    elif args.cmd == "convert-country":
        converted = convert_country(args.value, to=args.to, not_found=args.not_found)
        print(converted)


if __name__ == "__main__":
    main()
