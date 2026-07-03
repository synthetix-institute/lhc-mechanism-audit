#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


CHAIN_REQUIRED_ROLES = {
    "stable_black_hole_risk_exclusion_branch": [
        "stable_branch",
        "capture_stopping",
        "accretion_growth",
        "astrophysical_bound",
    ],
    "evaporation_safety_branch": [
        "evaporation_branch",
        "exclusion_conclusion",
    ],
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(text: str, limit: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def witness_score_for_role(witness: Dict[str, Any], role: str) -> float:
    if witness.get("dominant_role") == role:
        return max(1.0, float((witness.get("role_scores") or {}).get(role, 0.0)))
    return float((witness.get("role_scores") or {}).get(role, 0.0))


def best_witnesses(
    witnesses: Iterable[Dict[str, Any]],
    source_id: str,
    role: str,
    limit: int,
) -> List[Dict[str, Any]]:
    candidates = [
        witness
        for witness in witnesses
        if witness.get("source_id") == source_id and witness_score_for_role(witness, role) > 0
    ]
    candidates.sort(key=lambda w: witness_score_for_role(w, role), reverse=True)
    return candidates[:limit]


def render(out_dir: Path, witness_limit: int, context_chars: int, formula_chars: int) -> Dict[str, Any]:
    operational = read_json(out_dir / "operational_graph.json")
    witnesses = read_json(out_dir / "equation_witnesses.json").get("witnesses", [])
    chains = operational.get("chain_candidates", [])

    report: Dict[str, Any] = {
        "report_type": "lhc_chain_evidence",
        "readiness": "usable" if chains else "no_chain_candidates",
        "out_dir": str(out_dir),
        "chain_count": len(chains),
        "chains": [],
    }
    lines: List[str] = [
        "# LHC Mechanism Chain Evidence",
        "",
        "This file attaches source-local equation witnesses to each extracted mechanism-chain candidate.",
        "The purpose is inspection: a chain is useful only if its roles are supported by formulas and local text, not only by provenance.",
        "",
    ]

    for chain in chains:
        source_id = str(chain.get("source_id"))
        chain_type = str(chain.get("chain_type"))
        required_roles = CHAIN_REQUIRED_ROLES.get(chain_type, [])
        chain_obj = {
            "source_id": source_id,
            "chain_type": chain_type,
            "required_roles": required_roles,
            "roles": {},
        }
        lines.append(f"## {source_id} — `{chain_type}`")
        lines.append("")
        for step in chain.get("logic", []):
            lines.append(f"- {step}")
        lines.append("")

        for role in required_roles:
            role_witnesses = best_witnesses(witnesses, source_id, role, witness_limit)
            chain_obj["roles"][role] = []
            lines.append(f"### `{role}`")
            lines.append("")
            if not role_witnesses:
                lines.append("No source-local witness selected for this role.")
                lines.append("")
                continue
            for index, witness in enumerate(role_witnesses, start=1):
                item = {
                    "score": witness_score_for_role(witness, role),
                    "dominant_role": witness.get("dominant_role"),
                    "formula": witness.get("formula"),
                    "context": witness.get("context"),
                }
                chain_obj["roles"][role].append(item)
                lines.append(f"Evidence {index}. score `{item['score']:.3f}`, dominant role `{item['dominant_role']}`")
                lines.append("")
                lines.append("Formula:")
                lines.append("")
                lines.append("```text")
                lines.append(compact(str(item["formula"]), formula_chars))
                lines.append("```")
                lines.append("")
                lines.append("Local context:")
                lines.append("")
                lines.append("```text")
                lines.append(compact(str(item["context"]), context_chars))
                lines.append("```")
                lines.append("")
        report["chains"].append(chain_obj)

    json_path = out_dir / "chain_evidence.json"
    md_path = out_dir / "chain_evidence.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "readiness": report["readiness"],
        "chain_count": len(chains),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--witness-limit", type=int, default=2)
    parser.add_argument("--context-chars", type=int, default=900)
    parser.add_argument("--formula-chars", type=int, default=360)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(
        render(
            Path(args.out_dir),
            witness_limit=args.witness_limit,
            context_chars=args.context_chars,
            formula_chars=args.formula_chars,
        ),
        indent=2,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
