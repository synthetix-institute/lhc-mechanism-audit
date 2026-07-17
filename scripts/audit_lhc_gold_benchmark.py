#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lhc_audit.gold_benchmark import write_gold_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate LHC equation extraction against primary-source receipts.")
    parser.add_argument("--sources-dir", default="data/arxiv_lhc_full_sources/sources")
    parser.add_argument("--benchmark", default="data/lhc_gold_benchmark.json")
    parser.add_argument("--out-json", default="outputs/lhc_gold_benchmark.json")
    parser.add_argument("--out-markdown", default="outputs/lhc_gold_benchmark.md")
    parser.add_argument("--allow-incomplete", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = write_gold_benchmark(
        Path(args.sources_dir),
        Path(args.benchmark),
        Path(args.out_json),
        Path(args.out_markdown),
    )
    print(json.dumps({
        "readiness": result["readiness"],
        "source_coverage": result["source_coverage"],
        "receipt_coverage": result["receipt_coverage"],
        "json": args.out_json,
        "markdown": args.out_markdown,
    }, indent=2))
    if result["readiness"] != "usable" and not args.allow_incomplete:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
