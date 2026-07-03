#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lhc_audit.equation_mechanism import build_equation_mechanism_graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, help="Audit output directory containing equation_witnesses.json.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    graph = build_equation_mechanism_graph(Path(args.out_dir))
    print(json.dumps({
        "json": str(Path(args.out_dir) / "equation_mechanism_graph.json"),
        "markdown": str(Path(args.out_dir) / "equation_mechanism_graph.md"),
        "readiness": graph.get("readiness"),
        "fingerprinted_node_count": graph.get("fingerprinted_node_count"),
        "source_local_edges": len(graph.get("edges", [])),
        "cross_source_analogues": len(graph.get("analog_edges", [])),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
