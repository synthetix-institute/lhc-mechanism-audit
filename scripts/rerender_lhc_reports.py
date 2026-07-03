#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lhc_audit.render import render_audit_report, render_shallow_failure


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rerender(out_dir: Path) -> dict:
    sources = read_json(out_dir / "sources.json")
    provenance = read_json(out_dir / "provenance_graph.json")
    operational = read_json(out_dir / "operational_graph.json")
    (out_dir / "audit_report.md").write_text(
        render_audit_report(sources, provenance, operational),
        encoding="utf-8",
    )
    (out_dir / "shallow_failure.md").write_text(
        render_shallow_failure(provenance, operational),
        encoding="utf-8",
    )
    return {
        "report_type": "lhc_report_rerender",
        "readiness": "usable",
        "out_dir": str(out_dir),
        "markdown": {
            "audit_report": str(out_dir / "audit_report.md"),
            "shallow_failure": str(out_dir / "shallow_failure.md"),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(rerender(Path(args.out_dir)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
