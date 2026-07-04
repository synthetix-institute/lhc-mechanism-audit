#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lhc_audit.physical_constructor import write_constructor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assemble the LHC physical danger branch from static KnowledgeParser constructor receipts."
    )
    parser.add_argument("--out-dir", required=True, help="Run directory containing equation_mechanism_graph.json.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(write_constructor(Path(args.out_dir)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
