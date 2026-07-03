#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


KEYWORDS = [
    "LHC",
    "Large Hadron Collider",
    "black hole",
    "micro black hole",
    "microscopic black hole",
    "TeV-scale black hole",
    "Hawking radiation",
    "cosmic ray",
    "white dwarf",
    "neutron star",
    "accretion",
    "metastable",
    "collider risk",
    "disaster scenario",
]

SEED_IDS = {"0806.3381", "0806.3414", "0808.1415", "0807.3349", "0808.4087", "0901.2948"}


def score_text(text: str) -> int:
    return sum(1 for kw in KEYWORDS if re.search(re.escape(kw), text, flags=re.I))


def row_id(row: Dict[str, Any]) -> str:
    for key in ("arxiv_id", "id", "paper_id", "external_id"):
        value = row.get(key)
        if value:
            return str(value).replace("arXiv:", "")
    blob = " ".join(str(row.get(k, "")) for k in ("title", "latex", "text", "abstract"))
    match = re.search(r"(\d{4}\.\d{4,5})", blob)
    return match.group(1) if match else ""


def row_text(row: Dict[str, Any]) -> str:
    parts = []
    for key in ("title", "abstract", "latex", "text", "content"):
        value = row.get(key)
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)


def iter_hf_rows(dataset: str, split: str) -> Iterable[Dict[str, Any]]:
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:
        raise RuntimeError("Install `datasets` to stream Hugging Face rows.") from exc
    ds = load_dataset(dataset, split=split, streaming=True)
    for row in ds:
        yield dict(row)


def select(args: argparse.Namespace) -> Dict[str, Any]:
    out_dir = Path(args.out_dir)
    source_dir = out_dir / "sources"
    out_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)

    selected: List[Dict[str, Any]] = []
    scanned = 0
    for row in iter_hf_rows(args.dataset, args.split):
        scanned += 1
        rid = row_id(row)
        text = row_text(row)
        score = score_text(text)
        if rid in SEED_IDS or score >= args.min_score:
            selected.append({
                "row_index": scanned - 1,
                "paper_id": rid,
                "score": score,
                "title": str(row.get("title", ""))[:500],
            })
            if text:
                safe_id = rid or f"row_{scanned:09d}"
                (source_dir / f"{safe_id.replace('/', '_')}.tex").write_text(text, encoding="utf-8", errors="replace")
        if args.max_docs and scanned >= args.max_docs:
            break

    manifest = {
        "report_type": "lhc_literature_hf_selection",
        "dataset": args.dataset,
        "split": args.split,
        "scanned": scanned,
        "selected": len(selected),
        "min_score": args.min_score,
        "keywords": KEYWORDS,
        "seed_ids": sorted(SEED_IDS),
        "sources": str(source_dir),
        "records": selected,
    }
    (out_dir / "selection_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="synthetix-institute/latex-data-pub")
    parser.add_argument("--split", default="train")
    parser.add_argument("--out-dir", default="data/hf_lhc_selection")
    parser.add_argument("--max-docs", type=int, default=0, help="0 means scan the stream until exhaustion/interruption.")
    parser.add_argument("--min-score", type=int, default=3)
    return parser


def main() -> None:
    print(json.dumps(select(build_parser().parse_args()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
