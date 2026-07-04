#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lhc_audit.constructor_layer_export import build_constructor_layer_export


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build source-local constructor-layer export for the LHC mechanism audit.")
    parser.add_argument("--run-dir", default=str(ROOT / "runs" / "lhc_black_hole_audit_500k_strict"))
    parser.add_argument("--source-dir", default=str(ROOT / "data" / "hf_lhc_selection_500k" / "sources"))
    parser.add_argument("--out-dir", default=str(ROOT / "outputs" / "lhc_constructor_layer_export"))
    parser.add_argument("--context-window", type=int, default=1400)
    parser.add_argument("--max-context-chars", type=int, default=900)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = build_constructor_layer_export(
        run_dir=Path(args.run_dir),
        source_dir=Path(args.source_dir),
        out_dir=Path(args.out_dir),
        context_window=args.context_window,
        max_context_chars=args.max_context_chars,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

