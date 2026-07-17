#!/usr/bin/env python3
"""Merge the core guide and supporting article without rasterizing either PDF."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from pypdf import PdfWriter


def merge(core: Path, article: Path, output: Path) -> None:
    for path in (core, article):
        if not path.is_file():
            raise FileNotFoundError(path)

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")

    writer = PdfWriter()
    writer.append(str(core), import_outline=True)
    writer.append(str(article), import_outline=True)
    writer.add_metadata(
        {
            "/Title": "Two Maps of Scientific Reasoning: LHC Black-Hole Case",
            "/Author": "Synthetix Institute",
            "/Subject": "Epistack core submission and complete scientific artifact",
        }
    )
    with temporary.open("wb") as handle:
        writer.write(handle)
    writer.close()
    os.replace(temporary, output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("core", type=Path)
    parser.add_argument("article", type=Path)
    parser.add_argument("output", type=Path)
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    merge(args.core, args.article, args.output)
