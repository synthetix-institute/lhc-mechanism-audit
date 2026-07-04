#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lhc_audit.public_knowledge_graph import write_public_knowledge_graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a public typed knowledge graph from static LHC audit artifacts."
    )
    parser.add_argument("--out-dir", required=True, help="Run directory containing static graph artifacts.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(write_public_knowledge_graph(Path(args.out_dir)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

