"""Command-line interface for exiobase-meta.

Provides commands to read exio3 classification data from Excel and to
convert country names/codes via country_converter.
"""

from __future__ import annotations

import argparse
import json

from .classifications import read_exio3_classification
from .country_axes import AXIS_NAMES, read_country_axis
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

    p_axis = sub.add_parser("read-country-axis", help="Read an EXIOBASE country axis (exiobase3 / rx1 / rx2)")
    p_axis.add_argument("--name", required=True, choices=AXIS_NAMES, help="Axis identifier")
    p_axis.add_argument("--format", default="summary", choices=("summary", "csv"), help="Output format")

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
    elif args.cmd == "read-country-axis":
        axis = read_country_axis(args.name)
        if args.format == "csv":
            print(axis.table.to_csv(index=False), end="")
        else:
            payload = {
                "name": axis.name,
                "n_entries": axis.n,
                "n_individual": int((axis.table["type"] == "country").sum()),
                "n_row": int((axis.table["type"] == "RoW").sum()),
                "row_buckets": axis.row_buckets["code"].tolist(),
            }
            print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
