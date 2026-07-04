#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lhc_audit.discourse_mechanism_attention import write_discourse_mechanism_attention


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build discourse-vs-mechanism sparse attention proof.")
    parser.add_argument("--run-dir", required=True, help="Run directory containing static LHC audit artifacts.")
    return parser


def main() -> None:
    result = write_discourse_mechanism_attention(Path(build_parser().parse_args().run_dir))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
