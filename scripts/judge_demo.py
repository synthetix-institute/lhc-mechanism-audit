#!/usr/bin/env python3
"""Small, dependency-free tour of the committed LHC mechanism receipts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from build_judges_guide import ROOT, build


BUNDLE = ROOT / "paper" / "lhc_judges_guide_receipts.json"

RECEIPT_MEANINGS = {
    "E00292": ("formation probability above a model threshold", "production"),
    "E00455": ("mass lost per unit time through evaporation", "survival"),
    "E00124": ("coupled momentum loss and mass gain in matter", "stopping and growth"),
    "E00149": ("stopping and mass gain per distance travelled", "stopping and growth"),
    "E00179": ("time required for growth in compact-star regimes", "growth time"),
    "E00202": ("predicted neutron-star growth time", "astronomical test"),
}


def load_bundle() -> Dict[str, Any]:
    build()
    with BUNDLE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def line(title: str, value: Any) -> None:
    print(f"{title}: {value}")


def clean_formula(formula: str) -> str:
    return " ".join(formula.split())


def print_receipt(receipt: Dict[str, Any]) -> None:
    meaning, condition = RECEIPT_MEANINGS[receipt["node_id"]]
    print()
    print(f"Receipt {receipt['node_id']}")
    line("Paper", f"{receipt['source_id']} | {receipt['source_title']}")
    line("Source equation ordinal", receipt["source_equation_ordinal"])
    line("Source offsets", f"{receipt['source_start']}:{receipt['source_end']}")
    line("Formula", clean_formula(receipt["formula"]))
    line("What it calculates", meaning)
    line("Condition tested", condition)
    line("Source", receipt["source_url"])


def receipts_by_id(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {row["node_id"]: row for row in bundle["selected_equation_receipts"]}


def print_counterfactual(bundle: Dict[str, Any]) -> None:
    by_id = receipts_by_id(bundle)
    print("Counterfactual: assume Hawking evaporation is absent")
    print()
    print("1. Changed condition: survival against evaporation")
    print("2. Branch activated: hypothetical stable microscopic object")
    print("3. Calculations still required:")
    print("   - stopping or capture in matter")
    print("   - net mass gain after losses")
    print("   - integration of that rate over time")
    print("   - compatibility with long-lived compact stars")
    print("4. Load-bearing receipts:")
    for node_id, meaning in (
        ("E00149", "momentum loss and mass gain in matter"),
        ("E00179", "growth time under compact-star conditions"),
        ("E00202", "about 20 years for one neutron-star model"),
    ):
        row = by_id[node_id]
        print(f"   - {node_id}: {meaning} ({row['source_id']})")
    print("5. Result: rapid stable-object growth predicts compact-star consequences")
    print("   that conflict with observed stellar survival. Slow growth removes the")
    print("   terrestrial catastrophe. The safety conclusion survives the challenge")
    print("   through a different physical branch.")


def print_overview(bundle: Dict[str, Any]) -> None:
    metrics = bundle["metrics"]
    line("Question", bundle["question"])
    line("Answer", bundle["answer"])
    print()
    print("Two graphs")
    line("  Documentary", bundle["two_graphs"]["provenance"])
    line("  Mechanism", bundle["two_graphs"]["mechanism"])
    print()
    print("Measured case artifacts")
    line("  Papers", metrics["papers_in_reconstruction"])
    line("  Claims", metrics["claims"])
    line("  Equation windows", metrics["equation_windows"])
    line("  Usable equation nodes", metrics["usable_equation_nodes"])
    line("  Source-local equation edges", metrics["source_local_equation_edges"])
    line("  Cross-paper analogues", metrics["cross_paper_analogue_edges"])
    line(
        "  Prespecified equations recovered",
        f"{metrics['benchmark_receipts_recovered']}/{metrics['benchmark_receipts_total']}",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--counterfactual",
        choices=("no-hawking",),
        help="Propagate a named change through the physical dependency chain.",
    )
    parser.add_argument("--receipt", help="Print one selected equation receipt by node ID.")
    parser.add_argument("--list-receipts", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print the full receipt bundle as JSON.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    bundle = load_bundle()
    if args.json:
        print(json.dumps(bundle, indent=2, ensure_ascii=True))
        return

    if args.list_receipts:
        for receipt in bundle["selected_equation_receipts"]:
            meaning, condition = RECEIPT_MEANINGS[receipt["node_id"]]
            print(f"{receipt['node_id']}\t{receipt['source_id']}\t{condition}\t{meaning}")
        return

    if args.receipt:
        receipt = receipts_by_id(bundle).get(args.receipt)
        if receipt is None:
            available = ", ".join(sorted(receipts_by_id(bundle)))
            raise SystemExit(f"Unknown receipt {args.receipt}. Available: {available}")
        print_receipt(receipt)
        return

    print_overview(bundle)
    print()
    print_counterfactual(bundle)


if __name__ == "__main__":
    main()
